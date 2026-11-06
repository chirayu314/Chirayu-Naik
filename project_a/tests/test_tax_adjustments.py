from project_a.calculators.tax_adjustments import (
    calculate_87a_rebate,
    calculate_surcharge_rate,
    calculate_tax_with_surcharge,
    calculate_cess,
)

from project_a.calculators.slab_calculator import calculate_slab_tax

from project_a.config.tax_rules_2024_25 import (
    OLD_REGIME_SLABS,
    NEW_REGIME_SLABS,
)


def calculate_tax_after_rebate(income, regime):

    if regime == "old":
        slabs = OLD_REGIME_SLABS
    else:
        slabs = NEW_REGIME_SLABS

    tax_before_rebate = calculate_slab_tax(income, slabs)

    rebate = calculate_87a_rebate(
        income,
        tax_before_rebate,
        regime
    )

    return tax_before_rebate - rebate


# Section 87A rebate tests

def test_old_regime_rebate():
    result = calculate_87a_rebate(500000, 12500, "old")
    assert result == 12500


def test_old_regime_no_rebate_above_limit():
    result = calculate_87a_rebate(510000, 13000, "old")
    assert result == 0


def test_new_regime_rebate():
    result = calculate_87a_rebate(700000, 20000, "new")
    assert result == 20000


def test_new_regime_marginal_relief():
    result = calculate_87a_rebate(710000, 21000, "new")
    assert result == 11000


def test_non_resident_no_rebate():
    result = calculate_87a_rebate(
        500000, 12500, "old", is_resident=False
    )
    assert result == 0


# Surcharge rate tests

def test_no_surcharge_below_50_lakh():
    assert calculate_surcharge_rate(4900000, "old") == 0


def test_surcharge_10_percent():
    assert calculate_surcharge_rate(6000000, "old") == 0.10


def test_surcharge_15_percent():
    assert calculate_surcharge_rate(15000000, "old") == 0.15


def test_surcharge_25_percent():
    assert calculate_surcharge_rate(30000000, "old") == 0.25


def test_old_regime_surcharge_37_percent():
    assert calculate_surcharge_rate(60000000, "old") == 0.37


def test_new_regime_surcharge_capped_at_25_percent():
    assert calculate_surcharge_rate(60000000, "new") == 0.25


# Marginal relief tests

def test_surcharge_marginal_relief_using_real_slabs():

    income = 5100000

    tax_after_rebate = calculate_tax_after_rebate(
        income, "old"
    )

    result = calculate_tax_with_surcharge(
        taxable_income=income,
        tax_after_rebate=tax_after_rebate,
        regime="old",
        tax_at_threshold=lambda threshold: (
            calculate_tax_after_rebate(threshold, "old")
        )
    )

    assert result == 1412500


def test_surcharge_without_marginal_relief_using_real_slabs():

    income = 6000000

    tax_after_rebate = calculate_tax_after_rebate(
        income, "old"
    )

    result = calculate_tax_with_surcharge(
        taxable_income=income,
        tax_after_rebate=tax_after_rebate,
        regime="old",
        tax_at_threshold=lambda threshold: (
            calculate_tax_after_rebate(threshold, "old")
        )
    )

    assert result == 1773750


# Cess test

def test_cess():
    assert calculate_cess(50000) == 2000