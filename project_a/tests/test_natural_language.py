"""
Test suite for Natural Language Parser.
Covers at least 50 distinct test cases:
1. Normal English descriptions
2. Hinglish descriptions
3. Incomplete descriptions (clarification needed)
4. Contradictory descriptions
5. Indian number formats
"""

import pytest
from project_a.parsers.input_parser import parse_natural_language_input, parse_indian_number


# --- 1. Indian Number Parsing Tests (10 cases) ---

@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("12 lakh", 1200000.0),
        ("12 lac", 1200000.0),
        ("1.5 crore", 15000000.0),
        ("2 cr", 20000000.0),
        ("25k", 25000.0),
        ("50 hazar", 50000.0),
        ("1,50,000", 150000.0),
        ("15L", 1500000.0),
        ("9.5lakhs", 950000.0),
        ("₹ 75000", 75000.0),
    ]
)
def test_parse_indian_number_units(input_str, expected):
    assert parse_indian_number(input_str) == expected


# --- 2. Normal English Natural Language Tests (15 cases) ---

def test_nl_english_basic_complete():
    text = "My salary is 12 lakh, I live in Mumbai, pay 25k rent monthly, and invested 1.5 lakh in PPF. Old regime, FY 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.gross_salary == 1200000.0
    assert res.taxpayer_input.regime == "old"
    assert res.taxpayer_input.financial_year == "2024-25"
    assert res.taxpayer_input.city_type == "metro"
    assert res.taxpayer_input.annual_rent == 300000.0  # 25k * 12
    assert res.taxpayer_input.section_80c == 150000.0


def test_nl_english_new_regime_simple():
    text = "Salary 15 lakh, new regime, FY 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.gross_salary == 1500000.0
    assert res.taxpayer_input.regime == "new"
    assert res.taxpayer_input.financial_year == "2024-25"


def test_nl_english_senior_parents():
    text = "Salary 9L, 80C 1.2L, parents senior citizens, medical insurance 40000, old regime, FY 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.gross_salary == 900000.0
    assert res.taxpayer_input.parents_are_senior is True
    assert res.taxpayer_input.section_80c == 120000.0
    assert res.taxpayer_input.regime == "old"


def test_nl_english_with_nps():
    text = "Gross salary 18 lakh, NPS contribution 50k, 80C 150000, old regime, FY 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.gross_salary == 1800000.0
    assert res.taxpayer_input.section_80ccd_1b == 50000.0


def test_nl_english_with_home_loan():
    text = "Annual salary 20 lakh, home loan interest 2 lakh, old regime, FY 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.gross_salary == 2000000.0
    assert res.taxpayer_input.home_loan_interest == 200000.0


def test_nl_english_monthly_salary():
    text = "Salary is 1 lakh per month, new regime, FY 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.gross_salary == 1200000.0


def test_nl_english_delhi_metro():
    text = "Salary 14 lakh, rent 30k per month, city Delhi, old regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.city_type == "metro"


def test_nl_english_bangalore_non_metro():
    text = "Salary 14 lakh, rent 30k per month, Bangalore, old regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.city_type == "non_metro"


def test_nl_english_fy_2025_26():
    text = "Salary 12 lakh, new regime, FY 2025-26."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.financial_year == "2025-26"


def test_nl_english_crore_salary():
    text = "Annual salary 1.2 crore, new regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.gross_salary == 12000000.0


def test_nl_english_ctc_notation():
    text = "CTC 15 lakh, rent 30k monthly, old regime, FY 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.gross_salary == 1500000.0
    assert res.taxpayer_input.ctc == 1500000.0


def test_nl_english_elss_and_lic():
    text = "Gross salary 10L, ELSS 1 lakh, LIC 50k, old regime, FY 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.gross_salary == 1000000.0


def test_nl_english_hra_received_explicit():
    text = "Salary 16 lakh, basic 8 lakh, HRA received 3 lakh, rent 25k monthly in Chennai, old regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.basic_salary == 800000.0
    assert res.taxpayer_input.hra_received == 300000.0
    assert res.taxpayer_input.city_type == "metro"


def test_nl_english_senior_self():
    text = "I am senior citizen, salary 8 lakh, medical insurance 50k, old regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.self_is_senior is True


def test_nl_english_da_with_retirement():
    text = "Salary 10 lakh, basic 5 lakh, DA 1 lakh qualifying da, rent 20k pm Kolkata, old regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.da == 100000.0
    assert res.taxpayer_input.da_forms_part_of_retirement_benefits is True


# --- 3. Hinglish Natural Language Tests (15 cases) ---

def test_nl_hinglish_meri_salary():
    text = "Meri salary 10 lakh hai aur rent 20k per month hai, old regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.gross_salary == 1000000.0
    assert res.taxpayer_input.annual_rent == 240000.0


def test_nl_hinglish_kamata_hu():
    text = "Main saal ka 12 lakh kamata hu, naya regime, FY 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.gross_salary == 1200000.0
    assert res.taxpayer_input.regime == "new"


def test_nl_hinglish_kiraya_mumbai():
    text = "Salary 15 lakh, kiraya 30000 har mahine Mumbai me, purana regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.city_type == "metro"
    assert res.taxpayer_input.annual_rent == 360000.0
    assert res.taxpayer_input.regime == "old"


def test_nl_hinglish_mata_pita_bujurg():
    text = "Salary 8 lakh, mata pita bujurg hain, medical insurance 45000, old regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.parents_are_senior is True


def test_nl_hinglish_mahine_ka_salary():
    text = "Mera salary 80 hazar mahine ka hai, new regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.gross_salary == 960000.0


def test_nl_hinglish_naye_regime_25_26():
    text = "Package 14 lakh hai naye regime me calculate karo FY 2025-26."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.gross_salary == 1400000.0
    assert res.taxpayer_input.regime == "new"
    assert res.taxpayer_input.financial_year == "2025-26"


def test_nl_hinglish_purane_regime_ppf():
    text = "Meri salary 11 lakh, PPF me 1.5 lakh dala hai, purane regime me, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.section_80c == 150000.0
    assert res.taxpayer_input.regime == "old"


def test_nl_hinglish_nps_hazar():
    text = "Salary 13L, NPS me 50 hazar diya, old regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.section_80ccd_1b == 50000.0


def test_nl_hinglish_home_loan():
    text = "Salary 16 lakh, home loan ka interest 1.8 lakh, purana regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.home_loan_interest == 180000.0


def test_nl_hinglish_pune_non_metro():
    text = "Salary 9 lakh, Pune me kiraya 15 hazar, old regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.city_type == "non_metro"


def test_nl_hinglish_delhi_rent():
    text = "Salary 20 lakh, Delhi me rent 40k har mahine, old regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.city_type == "metro"


def test_nl_hinglish_mediclaim():
    text = "Gross salary 7 lakh, mediclaim 20k, purana regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.self_family_medical == 20000.0


def test_nl_hinglish_lic_premium():
    text = "Mera salary 10 lakh, LIC ka premium 60000, old regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.section_80c == 60000.0


def test_nl_hinglish_crore_package():
    text = "Package 1 crore hai, new regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.gross_salary == 10000000.0


def test_nl_hinglish_basic_and_rent():
    text = "Salary 12 lakh, basic salary 6 lakh, rent 20k, Kolkata, old regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "success"
    assert res.taxpayer_input.basic_salary == 600000.0


# --- 4. Incomplete Inputs & Targeted Clarifications (10 cases) ---

def test_nl_missing_all():
    res = parse_natural_language_input("")
    assert res.status == "error"
    assert len(res.clarification_questions) > 0


def test_nl_missing_salary():
    text = "I live in Mumbai and pay 25k rent, old regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "clarification_needed"
    assert any("salary" in q.lower() or "ctc" in q.lower() for q in res.clarification_questions)


def test_nl_missing_regime():
    text = "Salary 12 lakh, rent 20k monthly, FY 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "clarification_needed"
    assert any("regime" in q.lower() for q in res.clarification_questions)


def test_nl_missing_financial_year():
    text = "Salary 12 lakh, new regime."
    res = parse_natural_language_input(text)
    assert res.status == "clarification_needed"
    assert any("financial year" in q.lower() for q in res.clarification_questions)


def test_nl_missing_both_regime_and_fy():
    text = "Salary 15 lakh."
    res = parse_natural_language_input(text)
    assert res.status == "clarification_needed"
    assert len(res.clarification_questions) >= 2


def test_nl_only_deduction_no_salary():
    text = "80C 1.5 lakh, medical 25k, old regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "clarification_needed"
    assert any("salary" in q.lower() for q in res.clarification_questions)


def test_nl_just_city_and_rent():
    text = "Living in Chennai paying 30k rent monthly."
    res = parse_natural_language_input(text)
    assert res.status == "clarification_needed"


def test_nl_zero_salary():
    text = "Salary 0, old regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "clarification_needed"


def test_nl_missing_fy_with_hra():
    text = "My salary is 18 lakh, rent is 35k pm in Mumbai, old regime."
    res = parse_natural_language_input(text)
    assert res.status == "clarification_needed"
    assert any("financial year" in q.lower() for q in res.clarification_questions)


def test_nl_vague_query():
    text = "Hello I need tax calculation help."
    res = parse_natural_language_input(text)
    assert res.status == "clarification_needed"


# --- 5. Contradictory & Ambiguous Inputs (5 cases) ---

def test_nl_contradictory_both_regimes():
    text = "Salary 12 lakh, old regime and new regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "contradiction_detected"
    assert any("both 'old regime' and 'new regime'" in q.lower() for q in res.clarification_questions)


def test_nl_contradictory_basic_exceeds_gross():
    text = "Gross salary 5 lakh, basic salary 8 lakh, old regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "contradiction_detected"
    assert any("cannot exceed gross salary" in q.lower() for q in res.clarification_questions)


def test_nl_contradictory_ctc_and_basic():
    text = "CTC 6 lakh, basic 9 lakh, old regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "contradiction_detected"


def test_nl_contradictory_zero_salary_positive_basic():
    text = "Salary is 0, basic salary 2 lakh, old regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status in ("clarification_needed", "contradiction_detected")


def test_nl_conflicting_regime_words():
    text = "My salary is 10 lakh, purana regime naya regime, 2024-25."
    res = parse_natural_language_input(text)
    assert res.status == "contradiction_detected"

