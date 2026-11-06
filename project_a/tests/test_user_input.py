import pytest
from pydantic import ValidationError

from project_a.models.user_input import TaxpayerInput


def test_valid_taxpayer():
    taxpayer = TaxpayerInput(
        gross_salary=1200000,
        regime="old",
        section_80c=150000
    )

    assert taxpayer.gross_salary == 1200000
    assert taxpayer.regime == "old"
    assert taxpayer.section_80c == 150000


def test_default_values():
    taxpayer = TaxpayerInput(
        gross_salary=800000,
        regime="new"
    )

    assert taxpayer.section_80c == 0
    assert taxpayer.home_loan_interest == 0
    assert taxpayer.city_type == "non_metro"


def test_negative_salary():
    with pytest.raises(ValidationError):
        TaxpayerInput(
            gross_salary=-500000,
            regime="old"
        )


def test_invalid_regime():
    with pytest.raises(ValidationError):
        TaxpayerInput(
            gross_salary=800000,
            regime="invalid"
        )


def test_negative_deduction():
    with pytest.raises(ValidationError):
        TaxpayerInput(
            gross_salary=800000,
            regime="old",
            section_80c=-10000
        )