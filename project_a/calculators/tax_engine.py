"""
Main deterministic Income Tax Engine for salaried individuals in India.
Supports FY 2024-25 and FY 2025-26 under both Old and New tax regimes.
"""

from typing import Dict, Any, List
from project_a.calculators.deduction_engine import calculate_deductions
from project_a.calculators.slab_calculator import calculate_slab_tax
from project_a.calculators.tax_adjustments import (
    calculate_87a_rebate,
    calculate_surcharge_rate,
    calculate_tax_with_surcharge,
    calculate_cess,
)
from project_a.config.rule_loader import get_tax_rules
from project_a.config.tax_rules_2024_25 import (
    OLD_REGIME_SLABS,
    NEW_REGIME_SLABS,
)


def round_to_nearest_10(amount: float) -> int:
    """
    Statutory rounding under Sections 288A and 288B.
    Round amount to nearest Rs. 10. Halfway (5) rounds up.
    """
    if amount < 0:
        raise ValueError("Amount cannot be negative")
    return int((amount + 5) // 10) * 10


def calculate_tax_after_rebate_at_threshold(
    threshold: float,
    regime: str,
    is_resident: bool,
    financial_year: str = "2024-25"
) -> float:
    """Calculate tax after Section 87A rebate at a specific threshold."""
    rules = get_tax_rules(financial_year)
    slabs = rules.old_slabs if regime == "old" else rules.new_slabs

    tax_before_rebate = calculate_slab_tax(threshold, slabs)
    rebate = calculate_87a_rebate(
        taxable_income=threshold,
        tax_before_rebate=tax_before_rebate,
        regime=regime,
        is_resident=is_resident,
        financial_year=financial_year
    )
    return max(0.0, tax_before_rebate - rebate)


def calculate_income_tax(taxpayer) -> Dict[str, Any]:
    """
    Deterministic income tax calculation for salaried individuals.
    Returns complete breakdown with rule traceability.
    """
    financial_year = getattr(taxpayer, "financial_year", "2024-25")
    rules = get_tax_rules(financial_year)

    traceability: List[str] = []

    # Step 1: Calculate deductions
    deduction_result = calculate_deductions(taxpayer)
    traceability.append(
        f"Section 16(ia): Standard deduction of Rs. {deduction_result['standard_deduction']:,.0f} applied."
    )
    if taxpayer.regime == "old":
        if deduction_result["hra_exemption"] > 0:
            traceability.append(
                f"Section 10(13A) / Rule 2A: HRA exemption of Rs. {deduction_result['hra_exemption']:,.0f} deducted."
            )
        if deduction_result["section_80c"] > 0:
            traceability.append(
                f"Section 80C: Deduction of Rs. {deduction_result['section_80c']:,.0f} deducted (limit Rs. 1,50,000)."
            )
        if deduction_result["section_80ccd_1b"] > 0:
            traceability.append(
                f"Section 80CCD(1B): NPS deduction of Rs. {deduction_result['section_80ccd_1b']:,.0f} deducted (limit Rs. 50,000)."
            )
        if deduction_result["section_80d"] > 0:
            traceability.append(
                f"Section 80D: Health insurance deduction of Rs. {deduction_result['section_80d']:,.0f} deducted."
            )
        if deduction_result["home_loan_deduction"] > 0:
            traceability.append(
                f"Section 24(b): Self-occupied home loan interest deduction of Rs. {deduction_result['home_loan_deduction']:,.0f} deducted (limit Rs. 2,00,000)."
            )

    # Step 2: Statutory Rounding of taxable income under Section 288A
    raw_taxable = deduction_result["taxable_income"]
    taxable_income = round_to_nearest_10(raw_taxable)
    if taxable_income != raw_taxable:
        traceability.append(
            f"Section 288A: Taxable income rounded from Rs. {raw_taxable:,.2f} to Rs. {taxable_income:,}."
        )

    # Step 3: Select tax slabs
    slabs = rules.old_slabs if taxpayer.regime == "old" else rules.new_slabs

    # Step 4: Calculate slab tax before rebate
    tax_before_rebate = calculate_slab_tax(taxable_income, slabs)
    traceability.append(
        f"Chapter II / Section 115BAC slabs for FY {financial_year} applied: tax before rebate = Rs. {tax_before_rebate:,.2f}."
    )

    # Step 5: Section 87A rebate
    rebate = calculate_87a_rebate(
        taxable_income=taxable_income,
        tax_before_rebate=tax_before_rebate,
        regime=taxpayer.regime,
        is_resident=taxpayer.is_resident,
        financial_year=financial_year
    )
    if rebate > 0:
        traceability.append(
            f"Section 87A: Tax rebate of Rs. {rebate:,.2f} applied."
        )

    tax_after_rebate = max(0.0, tax_before_rebate - rebate)

    # Step 6: Surcharge and marginal relief
    surcharge_rate = calculate_surcharge_rate(taxable_income, taxpayer.regime)
    tax_after_surcharge = calculate_tax_with_surcharge(
        taxable_income=taxable_income,
        tax_after_rebate=tax_after_rebate,
        regime=taxpayer.regime,
        tax_at_threshold=lambda threshold: calculate_tax_after_rebate_at_threshold(
            threshold=threshold,
            regime=taxpayer.regime,
            is_resident=taxpayer.is_resident,
            financial_year=financial_year
        )
    )

    surcharge_amount = max(0.0, tax_after_surcharge - tax_after_rebate)
    nominal_surcharge = tax_after_rebate * surcharge_rate
    marginal_relief_surcharge = max(0.0, nominal_surcharge - surcharge_amount)

    if surcharge_amount > 0:
        traceability.append(
            f"Chapter II: Surcharge at {int(surcharge_rate * 100)}% applied: Rs. {surcharge_amount:,.2f}."
        )
    if marginal_relief_surcharge > 0:
        traceability.append(
            f"Marginal relief on surcharge of Rs. {marginal_relief_surcharge:,.2f} granted."
        )

    # Step 7: Health & Education Cess (4%)
    cess = calculate_cess(tax_after_surcharge)
    traceability.append(
        f"Finance Act: Health and Education Cess at 4% on (tax + surcharge) = Rs. {cess:,.2f}."
    )

    # Step 8 & 9: Final statutory rounding under Section 288B
    tax_before_final_rounding = tax_after_surcharge + cess
    final_tax = round_to_nearest_10(tax_before_final_rounding)
    traceability.append(
        f"Section 288B: Final tax liability rounded to nearest Rs. 10 = Rs. {final_tax:,}."
    )

    return {
        **deduction_result,
        "taxable_income": taxable_income,
        "tax_before_rebate": tax_before_rebate,
        "rebate_87a": rebate,
        "tax_after_rebate": tax_after_rebate,
        "surcharge_rate": surcharge_rate,
        "surcharge_amount": surcharge_amount,
        "marginal_relief_surcharge": marginal_relief_surcharge,
        "tax_after_surcharge": tax_after_surcharge,
        "cess": cess,
        "tax_before_final_rounding": tax_before_final_rounding,
        "final_tax": final_tax,
        "traceability": traceability,
    }


def compare_regimes(taxpayer_input) -> Dict[str, Any]:
    """
    Compare Old and New Tax Regimes for the taxpayer profile and recommend the optimal regime.
    """
    # Create copy for old regime
    taxpayer_dict = taxpayer_input.model_dump()
    old_input = taxpayer_input.__class__(**{**taxpayer_dict, "regime": "old"})
    new_input = taxpayer_input.__class__(**{**taxpayer_dict, "regime": "new"})

    old_result = calculate_income_tax(old_input)
    new_result = calculate_income_tax(new_input)

    old_tax = old_result["final_tax"]
    new_tax = new_result["final_tax"]
    diff = abs(old_tax - new_tax)

    if new_tax < old_tax:
        recommended = "new"
        reason = (
            f"New regime saves Rs. {diff:,.0f} in tax liability compared to Old regime "
            f"(Rs. {new_tax:,} vs Rs. {old_tax:,})."
        )
    elif old_tax < new_tax:
        recommended = "old"
        reason = (
            f"Old regime saves Rs. {diff:,.0f} in tax liability compared to New regime "
            f"(Rs. {old_tax:,} vs Rs. {new_tax:,}) due to higher itemized deductions (Rs. {old_result['total_deductions']:,})."
        )
    else:
        recommended = "either"
        reason = f"Both regimes result in the identical tax liability of Rs. {old_tax:,}."

    return {
        "financial_year": getattr(taxpayer_input, "financial_year", "2024-25"),
        "recommended_regime": recommended,
        "savings": diff,
        "reason": reason,
        "old_regime": old_result,
        "new_regime": new_result,
    }
