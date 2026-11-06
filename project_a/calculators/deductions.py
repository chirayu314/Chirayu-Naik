OLD_STANDARD_DEDUCTION = 50000
NEW_STANDARD_DEDUCTION = 75000

SECTION_80C_LIMIT = 150000
SECTION_80CCD_1B_LIMIT = 50000
HOME_LOAN_INTEREST_LIMIT = 200000


def calculate_standard_deduction(gross_salary, regime, financial_year="2024-25"):
    """
    Standard deduction under Section 16(ia):
    - Old Regime: Rs. 50,000 (capped at gross salary)
    - New Regime FY 2024-25: Rs. 75,000 (amended by Finance (No. 2) Act 2024)
    - New Regime FY 2025-26: Rs. 75,000 (Finance Act 2025)
    """
    if gross_salary < 0:
        raise ValueError("Salary cannot be negative")

    if regime == "old":
        limit = OLD_STANDARD_DEDUCTION
    elif regime == "new":
        limit = NEW_STANDARD_DEDUCTION
    else:
        raise ValueError("Invalid tax regime")

    return min(gross_salary, limit)


def calculate_hra_exemption(
    basic_salary,
    da,
    hra_received,
    annual_rent,
    city_type
):
    """
    HRA Exemption under Section 10(13A) read with Rule 2A.
    Exemption is the minimum of:
    1. Actual HRA received
    2. Rent paid - 10% of salary (basic + qualifying DA)
    3. 50% of salary (metro) or 40% of salary (non-metro)
    """
    if basic_salary < 0 or da < 0 or hra_received < 0 or annual_rent < 0:
        raise ValueError("HRA parameters cannot be negative")

    salary = basic_salary + da

    if salary <= 0:
        return 0

    city_norm = city_type.lower().strip()
    if city_norm == "metro":
        city_limit = salary * 0.50
    elif city_norm == "non_metro":
        city_limit = salary * 0.40
    else:
        raise ValueError("Invalid city type. Must be 'metro' or 'non_metro'")

    rent_limit = max(0.0, annual_rent - salary * 0.10)

    exemption = min(
        float(hra_received),
        float(rent_limit),
        float(city_limit)
    )

    return round(exemption)


def calculate_80c_deduction(investment):
    """Section 80C deduction, capped at Rs. 1,50,000."""
    if investment < 0:
        raise ValueError("Investment cannot be negative")
    return min(investment, SECTION_80C_LIMIT)


def calculate_80ccd_1b(contribution):
    """Section 80CCD(1B) additional NPS deduction, capped at Rs. 50,000."""
    if contribution < 0:
        raise ValueError("Contribution cannot be negative")
    return min(contribution, SECTION_80CCD_1B_LIMIT)


def calculate_80d_deduction(
    self_family_amount,
    parents_amount,
    self_is_senior,
    parents_are_senior
):
    """
    Section 80D health insurance deduction:
    - Self & Family: Rs. 25,000 (Rs. 50,000 if senior citizen)
    - Parents: Rs. 25,000 (Rs. 50,000 if senior citizen)
    """
    if self_family_amount < 0 or parents_amount < 0:
        raise ValueError("Medical insurance amount cannot be negative")

    self_limit = 50000 if self_is_senior else 25000
    parents_limit = 50000 if parents_are_senior else 25000

    self_deduction = min(self_family_amount, self_limit)
    parents_deduction = min(parents_amount, parents_limit)

    return self_deduction + parents_deduction


def calculate_home_loan_deduction(interest):
    """Section 24(b) deduction for self-occupied home loan interest, capped at Rs. 2,00,000."""
    if interest < 0:
        raise ValueError("Home loan interest cannot be negative")
    return min(interest, HOME_LOAN_INTEREST_LIMIT)
