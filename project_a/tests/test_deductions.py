from project_a.calculators.deductions import (
    calculate_standard_deduction,
    calculate_hra_exemption,
    calculate_80c_deduction,
    calculate_80ccd_1b,
    calculate_80d_deduction,
    calculate_home_loan_deduction
)


def test_old_standard_deduction():
    assert calculate_standard_deduction(
        1200000, "old"
    ) == 50000


def test_new_standard_deduction():
    assert calculate_standard_deduction(
        1200000, "new"
    ) == 75000


def test_hra():
    assert calculate_hra_exemption(
        500000, 50000, 200000, 180000, "metro"
    ) == 125000


def test_80c():
    assert calculate_80c_deduction(180000) == 150000


def test_80ccd():
    assert calculate_80ccd_1b(60000) == 50000


def test_80d():
    assert calculate_80d_deduction(
        20000, 45000, False, True
    ) == 65000


def test_home_loan():
    assert calculate_home_loan_deduction(
        250000
    ) == 200000