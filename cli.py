"""
Interactive Command-Line Demonstration Interface for Fire AI Project A (Income Tax Engine).
Supports:
1. Natural-language input parsing and clarification prompts.
2. Structured taxpayer input calculation.
3. Old vs New regime comparison with tax savings recommendation.
4. FY 2024-25 vs FY 2025-26 law-change demonstration.
5. All three engine approaches (Deterministic, Query-Time LLM, Compiled Rules).
"""

import sys
import argparse
from typing import Optional

from project_a.models.user_input import TaxpayerInput
from project_a.parsers.input_parser import parse_natural_language_input
from project_a.calculators.tax_engine import calculate_income_tax, compare_regimes
from project_a.llm.query_time_engine import LLMQueryTimeEngine
from project_a.llm.compiled_rules_engine import CompiledRulesTaxEngine


def print_banner():
    print("=" * 75)
    print("   FIRE AI - PROJECT A: SALARIED INCOME TAX ENGINE (RULES VS LLMS)   ")
    print("=" * 75)


def display_tax_result(result: dict):
    print("\n" + "-" * 60)
    print(f"TAX CALCULATION BREAKDOWN (FY {result.get('financial_year', '2024-25')})")
    print("-" * 60)
    print(f"  Regime                        : {result['regime'].upper()}")
    print(f"  Gross Salary                  : Rs. {result['gross_salary']:,.2f}")
    print(f"  Standard Deduction (Sec 16(ia)): Rs. {result['standard_deduction']:,.2f}")

    if result["regime"] == "old":
        print(f"  HRA Exemption (Sec 10(13A))   : Rs. {result['hra_exemption']:,.2f}")
        print(f"  Section 80C Deduction         : Rs. {result['section_80c']:,.2f}")
        print(f"  Section 80CCD(1B) NPS         : Rs. {result['section_80ccd_1b']:,.2f}")
        print(f"  Section 80D Health Insurance  : Rs. {result['section_80d']:,.2f}")
        print(f"  Section 24(b) Home Loan Int.  : Rs. {result['home_loan_deduction']:,.2f}")

    print(f"  Total Deductions              : Rs. {result['total_deductions']:,.2f}")
    print(f"  Taxable Income (Sec 288A)     : Rs. {result['taxable_income']:,.2f}")
    print(f"  Slab Tax (Before Rebate)      : Rs. {result['tax_before_rebate']:,.2f}")
    print(f"  Section 87A Rebate            : Rs. {result['rebate_87a']:,.2f}")
    print(f"  Tax After Rebate              : Rs. {result['tax_after_rebate']:,.2f}")

    if result.get("surcharge_amount", 0) > 0:
        print(f"  Surcharge ({int(result['surcharge_rate']*100)}%)               : Rs. {result['surcharge_amount']:,.2f}")
        if result.get("marginal_relief_surcharge", 0) > 0:
            print(f"  Surcharge Marginal Relief     : Rs. {result['marginal_relief_surcharge']:,.2f}")

    print(f"  Health & Education Cess (4%)  : Rs. {result['cess']:,.2f}")
    print("-" * 60)
    print(f"  >>> FINAL TAX PAYABLE (Sec 288B): Rs. {result['final_tax']:,} <<<")
    print("-" * 60)

    if result.get("traceability"):
        print("\nSTATUTORY AUDIT TRAIL:")
        for step in result["traceability"]:
            print(f"  [✓] {step}")


def display_comparison(comp: dict):
    print("\n" + "=" * 60)
    print(f"REGIME COMPARISON SUMMARY ({comp['financial_year']})")
    print("=" * 60)
    old = comp["old_regime"]
    new = comp["new_regime"]
    print(f"  Old Regime Final Tax : Rs. {old['final_tax']:,}")
    print(f"  New Regime Final Tax : Rs. {new['final_tax']:,}")
    print(f"  Recommended Regime   : {comp['recommended_regime'].upper()}")
    print(f"  Net Savings          : Rs. {comp['savings']:,}")
    print(f"  Reason               : {comp['reason']}")
    print("=" * 60)


def run_nl_mode(query: str):
    print(f"\nProcessing Natural Language Input:\n\"{query}\"\n")
    parse_res = parse_natural_language_input(query)

    if parse_res.status == "clarification_needed":
        print("[!] Clarification Needed before calculation can proceed:")
        for idx, q in enumerate(parse_res.clarification_questions, 1):
            print(f"   {idx}. {q}")
        if parse_res.detected_entities:
            print(f"\nDetected Entities so far: {parse_res.detected_entities}")
        return

    if parse_res.status == "contradiction_detected":
        print("[X] Contradiction or Ambiguity Detected:")
        for idx, q in enumerate(parse_res.clarification_questions, 1):
            print(f"   {idx}. {q}")
        return

    if parse_res.status == "error":
        print("[X] Parsing Error:")
        for idx, q in enumerate(parse_res.clarification_questions, 1):
            print(f"   {idx}. {q}")
        return

    print("[✓] Successfully parsed input into structured TaxpayerInput profile.")
    tp = parse_res.taxpayer_input

    # Execute deterministic calculation
    res = calculate_income_tax(tp)
    display_tax_result(res)

    # Also show regime comparison
    comp = compare_regimes(tp)
    display_comparison(comp)


def run_interactive():
    print_banner()
    print("Select an option:")
    print("  1. Enter Natural Language Description (English / Hinglish)")
    print("  2. Quick Sample: 12L Mumbai Renter (FY 2024-25)")
    print("  3. Quick Sample: FY 2024-25 vs FY 2025-26 Law Change on 12.75L")
    print("  4. Run Approach 3 (Compiled Rules Engine)")
    print("  5. Exit")

    choice = input("\nEnter choice [1-5]: ").strip()

    if choice == "1":
        query = input("\nEnter your tax description:\n> ").strip()
        if query:
            run_nl_mode(query)
    elif choice == "2":
        sample = "My salary is 12 lakh, I live in Mumbai, pay 25k rent monthly, and invested 1.5 lakh in PPF. Old regime, FY 2024-25."
        run_nl_mode(sample)
    elif choice == "3":
        print("\n--- DEMONSTRATING LAW CHANGE (FY 2024-25 vs FY 2025-26) on Rs. 12,75,000 New Regime ---")
        tp_24 = TaxpayerInput(gross_salary=1275000, regime="new", financial_year="2024-25")
        tp_25 = TaxpayerInput(gross_salary=1275000, regime="new", financial_year="2025-26")
        res_24 = calculate_income_tax(tp_24)
        res_25 = calculate_income_tax(tp_25)
        print(f"FY 2024-25 Tax Liability: Rs. {res_24['final_tax']:,}")
        print(f"FY 2025-26 Tax Liability: Rs. {res_25['final_tax']:,} (Zero tax due to Budget 2025 enhanced Rs. 12L rebate!)")
        print(f"Tax Saved under FY 2025-26: Rs. {res_24['final_tax'] - res_25['final_tax']:,}")
    elif choice == "4":
        sample_tp = TaxpayerInput(gross_salary=1200000, regime="new", financial_year="2024-25")
        engine = CompiledRulesTaxEngine()
        res = engine.calculate(sample_tp)
        print(f"\nCompiled Rules Engine Output: Final Tax = Rs. {res['final_tax']:,} (Provenance: {res['provenance']})")
    else:
        print("Exiting.")


def main():
    parser = argparse.ArgumentParser(description="Fire AI Project A - Salaried Income Tax Engine")
    parser.add_argument("--query", "-q", type=str, help="Natural language query description")
    parser.add_argument("--compare", "-c", action="store_true", help="Compare old and new regime for query")
    parser.add_argument("--benchmark", "-b", action="store_true", help="Run benchmark suite")
    parser.add_argument("--crosscheck", action="store_true", help="Run official calculator cross-checks")

    args = parser.parse_args()

    if args.benchmark:
        from project_a.benchmarks.benchmark_runner import run_benchmark
        run_benchmark()
    elif args.crosscheck:
        from project_a.benchmarks.generate_official_crosscheck import run_crosscheck
        run_crosscheck()
    elif args.query:
        run_nl_mode(args.query)
    else:
        run_interactive()


if __name__ == "__main__":
    main()

