"""
Declarative Rule Executor.
Executes declarative tax rule specifications against taxpayer inputs safely without eval() or exec().
"""

from typing import Dict, Any, List
from project_a.compiled_rules.declarative_schema import (
    DeclarativeTaxYearSpecification,
    DeclarativeRegimeRules,
)
from project_a.models.user_input import TaxpayerInput


def _round_statutory(amount: float, multiple: int = 10) -> int:
    if amount < 0:
        raise ValueError("Amount cannot be negative")
    half = multiple / 2.0
    return int((amount + half) // multiple) * multiple


def execute_declarative_rules(
    taxpayer: TaxpayerInput,
    spec: DeclarativeTaxYearSpecification
) -> Dict[str, Any]:
    """
    Executes compiled declarative tax rules against taxpayer input.
    Guarantees pure deterministic calculation and zero arbitrary execution.
    """
    regime_rules: DeclarativeRegimeRules = (
        spec.old_regime if taxpayer.regime == "old" else spec.new_regime
    )

    gross_salary = taxpayer.gross_salary

    # 1. Standard Deduction
    standard_deduction = min(gross_salary, regime_rules.standard_deduction)

    # 2. Itemized deductions (Old regime only)
    hra_exemption = 0.0
    sec_80c = 0.0
    sec_80ccd = 0.0
    sec_80d = 0.0
    hl_deduction = 0.0

    if regime_rules.allows_hra and taxpayer.annual_rent > 0:
        qualifying_da = taxpayer.da if taxpayer.da_forms_part_of_retirement_benefits else 0.0
        salary_for_hra = taxpayer.basic_salary + qualifying_da
        if salary_for_hra > 0:
            city_factor = 0.50 if taxpayer.city_type == "metro" else 0.40
            rent_excess = max(0.0, taxpayer.annual_rent - (0.10 * salary_for_hra))
            hra_exemption = min(float(taxpayer.hra_received), float(rent_excess), float(salary_for_hra * city_factor))
            hra_exemption = round(hra_exemption)

    if regime_rules.allows_80c:
        sec_80c = min(taxpayer.section_80c, 150000.0)

    if regime_rules.allows_80ccd_1b:
        sec_80ccd = min(taxpayer.section_80ccd_1b, 50000.0)

    if regime_rules.allows_80d:
        self_cap = 50000.0 if taxpayer.self_is_senior else 25000.0
        parents_cap = 50000.0 if taxpayer.parents_are_senior else 25000.0
        sec_80d = min(taxpayer.self_family_medical, self_cap) + min(taxpayer.parents_medical, parents_cap)

    if regime_rules.allows_home_loan:
        hl_deduction = min(taxpayer.home_loan_interest, 200000.0)

    total_deductions = (
        standard_deduction + hra_exemption + sec_80c + sec_80ccd + sec_80d + hl_deduction
    )
    raw_taxable = max(0.0, gross_salary - total_deductions)

    # 3. Section 288A Rounding
    taxable_income = _round_statutory(raw_taxable, spec.statutory_rounding_multiple)

    # 4. Slabs
    tax_before_rebate = 0.0
    prev_limit = 0.0
    for slab in regime_rules.slabs:
        upper = float("inf") if slab.upper_limit is None or slab.upper_limit < 0 else slab.upper_limit
        taxable_in_slab = min(taxable_income, upper) - prev_limit
        if taxable_in_slab <= 0:
            break
        tax_before_rebate += taxable_in_slab * slab.rate
        prev_limit = upper
        if taxable_income <= upper:
            break

    # 5. Section 87A Rebate
    rebate = 0.0
    rebate_rule = regime_rules.rebate_87a
    if taxpayer.is_resident:
        if taxable_income <= rebate_rule.income_threshold:
            rebate = min(tax_before_rebate, rebate_rule.max_rebate)
        elif rebate_rule.marginal_relief:
            excess = taxable_income - rebate_rule.income_threshold
            relief_rebate = max(0.0, tax_before_rebate - excess)
            rebate = min(tax_before_rebate, relief_rebate)

    tax_after_rebate = max(0.0, tax_before_rebate - rebate)

    # 6. Surcharge
    surcharge_rate = 0.0
    for bracket in sorted(regime_rules.surcharge_brackets, key=lambda b: b.threshold):
        if taxable_income > bracket.threshold:
            surcharge_rate = bracket.rate

    nominal_surcharge = tax_after_rebate * surcharge_rate
    actual_tax = tax_after_rebate + nominal_surcharge

    # Surcharge marginal relief
    applicable_thresholds = [
        b.threshold for b in regime_rules.surcharge_brackets if taxable_income > b.threshold
    ]
    if applicable_thresholds:
        t_val = max(applicable_thresholds)
        # Calculate base tax at threshold
        base_tax = 0.0
        p_lim = 0.0
        for slab in regime_rules.slabs:
            u_lim = float("inf") if slab.upper_limit is None or slab.upper_limit < 0 else slab.upper_limit
            taxable_chunk = min(t_val, u_lim) - p_lim
            if taxable_chunk <= 0:
                break
            base_tax += taxable_chunk * slab.rate
            p_lim = u_lim
            if t_val <= u_lim:
                break
        t_rate = 0.0
        for b in sorted(regime_rules.surcharge_brackets, key=lambda x: x.threshold):
            if t_val > b.threshold:
                t_rate = b.rate
        t_surcharge = base_tax * t_rate
        max_permitted_tax = (base_tax + t_surcharge) + (taxable_income - t_val)
        actual_tax = min(actual_tax, max_permitted_tax)

    tax_after_surcharge = actual_tax
    surcharge_amount = max(0.0, tax_after_surcharge - tax_after_rebate)

    # 7. Cess & Final Rounding
    cess = tax_after_surcharge * spec.cess_rate
    tax_before_final_rounding = tax_after_surcharge + cess
    final_tax = _round_statutory(tax_before_final_rounding, spec.statutory_rounding_multiple)

    return {
        "approach": "llm_compiled_rules",
        "provenance": spec.provenance,
        "financial_year": spec.financial_year,
        "regime": taxpayer.regime,
        "gross_salary": gross_salary,
        "standard_deduction": standard_deduction,
        "hra_exemption": hra_exemption,
        "section_80c": sec_80c,
        "section_80ccd_1b": sec_80ccd,
        "section_80d": sec_80d,
        "home_loan_deduction": hl_deduction,
        "total_deductions": total_deductions,
        "taxable_income": taxable_income,
        "tax_before_rebate": tax_before_rebate,
        "rebate_87a": rebate,
        "tax_after_rebate": tax_after_rebate,
        "surcharge_rate": surcharge_rate,
        "surcharge_amount": surcharge_amount,
        "tax_after_surcharge": tax_after_surcharge,
        "cess": cess,
        "final_tax": final_tax,
    }

