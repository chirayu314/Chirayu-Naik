import pytest

from project_a.config.tax_rules_2024_25 import (
    OLD_REGIME_SLABS,
    NEW_REGIME_SLABS
)

from project_a.calculators.slab_calculator import (
    calculate_slab_tax
)


def test_new_regime_10_lakh():
    result = calculate_slab_tax(1000000, NEW_REGIME_SLABS)
    assert result == 50000


def test_old_regime_10_lakh():
    result = calculate_slab_tax(1000000, OLD_REGIME_SLABS)
    assert result == 112500


def test_zero_income():
    result = calculate_slab_tax(0, NEW_REGIME_SLABS)
    assert result == 0


def test_negative_income():
    with pytest.raises(ValueError):
        calculate_slab_tax(-1000, NEW_REGIME_SLABS)


def test_unrounded_slab_tax():
    result = calculate_slab_tax(250001, OLD_REGIME_SLABS)
    assert result == 0.05