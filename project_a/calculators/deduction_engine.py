from project_a.calculators.deductions import (
    calculate_standard_deduction,
    calculate_hra_exemption,
    calculate_80c_deduction,
    calculate_80ccd_1b,
    calculate_80d_deduction,
    calculate_home_loan_deduction,
)


def calculate_deductions(taxpayer):
    regime = taxpayer.regime
    gross_salary = taxpayer.gross_salary
    financial_year = getattr(taxpayer, "financial_year", "2024-25")

    # Standard deduction is available in both regimes.
    standard_deduction = calculate_standard_deduction(
        gross_salary,
        regime,
        financial_year=financial_year
    )

    # Initialise old-regime deductions.
    hra_exemption = 0
    section_80c = 0
    section_80ccd_1b = 0
    section_80d = 0
    home_loan_deduction = 0

    # Additional deductions are available under the old regime only.
    if regime == "old":
        qualifying_da = (
            taxpayer.da
            if taxpayer.da_forms_part_of_retirement_benefits
            else 0
        )

        hra_exemption = calculate_hra_exemption(
            basic_salary=taxpayer.basic_salary,
            da=qualifying_da,
            hra_received=taxpayer.hra_received,
            annual_rent=taxpayer.annual_rent,
            city_type=taxpayer.city_type
        )

        section_80c = calculate_80c_deduction(
            taxpayer.section_80c
        )

        section_80ccd_1b = calculate_80ccd_1b(
            taxpayer.section_80ccd_1b
        )

        section_80d = calculate_80d_deduction(
            self_family_amount=taxpayer.self_family_medical,
            parents_amount=taxpayer.parents_medical,
            self_is_senior=taxpayer.self_is_senior,
            parents_are_senior=taxpayer.parents_are_senior
        )

        home_loan_deduction = calculate_home_loan_deduction(
            taxpayer.home_loan_interest
        )

    total_deductions = (
        standard_deduction
        + hra_exemption
        + section_80c
        + section_80ccd_1b
        + section_80d
        + home_loan_deduction
    )

    taxable_income = max(
        0,
        gross_salary - total_deductions
    )

    return {
        "gross_salary": gross_salary,
        "regime": regime,
        "financial_year": financial_year,
        "standard_deduction": standard_deduction,
        "hra_exemption": hra_exemption,
        "section_80c": section_80c,
        "section_80ccd_1b": section_80ccd_1b,
        "section_80d": section_80d,
        "home_loan_deduction": home_loan_deduction,
        "total_deductions": total_deductions,
        "taxable_income": taxable_income
    }
