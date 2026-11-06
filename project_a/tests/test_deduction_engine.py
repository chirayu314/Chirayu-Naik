from project_a.models.user_input import TaxpayerInput
from project_a.calculators.deduction_engine import calculate_deductions


def test_old_regime_deductions():

    taxpayer = TaxpayerInput(
        gross_salary=1200000,
        regime="old",
        basic_salary=600000,
        hra_received=200000,
        annual_rent=180000,
        city_type="metro",
        section_80c=150000,
        section_80ccd_1b=50000,
        self_family_medical=20000,
        parents_medical=45000,
        parents_are_senior=True
    )

    result = calculate_deductions(taxpayer)

    assert result["standard_deduction"] == 50000
    assert result["hra_exemption"] == 120000
    assert result["section_80c"] == 150000
    assert result["section_80ccd_1b"] == 50000
    assert result["section_80d"] == 65000
    assert result["total_deductions"] == 435000
    assert result["taxable_income"] == 765000


def test_new_regime_only_standard_deduction():

    taxpayer = TaxpayerInput(
        gross_salary=1200000,
        regime="new",
        basic_salary=600000,
        hra_received=200000,
        annual_rent=180000,
        section_80c=150000,
        section_80ccd_1b=50000,
        self_family_medical=20000,
        parents_medical=45000,
        home_loan_interest=200000
    )

    result = calculate_deductions(taxpayer)

    assert result["standard_deduction"] == 75000
    assert result["hra_exemption"] == 0
    assert result["section_80c"] == 0
    assert result["section_80ccd_1b"] == 0
    assert result["section_80d"] == 0
    assert result["home_loan_deduction"] == 0
    assert result["total_deductions"] == 75000
    assert result["taxable_income"] == 1125000


def test_da_not_included_in_hra_salary_by_default():

    taxpayer = TaxpayerInput(
        gross_salary=800000,
        regime="old",
        basic_salary=400000,
        da=100000,
        hra_received=150000,
        annual_rent=150000,
        city_type="metro"
    )

    result = calculate_deductions(taxpayer)

    # HRA exemption = min(150000, 110000, 200000)
    assert result["hra_exemption"] == 110000


def test_da_included_when_it_forms_part_of_retirement_benefits():

    taxpayer = TaxpayerInput(
        gross_salary=800000,
        regime="old",
        basic_salary=400000,
        da=100000,
        da_forms_part_of_retirement_benefits=True,
        hra_received=150000,
        annual_rent=150000,
        city_type="metro"
    )

    result = calculate_deductions(taxpayer)

    # HRA exemption = min(150000, 100000, 250000)
    assert result["hra_exemption"] == 100000