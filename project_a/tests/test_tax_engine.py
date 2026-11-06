
from project_a.calculators.tax_engine import (
    calculate_income_tax,
    round_to_nearest_10,
)
from project_a.models.user_input import TaxpayerInput


def test_old_regime_complete_calculation():
    taxpayer = TaxpayerInput(
        gross_salary=1200000,
        regime="old",
        basic_salary=600000,
        hra_received=200000,
        annual_rent=180000,
        city_type="metro",
        section_80c=150000,
        section_80ccd_1b=50000,
        self_family_medical=25000,
        parents_medical=50000,
        self_is_senior=False,
        parents_are_senior=True,
        home_loan_interest=200000,
    )

    result = calculate_income_tax(taxpayer)

    assert result["standard_deduction"] == 50000
    assert result["hra_exemption"] == 120000
    assert result["section_80c"] == 150000
    assert result["section_80ccd_1b"] == 50000
    assert result["section_80d"] == 75000
    assert result["home_loan_deduction"] == 200000

    assert result["total_deductions"] == 645000
    assert result["taxable_income"] == 555000
    assert result["tax_before_rebate"] == 23500
    assert result["rebate_87a"] == 0
    assert result["tax_after_rebate"] == 23500
    assert result["tax_after_surcharge"] == 23500
    assert result["cess"] == 940
    assert result["final_tax"] == 24440


def test_new_regime_complete_calculation():
    taxpayer = TaxpayerInput(
        gross_salary=1200000,
        regime="new",
    )

    result = calculate_income_tax(taxpayer)

    assert result["standard_deduction"] == 75000
    assert result["total_deductions"] == 75000
    assert result["taxable_income"] == 1125000
    assert result["tax_before_rebate"] == 68750
    assert result["rebate_87a"] == 0
    assert result["tax_after_rebate"] == 68750
    assert result["tax_after_surcharge"] == 68750
    assert result["cess"] == 2750
    assert result["final_tax"] == 71500


def test_round_to_nearest_10():
    assert round_to_nearest_10(123) == 120
    assert round_to_nearest_10(125) == 130
    assert round_to_nearest_10(128) == 130
    assert round_to_nearest_10(100) == 100
    assert round_to_nearest_10(0) == 0


def test_round_to_nearest_10_rejects_negative_amount():
    try:
        round_to_nearest_10(-10)
    except ValueError:
        pass
    else:
        raise AssertionError("Negative amounts should raise ValueError")
