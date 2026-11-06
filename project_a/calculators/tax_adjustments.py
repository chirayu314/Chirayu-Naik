"""
Tax adjustments: Section 87A rebate, surcharge rates, surcharge marginal relief, and cess.
Supports FY 2024-25 and FY 2025-26.
"""

def calculate_87a_rebate(
    taxable_income,
    tax_before_rebate,
    regime,
    is_resident=True,
    financial_year="2024-25"
):
    """
    Calculate Section 87A rebate:
    - Non-resident: No rebate.
    - Old Regime (both FY): taxable income <= 5L -> max Rs. 12,500. No marginal relief.
    - New Regime FY 2024-25: taxable income <= 7L -> max Rs. 25,000. Marginal relief above 7L.
    - New Regime FY 2025-26: taxable income <= 12L -> max Rs. 60,000. Marginal relief above 12L.
    """
    if taxable_income < 0 or tax_before_rebate < 0:
        raise ValueError("Income and tax cannot be negative")

    if regime not in ("old", "new"):
        raise ValueError("Invalid tax regime")

    if not is_resident:
        return 0.0

    if regime == "old":
        if taxable_income <= 500000:
            return float(min(tax_before_rebate, 12500))
        return 0.0

    # New regime
    if financial_year == "2025-26":
        threshold = 1200000.0
        max_rebate = 60000.0
    else:  # default 2024-25
        threshold = 700000.0
        max_rebate = 25000.0

    if taxable_income <= threshold:
        return float(min(tax_before_rebate, max_rebate))

    # Marginal relief under first proviso to Section 87A
    # Net tax payable shall not exceed (taxable_income - threshold)
    excess_income = taxable_income - threshold
    rebate = max(0.0, tax_before_rebate - excess_income)
    return float(min(tax_before_rebate, rebate))


def calculate_surcharge_rate(taxable_income, regime):
    """
    Surcharge rates under Income Tax Act:
    - Up to 50L: 0%
    - 50L to 1Cr: 10%
    - 1Cr to 2Cr: 15%
    - 2Cr to 5Cr: 25%
    - Above 5Cr: 37% (Old regime), 25% capped (New regime under Section 115BAC)
    """
    if regime not in ("old", "new"):
        raise ValueError("Invalid tax regime")

    if taxable_income <= 5000000:
        return 0.00
    elif taxable_income <= 10000000:
        return 0.10
    elif taxable_income <= 20000000:
        return 0.15
    elif taxable_income <= 50000000:
        return 0.25
    else:
        if regime == "old":
            return 0.37
        return 0.25


def get_surcharge_thresholds(regime):
    """Return applicable surcharge thresholds in ascending order."""
    if regime == "old":
        return [5000000, 10000000, 20000000, 50000000]
    elif regime == "new":
        return [5000000, 10000000, 20000000]
    else:
        raise ValueError("Invalid tax regime")


def calculate_tax_with_surcharge(
    taxable_income,
    tax_after_rebate,
    regime,
    tax_at_threshold
):
    """
    Calculate tax after surcharge and marginal relief.
    tax_at_threshold must return tax after rebate at the threshold income.
    """
    if taxable_income < 0 or tax_after_rebate < 0:
        raise ValueError("Income and tax cannot be negative")

    rate = calculate_surcharge_rate(taxable_income, regime)
    surcharge = tax_after_rebate * rate
    actual_tax = tax_after_rebate + surcharge

    applicable_thresholds = [
        t for t in get_surcharge_thresholds(regime) if taxable_income > t
    ]

    if not applicable_thresholds:
        return actual_tax

    threshold = max(applicable_thresholds)
    base_tax = tax_at_threshold(threshold)
    threshold_rate = calculate_surcharge_rate(threshold, regime)
    threshold_surcharge = base_tax * threshold_rate
    tax_at_threshold_with_surcharge = base_tax + threshold_surcharge

    maximum_tax = tax_at_threshold_with_surcharge + (taxable_income - threshold)
    return min(actual_tax, maximum_tax)


HEALTH_EDUCATION_CESS_RATE = 0.04


def calculate_cess(tax_after_surcharge):
    """Health and Education Cess at 4% on (tax + surcharge)."""
    if tax_after_surcharge < 0:
        raise ValueError("Tax cannot be negative")
    return tax_after_surcharge * HEALTH_EDUCATION_CESS_RATE
