"""
Natural language parser for Indian salaried taxpayer descriptions.
Supports standard English, Hinglish, Indian numeric notation, unit conversion,
and targeted clarification generation for missing/contradictory inputs.
"""

import re
from typing import Dict, Any, List, Optional, Tuple, Literal
from pydantic import BaseModel, Field

from project_a.models.user_input import TaxpayerInput


class ParseResult(BaseModel):
    status: Literal["success", "clarification_needed", "error", "contradiction_detected"]
    taxpayer_input: Optional[TaxpayerInput] = None
    clarification_questions: List[str] = Field(default_factory=list)
    detected_entities: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    raw_query: str


METRO_CITIES = {
    "mumbai", "bombay", "delhi", "new delhi", "kolkata", "calcutta",
    "chennai", "madras", "ncr", "gurugram", "noida"
}


def parse_indian_number(text: str) -> Optional[float]:
    """
    Parse numbers in Indian notation:
    e.g., '12 lakh', '1.5 crore', '25k', '50 hazar', '1,50,000', '15L', '1.5cr'.
    """
    if not text:
        return None

    cleaned = text.strip().lower().replace(",", "")
    cleaned = re.sub(r"^(rs\.?|inr|₹)\s*", "", cleaned).strip()

    # Match crore
    m = re.match(r"^(\d+(?:\.\d+)?)\s*(?:crores?|cr)\b", cleaned)
    if m:
        return float(m.group(1)) * 10_000_000

    # Match lakh / lac / L
    m = re.match(r"^(\d+(?:\.\d+)?)\s*(?:lakhs?|lacs?|lac|lk|l)\b", cleaned)
    if m:
        return float(m.group(1)) * 100_000

    # Match thousand / k / hazar
    m = re.match(r"^(\d+(?:\.\d+)?)\s*(?:k|thousands?|hazar)\b", cleaned)
    if m:
        return float(m.group(1)) * 1_000

    # Pure number
    m = re.match(r"^(\d+(?:\.\d+)?)$", cleaned)
    if m:
        return float(m.group(1))

    return None


NUM_TOKEN_PATTERN = r"(?:(?:rs\.?|inr|₹)\s*)?(?:\d+(?:\.\d+)?\s*(?:crores?|cr|lakhs?|lacs?|lac|lk|l|k|thousands?|hazar)\b|\d{1,3}(?:,\d{2,3})+(?:\.\d+)?|\d+(?:\.\d+)?)"


def _extract_amount_for_concept(
    cleaned_text: str,
    keywords: List[str]
) -> Tuple[Optional[float], Optional[str]]:
    """
    Look for an amount tightly bound to one of the concept keywords.
    Supports English & Hinglish connectors like 'in', 'of', 'me', 'ka', 'mein'.
    Periodicity (monthly/annual) is only recognized if immediately following the number.
    """
    connector = r"(?:(?:\s+(?:in|of|is|are|me|mein|ka|ke|ki|ko|premium|interest|invested|contribution|payment|paid|liya|diya|dala|hai))+|\s*[:=,-]?\s*)"

    for kw in keywords:
        # Pattern 1: keyword followed by connectors and number
        # e.g., "rent is 25k", "PPF me 1.5 lakh", "LIC ka premium 60000"
        p1 = rf"\b{re.escape(kw)}\b{connector}*?\s*({NUM_TOKEN_PATTERN})(?:\s*(per month|p\.m\.|pm|monthly|har mahine|mahine ka|per annum|p\.a\.|pa|annually|annual|salana))?"
        m = re.search(p1, cleaned_text, re.IGNORECASE)
        if m:
            num_str = m.group(1).strip()
            num = parse_indian_number(num_str)
            if num is not None:
                period_str = m.group(2)
                periodicity = None
                if period_str:
                    period_lower = period_str.lower()
                    if any(w in period_lower for w in ["month", "pm", "p.m.", "mahine"]):
                        periodicity = "monthly"
                    elif any(w in period_lower for w in ["annum", "annual", "pa", "p.a.", "salana"]):
                        periodicity = "annual"
                return num, periodicity

        # Pattern 2: number followed by connectors and keyword
        # e.g., "1.5 lakh in PPF", "25k rent"
        p2 = rf"({NUM_TOKEN_PATTERN})\s*{connector}*?\b{re.escape(kw)}\b"
        m = re.search(p2, cleaned_text, re.IGNORECASE)
        if m:
            num_str = m.group(1).strip()
            num = parse_indian_number(num_str)
            if num is not None:
                return num, None

    return None, None


def parse_natural_language_input(query: str) -> ParseResult:
    """
    Deterministic rule-based parser that converts natural language input
    into structured TaxpayerInput or generates specific clarification questions.
    """
    raw_query = query.strip()
    if not raw_query:
        return ParseResult(
            status="error",
            clarification_questions=["Please provide your tax information (e.g. salary, rent, investments)."],
            raw_query=raw_query,
        )

    text_lower = raw_query.lower()
    entities: Dict[str, Any] = {}
    warnings: List[str] = []
    questions: List[str] = []

    # 1. Financial Year Detection & Masking
    fy: Optional[str] = None
    if re.search(r"\b(2025[-–]26|25[-–]26|ay\s*2026[-–]27|ay\s*26[-–]27)\b", text_lower):
        fy = "2025-26"
    elif re.search(r"\b(2024[-–]25|24[-–]25|ay\s*2025[-–]26|ay\s*25[-–]26)\b", text_lower):
        fy = "2024-25"
    entities["financial_year"] = fy

    # Mask FY from text so year digits (2024, 2025) don't get parsed as income numbers
    working_text = re.sub(r"\b(fy|ay)?\s*(2024[-–]25|2025[-–]26|24[-–]25|25[-–]26|2025|2026|2024)\b", " ", text_lower)

    # 2. Regime Detection
    regime: Optional[str] = None
    has_old = bool(re.search(r"\b(old regime|purana regime|old tax regime|purane regime)\b", working_text))
    has_new = bool(re.search(r"\b(new regime|naya regime|new tax regime|naye regime)\b", working_text))

    if has_old and has_new:
        return ParseResult(
            status="contradiction_detected",
            clarification_questions=[
                "You mentioned both 'old regime' and 'new regime'. Please clarify which tax regime you wish to use, or ask for a comparative evaluation."
            ],
            raw_query=raw_query,
            detected_entities={"contradiction": "both regimes specified"},
        )
    elif has_old:
        regime = "old"
    elif has_new:
        regime = "new"
    entities["regime"] = regime

    # 3. Salary & CTC Detection
    salary_keywords = [
        "gross salary", "gross pay", "salary is", "salary of", "salary",
        "meri salary", "mera salary", "kamata hu", "earning", "income is",
        "annual income", "package is", "package of", "package", "ctc is", "ctc of", "ctc"
    ]
    sal_val, sal_period = _extract_amount_for_concept(working_text, salary_keywords)

    gross_salary = None
    ctc = None

    if sal_val is not None:
        if "ctc" in working_text and sal_val > 0:
            ctc = sal_val * 12 if sal_period == "monthly" else sal_val
            gross_salary = ctc
            warnings.append(f"CTC of Rs. {ctc:,.0f} used as gross salary.")
        else:
            gross_salary = sal_val * 12 if sal_period == "monthly" else sal_val
            if sal_period == "monthly":
                warnings.append(f"Monthly salary Rs. {sal_val:,.0f} annualized to Rs. {gross_salary:,.0f}/year.")

    # Fallback: check standalone salary pattern like "salary 12L" or "sal 10 lakh"
    if gross_salary is None:
        m_sal = re.search(r"\b(?:salary|sal)\s*[:=]?\s*(\d+(?:\.\d+)?\s*(?:crores?|cr|lakhs?|lacs?|lac|lk|l|k|thousands?|hazar)?)\b", working_text)
        if m_sal:
            val = parse_indian_number(m_sal.group(1))
            if val is not None:
                gross_salary = val

    entities["gross_salary"] = gross_salary
    entities["ctc"] = ctc

    # 4. Basic Salary & DA
    basic_val, basic_period = _extract_amount_for_concept(
        working_text, ["basic salary", "basic pay", "basic is", "basic"]
    )
    basic_salary = (basic_val * 12 if basic_period == "monthly" else basic_val) if basic_val else 0.0
    entities["basic_salary"] = basic_salary

    da_val, _ = _extract_amount_for_concept(working_text, ["dearness allowance", "da is", "da"])
    da = da_val or 0.0
    da_retirement = bool(re.search(r"\b(da forms part|retirement benefits|qualifying da)\b", working_text))
    entities["da"] = da
    entities["da_forms_part_of_retirement_benefits"] = da_retirement

    # 5. Rent & HRA
    rent_val, rent_period = _extract_amount_for_concept(
        working_text, ["monthly rent", "rent paid", "paying rent", "kiraya", "rent"]
    )
    annual_rent = 0.0
    if rent_val is not None:
        # If rent is explicitly monthly or <= 100k, treat as monthly
        if rent_period == "monthly" or (rent_period is None and rent_val <= 100_000):
            annual_rent = rent_val * 12
            warnings.append(f"Rent of Rs. {rent_val:,.0f} treated as monthly (Rs. {annual_rent:,.0f}/year).")
        else:
            annual_rent = rent_val
    entities["annual_rent"] = annual_rent

    hra_val, hra_period = _extract_amount_for_concept(
        working_text, ["hra received", "hra is", "hra of", "hra"]
    )
    hra_received = 0.0
    if hra_val is not None:
        hra_received = (hra_val * 12 if hra_period == "monthly" else hra_val)
    entities["hra_received"] = hra_received

    # 6. City / Metro
    city_type = "non_metro"
    for metro in METRO_CITIES:
        if re.search(rf"\b{metro}\b", working_text):
            city_type = "metro"
            break
    entities["city_type"] = city_type

    # 7. Deductions: Section 80C
    c_val, _ = _extract_amount_for_concept(
        working_text,
        ["section 80c", "80c", "ppf", "elss", "lic", "epf", "life insurance", "provident fund"]
    )
    sec_80c = c_val or 0.0
    entities["section_80c"] = sec_80c

    # 8. Deductions: Section 80CCD(1B) NPS
    nps_val, _ = _extract_amount_for_concept(
        working_text,
        ["80ccd(1b)", "80ccd1b", "80ccd", "nps tier 1", "nps contribution", "nps", "national pension"]
    )
    sec_80ccd_1b = nps_val or 0.0
    entities["section_80ccd_1b"] = sec_80ccd_1b

    # 9. Deductions: Section 80D Health Insurance & Senior Citizen
    parents_senior = bool(re.search(
        r"\b(parents are senior|parents senior|senior citizen parents|mata pita bujurg|mother senior|father senior)\b",
        working_text
    ))
    self_senior = bool(re.search(
        r"\b(i am senior citizen|self senior|am senior|age 60\+|age above 60)\b",
        working_text
    ))
    entities["parents_are_senior"] = parents_senior
    entities["self_is_senior"] = self_senior

    parents_med_val, _ = _extract_amount_for_concept(
        working_text, ["parents medical", "parents insurance", "parents health insurance", "parents mediclaim"]
    )
    parents_medical = parents_med_val or 0.0

    self_med_val, _ = _extract_amount_for_concept(
        working_text,
        ["health insurance", "mediclaim", "medical insurance", "80d", "medical premium"]
    )
    self_family_medical = self_med_val or 0.0
    if parents_medical > 0 and self_family_medical == parents_medical:
        self_family_medical = 0.0  # Avoid duplicate attribution

    entities["self_family_medical"] = self_family_medical
    entities["parents_medical"] = parents_medical

    # 10. Home Loan Interest
    hl_val, _ = _extract_amount_for_concept(
        working_text,
        ["home loan interest", "housing loan interest", "interest on home loan", "home loan"]
    )
    home_loan_interest = hl_val or 0.0
    entities["home_loan_interest"] = home_loan_interest

    # --- Validation & Clarification Checks ---

    # Missing essential: Gross salary
    if gross_salary is None or gross_salary <= 0:
        questions.append("What is your annual gross salary or monthly take-home/CTC?")

    # Contradiction: Basic salary > Gross salary
    if gross_salary is not None and basic_salary > gross_salary:
        return ParseResult(
            status="contradiction_detected",
            clarification_questions=[
                f"Basic salary (Rs. {basic_salary:,.0f}) cannot exceed gross salary (Rs. {gross_salary:,.0f}). Please verify the amounts."
            ],
            detected_entities=entities,
            raw_query=raw_query,
            warnings=warnings,
        )

    # Missing regime: Do not silently guess regime if not provided
    if regime is None:
        questions.append(
            "Which tax regime do you prefer to calculate under ('old' or 'new')? (You can also request a comparison of both regimes.)"
        )

    # Missing financial year: Ask or state explicitly
    if fy is None:
        questions.append(
            "Which financial year are you filing for: FY 2024-25 (AY 2025-26) or FY 2025-26 (AY 2026-27)?"
        )

    # Missing rent support: If rent mentioned, but no basic salary or HRA received
    if annual_rent > 0 and regime == "old":
        if basic_salary == 0:
            warnings.append(
                "Rent was provided, but basic salary is missing. HRA exemption calculation defaults basic salary to 50% of gross salary unless specified."
            )
            if gross_salary:
                basic_salary = gross_salary * 0.50
        if hra_received == 0:
            warnings.append(
                "Rent was provided, but HRA received was not specified. HRA exemption requires actual HRA received."
            )

    if questions:
        return ParseResult(
            status="clarification_needed",
            taxpayer_input=None,
            clarification_questions=questions,
            detected_entities=entities,
            warnings=warnings,
            raw_query=raw_query,
        )

    # Construct validated TaxpayerInput
    try:
        taxpayer = TaxpayerInput(
            gross_salary=gross_salary,
            regime=regime,
            financial_year=fy,
            ctc=ctc,
            basic_salary=basic_salary,
            da=da,
            da_forms_part_of_retirement_benefits=da_retirement,
            hra_received=hra_received,
            annual_rent=annual_rent,
            city_type=city_type,
            section_80c=sec_80c,
            section_80ccd_1b=sec_80ccd_1b,
            self_family_medical=self_family_medical,
            parents_medical=parents_medical,
            self_is_senior=self_senior,
            parents_are_senior=parents_senior,
            home_loan_interest=home_loan_interest,
        )
        return ParseResult(
            status="success",
            taxpayer_input=taxpayer,
            clarification_questions=[],
            detected_entities=entities,
            warnings=warnings,
            raw_query=raw_query,
        )
    except Exception as e:
        return ParseResult(
            status="error",
            clarification_questions=[f"Validation error: {str(e)}"],
            detected_entities=entities,
            warnings=warnings,
            raw_query=raw_query,
        )
