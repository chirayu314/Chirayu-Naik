"""
Approach 3: LLM-Compiled Rules Engine.
Uses an LLM (or pre-compiled, schema-validated artifacts when offline) to compile statutory tax law
into a safe declarative specification, and executes locally with zero LLM query overhead and no eval/exec.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

from project_a.models.user_input import TaxpayerInput
from project_a.compiled_rules.declarative_schema import DeclarativeTaxYearSpecification
from project_a.compiled_rules.declarative_executor import execute_declarative_rules
from project_a.calculators.tax_engine import calculate_income_tax
from project_a.llm.llm_client import LLMClient


COMPILED_DIR = Path(__file__).parent.parent / "compiled_rules"


class CompiledRulesTaxEngine:
    def __init__(self, client: Optional[LLMClient] = None):
        self.client = client or LLMClient()
        self._cache: Dict[str, DeclarativeTaxYearSpecification] = {}

    def get_specification(
        self,
        financial_year: str = "2024-25",
        force_recompile: bool = False
    ) -> DeclarativeTaxYearSpecification:
        """
        Load declarative specification. If force_recompile is requested and credentials exist,
        compiles via LLM. Otherwise loads audited pre-compiled artifact.
        """
        cache_key = f"{financial_year}"
        if not force_recompile and cache_key in self._cache:
            return self._cache[cache_key]

        artifact_file = COMPILED_DIR / f"compiled_rules_{financial_year.replace('-', '_')}.json"

        if force_recompile and self.client.is_configured():
            spec = self._compile_with_llm(financial_year)
            self._cache[cache_key] = spec
            return spec

        # Fallback to audited pre-compiled artifact
        if not artifact_file.exists():
            raise FileNotFoundError(f"No compiled rules artifact found for FY {financial_year} at {artifact_file}")

        with open(artifact_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        spec = DeclarativeTaxYearSpecification.model_validate(data)
        self._cache[cache_key] = spec
        return spec

    def _compile_with_llm(self, financial_year: str) -> DeclarativeTaxYearSpecification:
        """
        Live compilation of statutory rules using LLM.
        """
        schema_example = json.dumps(
            DeclarativeTaxYearSpecification.model_json_schema(),
            indent=2
        )
        system_prompt = (
            "You are a tax code compiler. Translate Indian statutory tax provisions into a strict JSON "
            "declarative specification matching this exact JSON schema:\n"
            f"{schema_example}\n"
            "Include both old_regime and new_regime objects with standard_deduction, slabs, rebate_87a, and surcharge_brackets."
        )
        user_prompt = (
            f"Compile the statutory income tax rules for FY {financial_year} into strict JSON. "
            "Ensure old_regime has standard deduction 50000, new_regime has standard deduction 75000. "
            "Return ONLY valid JSON."
        )

        raw_resp, meta = self.client.call_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"}
        )

        if not raw_resp:
            raise RuntimeError(f"LLM compilation failed: {meta.get('error')}")

        content = raw_resp["choices"][0]["message"]["content"]
        data = json.loads(content)
        data["provenance"] = "LLM_COMPILED_LIVE"
        return DeclarativeTaxYearSpecification.model_validate(data)

    def calculate(self, taxpayer: TaxpayerInput) -> Dict[str, Any]:
        """
        Execute tax calculation against declarative compiled rules without LLM query calls.
        """
        fy = taxpayer.financial_year
        spec = self.get_specification(fy)
        result = execute_declarative_rules(taxpayer, spec)

        # Accuracy comparison with deterministic ground truth
        ground_truth = calculate_income_tax(taxpayer)
        diff = abs(result["final_tax"] - ground_truth["final_tax"])

        return {
            **result,
            "ground_truth_final_tax": ground_truth["final_tax"],
            "difference_rupees": diff,
            "exact_match": (diff == 0),
        }

