"""
Approach 2: LLM at Query Time.
Sends structured taxpayer information and applicable statutory tax rules to an LLM,
requests structured JSON output, validates with Pydantic, and measures latency,
token usage, cost, and accuracy against ground truth.
"""

import json
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ValidationError

from project_a.models.user_input import TaxpayerInput
from project_a.llm.llm_client import LLMClient
from project_a.calculators.tax_engine import calculate_income_tax


class LLMTaxCalculationResponse(BaseModel):
    gross_salary: float
    regime: str
    financial_year: str
    standard_deduction: float
    hra_exemption: float = 0.0
    section_80c: float = 0.0
    section_80ccd_1b: float = 0.0
    section_80d: float = 0.0
    home_loan_deduction: float = 0.0
    total_deductions: float
    taxable_income: float
    tax_before_rebate: float
    rebate_87a: float = 0.0
    tax_after_rebate: float
    surcharge: float = 0.0
    cess: float
    final_tax: int
    rule_references: list[str] = Field(default_factory=list)
    reasoning: str = ""


SYSTEM_PROMPT_TEMPLATE = """You are an Indian Income Tax calculation engine for salaried employees.
Compute the exact tax payable under the Indian Income-tax Act, 1961 for the specified financial year and regime.

APPLICABLE STATUTORY RULES FOR {financial_year} ({regime_upper} REGIME):
{rules_text}

MANDATORY CALCULATION RULES:
1. Standard deduction: Apply Section 16(ia) limit.
2. Deductions under Chapter VI-A (80C, 80CCD, 80D, 24b) apply ONLY in the Old Regime. In New Regime, only standard deduction applies.
3. Taxable income must be rounded to nearest Rs. 10 under Section 288A.
4. Calculate slab tax step by step according to the exact slabs.
5. Apply Section 87A rebate and marginal relief if eligible.
6. Apply surcharge and marginal relief if taxable income exceeds Rs. 50 Lakh.
7. Apply Health & Education Cess at 4% on (tax + surcharge).
8. Round final tax to nearest Rs. 10 under Section 288B.

You must reply with ONLY a single valid JSON object with the following exact keys:
{{
  "gross_salary": float,
  "regime": "{regime}",
  "financial_year": "{financial_year}",
  "standard_deduction": float,
  "hra_exemption": float,
  "section_80c": float,
  "section_80ccd_1b": float,
  "section_80d": float,
  "home_loan_deduction": float,
  "total_deductions": float,
  "taxable_income": float,
  "tax_before_rebate": float,
  "rebate_87a": float,
  "tax_after_rebate": float,
  "surcharge": float,
  "cess": float,
  "final_tax": integer,
  "rule_references": [string],
  "reasoning": string
}}
No explanation or markdown outside the JSON.
"""


def _get_rules_text_for_llm(financial_year: str, regime: str) -> str:
    if financial_year == "2024-25":
        if regime == "new":
            return """- Section 16(ia): Standard deduction Rs. 75,000.
- Slabs: 0-3L: Nil, 3L-7L: 5%, 7L-10L: 10%, 10L-12L: 15%, 12L-15L: 20%, Above 15L: 30%.
- Section 87A: If taxable income <= 7,00,000, rebate up to Rs. 25,000 (tax becomes 0).
  Marginal relief for income exceeding 7,00,000: tax payable cannot exceed income exceeding Rs. 7,00,000.
- Surcharge: >50L: 10%, >1Cr: 15%, >2Cr: 25% (max 25%).
- Cess: 4% on tax+surcharge."""
        else:
            return """- Section 16(ia): Standard deduction Rs. 50,000.
- Slabs: 0-2.5L: Nil, 2.5L-5L: 5%, 5L-10L: 20%, Above 10L: 30%.
- Section 87A: If taxable income <= 5,00,000, rebate up to Rs. 12,500. No marginal relief.
- Section 10(13A) HRA: Least of actual HRA, rent - 10% salary, or 50%(metro)/40%(non-metro) salary.
- 80C cap Rs. 1,50,000; 80CCD(1B) cap Rs. 50,000; 80D: Self 25k/50k, Parents 25k/50k; Sec 24(b) home loan max Rs. 2,00,000.
- Surcharge: >50L: 10%, >1Cr: 15%, >2Cr: 25%, >5Cr: 37%.
- Cess: 4% on tax+surcharge."""
    else:  # 2025-26
        if regime == "new":
            return """- Section 16(ia): Standard deduction Rs. 75,000.
- Slabs: 0-4L: Nil, 4L-8L: 5%, 8L-12L: 10%, 12L-16L: 15%, 16L-20L: 20%, 20L-24L: 25%, Above 24L: 30%.
- Section 87A: If taxable income <= 12,00,000, rebate up to Rs. 60,000 (tax becomes 0).
  Marginal relief: Tax payable cannot exceed income exceeding Rs. 12,00,000.
- Surcharge: >50L: 10%, >1Cr: 15%, >2Cr: 25% (max 25%).
- Cess: 4% on tax+surcharge."""
        else:
            return """- Section 16(ia): Standard deduction Rs. 50,000.
- Slabs: 0-2.5L: Nil, 2.5L-5L: 5%, 5L-10L: 20%, Above 10L: 30%.
- Section 87A: If taxable income <= 5,00,000, rebate up to Rs. 12,500.
- Section 10(13A) HRA, 80C, 80CCD(1B), 80D, 24(b) same as FY 2024-25.
- Surcharge: >50L: 10%, >1Cr: 15%, >2Cr: 25%, >5Cr: 37%.
- Cess: 4% on tax+surcharge."""


class LLMQueryTimeEngine:
    def __init__(self, client: Optional[LLMClient] = None):
        self.client = client or LLMClient()

    def calculate(
        self,
        taxpayer: TaxpayerInput,
        max_retries: int = 1
    ) -> Dict[str, Any]:
        """
        Execute tax calculation using LLM at query time.
        If credentials unavailable, returns status="NOT_RUN".
        Never fakes LLM output or presents fallback silently as LLM calculation.
        """
        if not self.client.is_configured():
            return {
                "approach": "llm_at_query_time",
                "status": "NOT_RUN",
                "error": "LLM credentials not available. Set OPENAI_API_KEY or GEMINI_API_KEY in environment.",
                "taxpayer_gross_salary": taxpayer.gross_salary,
                "regime": taxpayer.regime,
                "financial_year": taxpayer.financial_year,
            }

        fy = taxpayer.financial_year
        regime = taxpayer.regime
        rules_text = _get_rules_text_for_llm(fy, regime)
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            financial_year=fy, regime=regime, regime_upper=regime.upper(), rules_text=rules_text
        )

        taxpayer_payload = taxpayer.model_dump(mode="json")
        user_prompt = f"Calculate income tax for this salaried taxpayer:\n{json.dumps(taxpayer_payload, indent=2)}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Calculate deterministic ground truth for accuracy measurement
        ground_truth = calculate_income_tax(taxpayer)

        attempts = 0
        last_error = None
        while attempts <= max_retries:
            attempts += 1
            raw_resp, meta = self.client.call_chat_completion(
                messages=messages,
                temperature=0.0,
                response_format={"type": "json_object"}
            )

            if meta.get("error"):
                return {
                    "approach": "llm_at_query_time",
                    "status": "ERROR",
                    "error": meta["error"],
                    "metadata": meta,
                }

            try:
                content = raw_resp["choices"][0]["message"]["content"]
                parsed_json = json.loads(content)
                validated = LLMTaxCalculationResponse.model_validate(parsed_json)

                # Check rupee exactness with ground truth
                diff_rupees = abs(validated.final_tax - ground_truth["final_tax"])
                exact_match = (diff_rupees == 0)

                return {
                    "approach": "llm_at_query_time",
                    "status": "SUCCESS",
                    "result": validated.model_dump(),
                    "ground_truth_final_tax": ground_truth["final_tax"],
                    "difference_rupees": diff_rupees,
                    "exact_match": exact_match,
                    "metadata": meta,
                }
            except (json.JSONDecodeError, ValidationError, KeyError) as e:
                last_error = str(e)
                # Retry on malformed json
                messages.append({
                    "role": "user",
                    "content": f"Your previous response caused validation error: {last_error}. Please provide strict JSON matching schema."
                })

        return {
            "approach": "llm_at_query_time",
            "status": "VALIDATION_FAILED",
            "error": f"LLM output failed Pydantic validation after {attempts} attempts: {last_error}",
            "metadata": meta,
        }

