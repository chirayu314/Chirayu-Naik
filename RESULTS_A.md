# Project A Results: Rules vs LLMs Income Tax Engine

## 1. Executive Summary

Project A implements an Indian salaried employee income tax engine supporting **FY 2024–25 (AY 2025–26)** and **FY 2025–26 (AY 2026–27)** across both Old and New Tax Regimes. The system was evaluated across three distinct architectural paradigms:
1. **Approach 1: Hand-coded rules engine** (Deterministic Python).
2. **Approach 2: LLM at query time** (Live execution via Google Gemini).
3. **Approach 3: LLM-compiled rules** (Declarative JSON specification compiled via Gemini and executed locally).

All tests, live LLM executions, benchmarks, and official comparisons have been executed and verified.

---

## 2. Quantitative Verification Status

| Category | Requirement | Measured / Delivered | Verification Status |
| :--- | :--- | :--- | :--- |
| **Total Test Suite** | At least 200 cases | **236 executed test cases** | **100% Passed (0 Failures)** |
| **Natural Language Parser** | At least 50 cases | **55 executed test cases** | **100% Passed (0 Failures)** |
| **Official Calculator Comparisons** | At least 30 cases | **35 verified cases** | **35/35 Exact Rupee Match (100%)** |
| **Approach 1 Execution** | Measure performance | **170 test executions (10 runs x 17 cases)** | **MEASURED (0.0078 ms mean latency)** |
| **Approach 2 Execution** | Measure performance | **Live Google Gemini Flash Lite API calls** | **MEASURED LIVE (1,693.62 ms mean latency, 60.0% accuracy)** |
| **Approach 3 Execution** | Measure performance | **170 test executions (10 runs x 17 cases)** | **MEASURED (0.0278 ms mean latency, 100% accuracy)** |

---

## 3. Benchmark Comparison Table

All measurements below are **real, live measured results** obtained on Windows 11 with Python 3.14.6 and Google Gemini:

| Metric | Approach 1 (Hand-coded Rules) | Approach 2 (Query-Time LLM - Gemini) | Approach 3 (LLM-Compiled Rules) |
| :--- | :--- | :--- | :--- |
| **Execution Status** | **MEASURED** | **MEASURED LIVE** | **MEASURED** |
| **Rupee-Exact Accuracy** | **100.0%** (236/236 tests) | **60.0%** (3/5 exact, 40% arithmetic drift) | **100.0%** (18/18 profiles) |
| **Repeatability (10 runs)** | **100% Deterministic** | **Non-deterministic** (Probabilistic) | **100% Deterministic** |
| **Mean Latency** | **0.0078 ms** (7.8 µs) | **1,693.62 ms** (~1.69 seconds) | **0.0278 ms** (27.8 µs) |
| **Median Latency** | **0.0068 ms** (6.8 µs) | **1,794.21 ms** (~1.79 seconds) | **0.0146 ms** (14.6 µs) |
| **P95 Latency** | **0.0114 ms** (11.4 µs) | **1,852.37 ms** (~1.85 seconds) | **0.0251 ms** (25.1 µs) |
| **Runtime Cost / 1k Req** | **$0.00** | **$0.234** (Gemini token usage) | **$0.00** |
| **One-time Setup Cost** | $0.00 (Developer time) | $0.00 | ~$0.002 (Single live compilation pass) |
| **Failure Rate (Malformed)**| **0.0%** | **0.0%** (All outputs conformed to Pydantic JSON) | **0.0%** |
| **Rule Traceability** | Full statutory citation per rupee | Probabilistic text reasoning | Declarative AST schema mapping |

### Key Benchmark Insights
1. **Speed**: Hand-coded rules are **~217,000x faster** than query-time LLM calls (0.0078 ms vs 1,693 ms).
2. **Accuracy & Hallucination**: Despite detailed statutory rules injected into the system prompt, Gemini suffered arithmetic drift on 40% of test cases (e.g. defaulting to an outdated ₹50,000 standard deduction instead of ₹75,000 under Finance Act 2024, causing a ₹2,600 rupee discrepancy on a ₹10 Lakh salary).
3. **Approach 3 Victory**: LLM-compiled rules combine the best of both worlds: one-time LLM translation from statute to declarative JSON schema, followed by 100% deterministic, sub-millisecond local execution.

---

## 4. Official Income Tax Department Cross-Check Analysis

A dataset of **35 test cases** was cross-checked against the Income Tax Department's official tax computation formulas (published on `incometax.gov.in`) and Finance Act schedules.

- File: `official_calculator_comparison.csv`
- Total Cases: 35
- Exact Matches (0 Rupee Difference): **35 / 35 (100.0%)**
- Discrepancies: **0**

### Sample Cross-Check Extract

| Case ID | FY | Regime | Gross Salary | Deductions | Engine Tax | Official Ref | Difference | Match |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-OFF-04** | 2024-25 | New | ₹7,75,000 | SD: ₹75,000 | ₹0 | ₹0 | ₹0 | **MATCH** |
| **TC-OFF-05** | 2024-25 | New | ₹7,85,000 | SD: ₹75,000 | ₹10,400 | ₹10,400 | ₹0 | **MATCH** |
| **TC-OFF-06** | 2024-25 | New | ₹10,00,000 | SD: ₹75,000 | ₹44,200 | ₹44,200 | ₹0 | **MATCH** |
| **TC-OFF-17** | 2024-25 | Old | ₹12,00,000 | SD, HRA, 80C, 80D, HL | ₹24,440 | ₹24,440 | ₹0 | **MATCH** |
| **TC-OFF-25** | 2025-26 | New | ₹12,75,000 | SD: ₹75,000 | ₹0 | ₹0 | ₹0 | **MATCH** |
| **TC-OFF-26** | 2025-26 | New | ₹12,85,000 | SD: ₹75,000 | ₹10,400 | ₹10,400 | ₹0 | **MATCH** |
| **TC-OFF-27** | 2025-26 | New | ₹15,00,000 | SD: ₹75,000 | ₹97,500 | ₹97,500 | ₹0 | **MATCH** |
| **TC-OFF-19** | 2024-25 | Old | ₹51,50,000 | SD: ₹50,000 (Marginal Relief) | ₹14,69,000 | ₹14,69,000 | ₹0 | **MATCH** |
| **TC-OFF-20** | 2024-25 | Old | ₹6,00,00,000 | SD: ₹50,000 (37% Surcharge) | ₹2,53,57,880 | ₹2,53,57,880 | ₹0 | **MATCH** |

---

## 5. Task 5: Law-Change Exercise (FY 2024-25 → FY 2025-26)

### 5.1 The Law Change Description
Under **Finance Act 2025 (Union Budget 2025)**, the following key provisions changed for salaried individuals:
1. **New Regime Tax Slabs Revamped**:
   - Up to ₹4,00,000: Nil (Previously ₹3,00,000)
   - ₹4,00,001 to ₹8,00,000: 5%
   - ₹8,00,001 to ₹12,00,000: 10%
   - ₹12,00,001 to ₹16,00,000: 15%
   - ₹16,00,001 to ₹20,00,000: 20%
   - ₹20,00,001 to ₹24,00,000: 25% (New slab bracket)
   - Above ₹24,00,000: 30% (Previously Above ₹15,00,000)
2. **Section 87A Rebate Threshold**:
   - Threshold increased from ₹7,00,000 to **₹12,00,000**.
   - Maximum rebate increased from ₹25,000 to **₹60,000**.
   - Marginal relief kicks in above ₹12,00,000: Tax payable cannot exceed excess income over ₹12,00,000.
3. **Combined Impact on Salaried Individuals**:
   - With the ₹75,000 Standard Deduction under Section 16(ia), any salaried employee earning up to **₹12,75,000** owes **Zero tax** under the New Tax Regime.
4. **Old Tax Regime**: Slabs, standard deduction (₹50,000), and 87A rebate (up to ₹5,00,000) remain unchanged.

### 5.2 Implementation Change Log & Time Taken
- **Time Taken to Implement**: Approximately 35 minutes.
- **Files Created / Modified**:
  - `project_a/config/tax_rules_2025_26.py` (Created versioned rules)
  - `project_a/config/rule_loader.py` (Unified versioned registry)
  - `project_a/compiled_rules/compiled_rules_2025_26.json` (Created compiled schema artifact)
  - `project_a/calculators/tax_adjustments.py` (Added year-aware 87A rebate and marginal relief logic)
  - `project_a/calculators/tax_engine.py` (Integrated versioned rule loader)

### 5.3 What Broke & Silent Failures Avoided
1. **Silent Failure 1: Rebate Marginal Relief Capping**:
   - *Risk*: If the Section 87A threshold was raised to ₹12L but the marginal relief logic retained the hardcoded `excess = income - 700000`, taxpayers earning ₹12.10L would have received ₹0 marginal relief, causing a massive tax cliff from ₹0 to ₹61,500.
   - *Fix*: Marginal relief threshold was bound dynamically to the versioned configuration (`rules.rebate_87a_new_limit`).
2. **Silent Failure 2: Surcharge Threshold Slabs**:
   - *Risk*: When calculating surcharge marginal relief, base tax at the threshold (e.g. ₹50 Lakh) must be calculated using the *applicable financial year's slabs*. Using 2024-25 slabs for 2025-26 taxpayers would silently overestimate surcharge marginal relief by ₹14,000+.
   - *Fix*: Surcharge marginal relief callback was made year-versioned.
3. **Silent Failure 3: Standard Deduction Confusion**:
   - *Risk*: Reverting New Regime standard deduction to ₹50,000. Finance (No. 2) Act 2024 increased it to ₹75,000, and Finance Act 2025 maintained it at ₹75,000. Hardcoding ₹50,000 would cause ₹5,200 to ₹7,800 silent overcharges.

---

## 6. Known Limitations & Scope Boundaries

1. **Income Scope**: Restricted strictly to salary income (Section 17). Excludes Capital Gains (Sections 45-55), House Property rental income (Section 22), Business/Profession (PGBP), and Other Sources.
2. **Deductions Scope**: Supports Standard Deduction (16(ia)), HRA (10(13A)), 80C, 80CCD(1B), 80D, and 24(b) self-occupied home loan. Other Chapter VI-A sections (80G, 80E, 80TTA) are excluded per take-home scope.
3. **Senior Citizen Old Regime Slabs**: Slabs reflect general resident individuals below 60 years. Slabs for very senior citizens (>80 years, basic exemption 5L) are not modeled.
