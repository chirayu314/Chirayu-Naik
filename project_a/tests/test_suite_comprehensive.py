"""
Comprehensive Tax Engine Test Suite.
Exhaustively tests all statutory boundaries, financial years, regimes,
rebate thresholds, surcharge marginal relief, deductions, statutory rounding,
law-change comparisons, and declarative compiled-rule execution.
"""

import pytest
from pydantic import ValidationError

from project_a.models.user_input import TaxpayerInput
from project_a.calculators.tax_engine import (
    calculate_income_tax,
    compare_regimes,
    round_to_nearest_10,
)
from project_a.calculators.slab_calculator import calculate_slab_tax
from project_a.calculators.tax_adjustments import calculate_87a_rebate, calculate_surcharge_rate
from project_a.config.rule_loader import get_tax_rules
from project_a.llm.compiled_rules_engine import CompiledRulesTaxEngine


# =====================================================================
# 1. SLAB BOUNDARIES: OLD REGIME (FY 2024-25 & FY 2025-26)
# =====================================================================
@pytest.mark.parametrize(
    "income, expected_tax",
    [
        (249990, 0.0),            # Just below 2.5L
        (250000, 0.0),            # Exactly at 2.5L
        (250010, 0.5),            # Just above 2.5L (5% on 10)
        (499990, 12499.5),        # Just below 5L
        (500000, 12500.0),        # Exactly at 5L
        (500010, 12502.0),        # Just above 5L (20% on 10)
        (999990, 112498.0),       # Just below 10L
        (1000000, 112500.0),      # Exactly at 10L
        (1000010, 112503.0),      # Just above 10L (30% on 10)
    ]
)
def test_old_regime_slab_boundaries(income, expected_tax):
    rules = get_tax_rules("2024-25")
    tax = calculate_slab_tax(income, rules.old_slabs)
    assert round(tax, 2) == round(expected_tax, 2)


# =====================================================================
# 2. SLAB BOUNDARIES: NEW REGIME FY 2024-25
# =====================================================================
@pytest.mark.parametrize(
    "income, expected_tax",
    [
        (299990, 0.0),            # Just below 3L
        (300000, 0.0),            # Exactly at 3L
        (300010, 0.5),            # Just above 3L (5% on 10)
        (699990, 19999.5),        # Just below 7L
        (700000, 20000.0),        # Exactly at 7L
        (700010, 20001.0),        # Just above 7L (10% on 10)
        (999990, 49999.0),        # Just below 10L
        (1000000, 50000.0),       # Exactly at 10L
        (1000010, 50001.5),       # Just above 10L (15% on 10)
        (1199990, 79998.5),       # Just below 12L
        (1200000, 80000.0),       # Exactly at 12L
        (1200010, 80002.0),       # Just above 12L (20% on 10)
        (1499990, 139998.0),      # Just below 15L
        (1500000, 140000.0),      # Exactly at 15L
        (1500010, 140003.0),      # Just above 15L (30% on 10)
    ]
)
def test_new_regime_2024_25_slab_boundaries(income, expected_tax):
    rules = get_tax_rules("2024-25")
    tax = calculate_slab_tax(income, rules.new_slabs)
    assert round(tax, 2) == round(expected_tax, 2)


# =====================================================================
# 3. SLAB BOUNDARIES: NEW REGIME FY 2025-26 (FINANCE ACT 2025)
# =====================================================================
@pytest.mark.parametrize(
    "income, expected_tax",
    [
        (399990, 0.0),            # Below 4L
        (400000, 0.0),            # Exactly at 4L
        (400010, 0.5),            # Above 4L (5% on 10)
        (799990, 19999.5),        # Below 8L
        (800000, 20000.0),        # Exactly at 8L
        (800010, 20001.0),        # Above 8L (10% on 10)
        (1199990, 59999.0),       # Below 12L
        (1200000, 60000.0),       # Exactly at 12L
        (1200010, 60001.5),       # Above 12L (15% on 10)
        (1599990, 119998.5),      # Below 16L
        (1600000, 120000.0),      # Exactly at 16L
        (1600010, 120002.0),      # Above 16L (20% on 10)
        (1999990, 199998.0),      # Below 20L
        (2000000, 200000.0),      # Exactly at 20L
        (2000010, 200002.5),      # Above 20L (25% on 10)
        (2399990, 299997.5),      # Below 24L
        (2400000, 300000.0),      # Exactly at 24L
        (2400010, 300003.0),      # Above 24L (30% on 10)
    ]
)
def test_new_regime_2025_26_slab_boundaries(income, expected_tax):
    rules = get_tax_rules("2025-26")
    tax = calculate_slab_tax(income, rules.new_slabs)
    assert round(tax, 2) == round(expected_tax, 2)


# =====================================================================
# 4. SECTION 87A REBATE & MARGINAL RELIEF (FY 2024-25 & FY 2025-26)
# =====================================================================
@pytest.mark.parametrize(
    "income, tax_before_rebate, regime, fy, expected_rebate, expected_tax_after",
    [
        # Old regime (threshold 5L, max 12500, no marginal relief)
        (490000, 12000, "old", "2024-25", 12000.0, 0.0),
        (500000, 12500, "old", "2024-25", 12500.0, 0.0),
        (500010, 12502, "old", "2024-25", 0.0, 12502.0),
        (510000, 14500, "old", "2024-25", 0.0, 14500.0),

        # New regime FY 2024-25 (threshold 7L, max 25000, with marginal relief)
        (690000, 19500, "new", "2024-25", 19500.0, 0.0),
        (700000, 20000, "new", "2024-25", 20000.0, 0.0),
        (705000, 20500, "new", "2024-25", 15500.0, 5000.0),   # tax after rebate = excess = 5k
        (710000, 21000, "new", "2024-25", 11000.0, 10000.0),  # tax after rebate = excess = 10k
        (720000, 22000, "new", "2024-25", 2000.0, 20000.0),   # tax after rebate = excess = 20k
        (725000, 22500, "new", "2024-25", 0.0, 22500.0),      # excess (25k) >= tax_before (22.5k)
        (730000, 23000, "new", "2024-25", 0.0, 23000.0),

        # New regime FY 2025-26 (threshold 12L, max 60000, with marginal relief)
        (1190000, 59000, "new", "2025-26", 59000.0, 0.0),
        (1200000, 60000, "new", "2025-26", 60000.0, 0.0),
        (1205000, 60750, "new", "2025-26", 55750.0, 5000.0),  # tax after rebate = excess = 5k
        (1210000, 61500, "new", "2025-26", 51500.0, 10000.0), # tax after rebate = excess = 10k
        (1220000, 63000, "new", "2025-26", 43000.0, 20000.0), # tax after rebate = excess = 20k
        (1250000, 67500, "new", "2025-26", 17500.0, 50000.0), # tax after rebate = excess = 50k
        (1270000, 70500, "new", "2025-26", 500.0, 70000.0),   # tax after rebate = excess = 70k
        (1275000, 71250, "new", "2025-26", 0.0, 71250.0),     # excess (75k) >= tax_before (71.25k)
    ]
)
def test_section_87a_rebate_and_marginal_relief(
    income, tax_before_rebate, regime, fy, expected_rebate, expected_tax_after
):
    rebate = calculate_87a_rebate(
        taxable_income=income,
        tax_before_rebate=tax_before_rebate,
        regime=regime,
        is_resident=True,
        financial_year=fy
    )
    assert rebate == expected_rebate
    assert (tax_before_rebate - rebate) == expected_tax_after


# =====================================================================
# 5. SURCHARGE RATES AND MARGINAL RELIEF
# =====================================================================
@pytest.mark.parametrize(
    "income, regime, expected_rate",
    [
        (4999990, "old", 0.00),
        (5000000, "old", 0.00),
        (5000010, "old", 0.10),
        (9999990, "old", 0.10),
        (10000000, "old", 0.10),
        (10000010, "old", 0.15),
        (19999990, "old", 0.15),
        (20000000, "old", 0.15),
        (20000010, "old", 0.25),
        (49999990, "old", 0.25),
        (50000000, "old", 0.25),
        (50000010, "old", 0.37),

        # New regime capping at 25% above 5 Crore
        (50000010, "new", 0.25),
        (60000000, "new", 0.25),
        (100000000, "new", 0.25),
    ]
)
def test_surcharge_rates(income, regime, expected_rate):
    assert calculate_surcharge_rate(income, regime) == expected_rate


def test_surcharge_marginal_relief_at_50_lakh_boundary():
    # At 51 Lakh Old Regime, tax at 50L = 13,12,500. Excess income = 1,00,000.
    # Max tax permitted = 13,12,500 + 1,00,000 = 14,12,500.
    taxpayer = TaxpayerInput(
        gross_salary=5150000,  # 51.5L - 50k SD = 51L taxable
        regime="old",
        financial_year="2024-25"
    )
    res = calculate_income_tax(taxpayer)
    assert res["taxable_income"] == 5100000
    assert res["tax_after_surcharge"] == 1412500
    assert res["marginal_relief_surcharge"] > 0


def test_surcharge_marginal_relief_at_1_crore_boundary():
    taxpayer = TaxpayerInput(
        gross_salary=10150000,  # 101.5L - 50k SD = 101L taxable
        regime="old",
        financial_year="2024-25"
    )
    res = calculate_income_tax(taxpayer)
    assert res["taxable_income"] == 10100000
    assert res["surcharge_rate"] == 0.15
    # Marginal relief ensures tax payable does not jump disproportionately
    assert res["marginal_relief_surcharge"] >= 0


# =====================================================================
# 6. DEDUCTIONS & ITEMIZATION VARIATIONS
# =====================================================================
@pytest.mark.parametrize(
    "sec_80c, expected_80c",
    [
        (0, 0),
        (50000, 50000),
        (150000, 150000),
        (200000, 150000),  # capped at 1.5L
        (500000, 150000),
    ]
)
def test_80c_caps(sec_80c, expected_80c):
    tp = TaxpayerInput(gross_salary=1000000, regime="old", section_80c=sec_80c)
    res = calculate_income_tax(tp)
    assert res["section_80c"] == expected_80c


@pytest.mark.parametrize(
    "self_amt, parents_amt, self_sen, par_sen, expected_80d",
    [
        (20000, 20000, False, False, 40000),
        (30000, 30000, False, False, 50000),  # 25k + 25k
        (30000, 60000, False, True, 75000),   # 25k + 50k
        (60000, 30000, True, False, 75000),   # 50k + 25k
        (60000, 60000, True, True, 100000),   # 50k + 50k
    ]
)
def test_80d_senior_combinations(self_amt, parents_amt, self_sen, par_sen, expected_80d):
    tp = TaxpayerInput(
        gross_salary=1200000,
        regime="old",
        self_family_medical=self_amt,
        parents_medical=parents_amt,
        self_is_senior=self_sen,
        parents_are_senior=par_sen
    )
    res = calculate_income_tax(tp)
    assert res["section_80d"] == expected_80d


@pytest.mark.parametrize(
    "hl_interest, expected_hl",
    [
        (0, 0),
        (100000, 100000),
        (200000, 200000),
        (250000, 200000),  # capped at 2L
        (500000, 200000),
    ]
)
def test_home_loan_interest_cap(hl_interest, expected_hl):
    tp = TaxpayerInput(gross_salary=1500000, regime="old", home_loan_interest=hl_interest)
    res = calculate_income_tax(tp)
    assert res["home_loan_deduction"] == expected_hl


def test_home_loan_disallowed_in_new_regime():
    tp = TaxpayerInput(gross_salary=1500000, regime="new", home_loan_interest=250000)
    res = calculate_income_tax(tp)
    assert res["home_loan_deduction"] == 0


# =====================================================================
# 7. HRA EXEMPTION SCENARIOS
# =====================================================================
@pytest.mark.parametrize(
    "basic, da, da_ret, hra_rec, rent, city, expected_hra",
    [
        (500000, 0, False, 200000, 180000, "metro", 130000),       # rent - 10% basic = 1.3L
        (500000, 0, False, 200000, 180000, "non_metro", 130000),   # 40% basic = 2L, rent-10% = 1.3L
        (500000, 0, False, 100000, 250000, "metro", 100000),       # actual HRA is least (1L)
        (500000, 0, False, 300000, 400000, "non_metro", 200000),   # 40% of basic is least (2L)
        (500000, 0, False, 200000, 40000, "metro", 0),             # rent < 10% basic
        (400000, 100000, False, 150000, 150000, "metro", 110000),  # DA excluded
        (400000, 100000, True, 150000, 150000, "metro", 100000),   # DA included in salary (salary=5L)
    ]
)
def test_hra_scenarios(basic, da, da_ret, hra_rec, rent, city, expected_hra):
    tp = TaxpayerInput(
        gross_salary=1000000,
        regime="old",
        basic_salary=basic,
        da=da,
        da_forms_part_of_retirement_benefits=da_ret,
        hra_received=hra_rec,
        annual_rent=rent,
        city_type=city
    )
    res = calculate_income_tax(tp)
    assert res["hra_exemption"] == expected_hra


# =====================================================================
# 8. STATUTORY ROUNDING (SECTION 288A & 288B)
# =====================================================================
@pytest.mark.parametrize(
    "amount, expected",
    [
        (100.0, 100),
        (101.0, 100),
        (104.0, 100),
        (104.9, 100),
        (105.0, 110),
        (105.1, 110),
        (106.0, 110),
        (109.0, 110),
        (0.0, 0),
        (5.0, 10),
    ]
)
def test_statutory_rounding_rules(amount, expected):
    assert round_to_nearest_10(amount) == expected


# =====================================================================
# 9. EXTREME AND ZERO SALARY CASES
# =====================================================================
def test_zero_salary_both_regimes():
    tp_old = TaxpayerInput(gross_salary=0, regime="old")
    tp_new = TaxpayerInput(gross_salary=0, regime="new")
    assert calculate_income_tax(tp_old)["final_tax"] == 0
    assert calculate_income_tax(tp_new)["final_tax"] == 0


def test_very_high_salary_10_crore():
    tp_old = TaxpayerInput(gross_salary=100000000, regime="old", financial_year="2024-25")
    tp_new = TaxpayerInput(gross_salary=100000000, regime="new", financial_year="2024-25")
    res_old = calculate_income_tax(tp_old)
    res_new = calculate_income_tax(tp_new)
    # Under old regime above 5 Cr, surcharge is 37%
    assert res_old["surcharge_rate"] == 0.37
    # Under new regime, surcharge is capped at 25%
    assert res_new["surcharge_rate"] == 0.25
    assert res_new["final_tax"] < res_old["final_tax"]


# =====================================================================
# 10. LAW CHANGE CONTRAST: FY 2024-25 VS FY 2025-26
# =====================================================================
@pytest.mark.parametrize(
    "gross_salary, expected_tax_24_25, expected_tax_25_26",
    [
        (775000, 0, 0),         # 7.75L - 75k SD = 7L: Nil in both years (87A rebate)
        (1000000, 44200, 0),    # 10L - 75k SD = 9.25L: 24-25 has tax, 25-26 is 0 due to 12L rebate
        (1200000, 71500, 0),    # 12L - 75k SD = 11.25L: 24-25 has tax, 25-26 is 0 due to 12L rebate
        (1275000, 83200, 0),    # 12.75L - 75k SD = 12L: 25-26 tax is exactly 0
        (1500000, 130000, 97500), # 15L - 75k SD = 14.25L: 25-26 has much lower slab rates (97.5k vs 130k)
    ]
)
def test_direct_law_change_comparison(gross_salary, expected_tax_24_25, expected_tax_25_26):
    tp_24 = TaxpayerInput(gross_salary=gross_salary, regime="new", financial_year="2024-25")
    tp_25 = TaxpayerInput(gross_salary=gross_salary, regime="new", financial_year="2025-26")

    res_24 = calculate_income_tax(tp_24)
    res_25 = calculate_income_tax(tp_25)

    assert res_24["final_tax"] == expected_tax_24_25
    assert res_25["final_tax"] == expected_tax_25_26


# =====================================================================
# 11. REGIME COMPARISON RECOMMENDATION
# =====================================================================
def test_compare_regimes_prefers_old_when_deductions_are_massive():
    tp = TaxpayerInput(
        gross_salary=1200000,
        regime="new",  # initial choice will be evaluated across both
        basic_salary=600000,
        hra_received=250000,
        annual_rent=240000,
        city_type="metro",
        section_80c=150000,
        section_80ccd_1b=50000,
        self_family_medical=25000,
        parents_medical=50000,
        parents_are_senior=True,
        home_loan_interest=200000
    )
    comp = compare_regimes(tp)
    assert comp["recommended_regime"] == "old"
    assert comp["savings"] > 0


def test_compare_regimes_prefers_new_when_no_deductions():
    tp = TaxpayerInput(gross_salary=1200000, regime="old")
    comp = compare_regimes(tp)
    assert comp["recommended_regime"] == "new"
    assert comp["savings"] > 0


# =====================================================================
# 12. APPROACH 3: DECLARATIVE COMPILED RULES EXECUTION EQUALITY
# =====================================================================
@pytest.mark.parametrize(
    "gross_salary, regime, fy",
    [
        (500000, "old", "2024-25"),
        (750000, "new", "2024-25"),
        (1000000, "old", "2024-25"),
        (1200000, "new", "2024-25"),
        (1500000, "old", "2024-25"),
        (2500000, "new", "2024-25"),
        (6000000, "old", "2024-25"),
        (8000000, "new", "2024-25"),
        (60000000, "old", "2024-25"),
        (60000000, "new", "2024-25"),

        # FY 2025-26
        (500000, "old", "2025-26"),
        (800000, "new", "2025-26"),
        (1200000, "new", "2025-26"),
        (1275000, "new", "2025-26"),
        (1600000, "new", "2025-26"),
        (2400000, "new", "2025-26"),
        (3000000, "new", "2025-26"),
        (5500000, "new", "2025-26"),
    ]
)
def test_compiled_rules_engine_exact_match(gross_salary, regime, fy):
    tp = TaxpayerInput(gross_salary=gross_salary, regime=regime, financial_year=fy)
    engine = CompiledRulesTaxEngine()
    compiled_res = engine.calculate(tp)
    det_res = calculate_income_tax(tp)

    assert compiled_res["final_tax"] == det_res["final_tax"]
    assert compiled_res["taxable_income"] == det_res["taxable_income"]
    assert compiled_res["rebate_87a"] == det_res["rebate_87a"]


# =====================================================================
# 13. INPUT VALIDATION & ERROR HANDLING
# =====================================================================
def test_negative_salary_rejected():
    with pytest.raises(ValidationError):
        TaxpayerInput(gross_salary=-1000, regime="new")


def test_invalid_regime_rejected():
    with pytest.raises(ValidationError):
        TaxpayerInput(gross_salary=500000, regime="flat")


def test_invalid_fy_rejected():
    with pytest.raises(ValidationError):
        TaxpayerInput(gross_salary=500000, regime="new", financial_year="2030-31")


def test_basic_salary_exceeding_gross_rejected():
    with pytest.raises(ValidationError):
        TaxpayerInput(gross_salary=500000, basic_salary=600000, regime="old")
