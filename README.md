# Fire AI Take-Home Assignment: Project A (Income Tax Engine)

> **Mission**: Build an Indian salaried income-tax engine supporting FY 2024–25 (AY 2025–26) and FY 2025–26 (AY 2026–27) under both Old and New regimes, evaluate three architectural paradigms (Rules vs LLMs), handle natural-language input, and provide reproducible benchmarks with complete legal traceability.

---

## 1. Project Architecture

The engine is structured as a clean, modular Python application:

```text
fireai_income_tax_engine/
├── project_a/
│   ├── config/
│   │   ├── legal_sources.json            # Official Income Tax Act & Finance Act references
│   │   ├── tax_rules_2024_25.py          # FY 2024-25 slabs & parameters
│   │   ├── tax_rules_2025_26.py          # FY 2025-26 slabs & parameters (Finance Act 2025)
│   │   └── rule_loader.py                # Versioned tax rules registry
│   ├── models/
│   │   └── user_input.py                 # Pydantic TaxpayerInput schema with cross-field validators
│   ├── calculators/
│   │   ├── slab_calculator.py            # Generic deterministic slab-rate calculator
│   │   ├── deductions.py                 # Standard deduction, HRA, 80C, 80CCD, 80D, 24(b)
│   │   ├── deduction_engine.py           # Itemized vs Standard deduction routing
│   │   ├── tax_adjustments.py            # Section 87A rebate, surcharge, marginal relief, cess
│   │   └── tax_engine.py                 # Core engine with Section 288A/B rounding & audit trail
│   ├── parsers/
│   │   └── input_parser.py               # Deterministic NLP parser (Indian numerals, Hinglish, clarifications)
│   ├── llm/
│   │   ├── llm_client.py                 # Lightweight OpenAI/Gemini client with cost & token tracking
│   │   ├── query_time_engine.py          # Approach 2: LLM at query time with Pydantic validation
│   │   └── compiled_rules_engine.py      # Approach 3: LLM rule compiler + declarative execution
│   ├── compiled_rules/
│   │   ├── declarative_schema.py         # Safe declarative AST schema (no eval/exec)
│   │   ├── declarative_executor.py       # Deterministic virtual machine for compiled rules
│   │   ├── compiled_rules_2024_25.json   # Pre-compiled, audited FY 2024-25 rules
│   │   └── compiled_rules_2025_26.json   # Pre-compiled, audited FY 2025-26 rules
│   ├── benchmarks/
│   │   ├── benchmark_runner.py           # 10-run repeatability, latency, cost, failure measurement
│   │   └── generate_official_crosscheck.py # 35-case crosscheck against official ITD calculator
│   └── tests/
│       ├── test_deductions.py            # Deductions unit tests
│       ├── test_deduction_engine.py      # Deduction aggregation tests
│       ├── test_tax.py                   # Slab rate calculation tests
│       ├── test_tax_adjustments.py       # Surcharge & rebate tests
│       ├── test_tax_engine.py            # Core engine integration tests
│       ├── test_user_input.py            # Pydantic validation tests
│       ├── test_natural_language.py      # 55 natural language tests (English, Hinglish, edge cases)
│       └── test_suite_comprehensive.py   # Full 200+ case exhaustive boundary test suite
├── app.py                                # Streamlit Web UI
├── cli.py                                # Interactive Command-Line Interface
├── official_calculator_comparison.csv    # 35 verified comparison cases against official ITD calculator
├── benchmark_results.json                # Machine-readable benchmark outputs
├── RESULTS_A.md                          # Benchmark tables, verification status, and law-change analysis
├── DESIGN_A.md                           # System architecture defense for 100,000 users
├── DECISION_MATRIX.md                    # Component-by-component rule vs LLM decision matrix
├── AI_USAGE.md                           # AI assistance disclosure and verification log
├── requirements.txt                      # Project dependencies
├── .env.example                          # Environment template
└── .gitignore                            # Secret and artifact exclusion rules
```

---

## 2. Windows PowerShell Setup & Quickstart

### Prerequisites
- Windows 10/11
- Python 3.10+ (Tested on Python 3.14.6)
- PowerShell 5.1 or PowerShell Core 7+

### Step 1: Clone or Navigate to Project
```powershell
cd c:\Users\chira\OneDrive\Desktop\fireai_income_tax_engine
```

### Step 2: Activate Virtual Environment
```powershell
# If using existing venv:
.\venv\Scripts\Activate.ps1

# Or create a fresh virtual environment:
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 3. Single Reproducible Verification Commands

### Run Full Test Suite (236 Tests Passing)
```powershell
python -m pytest
```
*Output: `236 passed in ~0.5 seconds`.*

### Run Benchmark Suite
```powershell
python -m project_a.benchmarks.benchmark_runner
```
*Measures latency (mean/median/p95), repeatability over 10 runs, cost per 1,000 requests, and saves `benchmark_results.json`.*

### Run Official Calculator Cross-Checks (35 Cases Verified)
```powershell
python -m project_a.benchmarks.generate_official_crosscheck
```
*Generates and verifies `official_calculator_comparison.csv` with 100% agreement.*

---

## 4. Interfaces & Demonstrations

### Interactive CLI Tool
```powershell
# Interactive menu:
python cli.py

# Direct natural language query:
python cli.py --query "My salary is 12 lakh, I live in Mumbai, pay 25k rent monthly, and invested 1.5 lakh in PPF. Old regime, FY 2024-25."

# Hinglish query:
python cli.py --query "Meri salary 10 lakh hai aur rent 20k per month hai, old regime, 2024-25."

# Incomplete query (triggers clarification questions):
python cli.py --query "Salary 15 lakh."
```

### Streamlit Web App
```powershell
streamlit run app.py
```
*(If Streamlit is not yet installed in your environment, run `pip install streamlit` or use `python cli.py`).*

---

## 5. Scope & Statutory Tax Coverage

| Statutory Head | Section | Rules Applied |
| :--- | :--- | :--- |
| **Standard Deduction** | Section 16(ia) | Old: ₹50,000. New (FY 2024-25 & 2025-26): ₹75,000. |
| **HRA Exemption** | Section 10(13A) / Rule 2A | Least of: (1) Actual HRA, (2) Rent - 10% salary, (3) 50% (metro) or 40% (non-metro) salary. |
| **Section 80C** | Section 80C | Capped at ₹1,50,000 (PPF, EPF, ELSS, Life Insurance). Old regime only. |
| **Section 80CCD(1B)** | Section 80CCD(1B) | Additional NPS deduction capped at ₹50,000. Old regime only. |
| **Section 80D** | Section 80D | Self/Family: ₹25k (₹50k if senior). Parents: ₹25k (₹50k if senior). Max ₹1,00,000. |
| **Self-Occupied Home Loan** | Section 24(b) | Interest capped at ₹2,00,000. Old regime only. |
| **Section 87A Rebate** | Section 87A | **FY 2024-25**: Old: <= ₹5L (max ₹12.5k). New: <= ₹7L (max ₹25k) with marginal relief.<br>**FY 2025-26**: New: <= ₹12L (max ₹60k) with marginal relief. |
| **Surcharge & Relief** | Chapter II | 10% (>50L), 15% (>1Cr), 25% (>2Cr), 37% (>5Cr Old only). New regime capped at 25%. Marginal relief enforced at all thresholds. |
| **Health & Education Cess**| Finance Act | 4% on (Tax + Surcharge). |
| **Statutory Rounding** | Section 288A & 288B | Round total income and final tax liability to nearest multiple of ₹10. |

---

## 6. Deliverables Reference

- `RESULTS_A.md`: Detailed benchmark results, official cross-check table, and law-change analysis.
- `DESIGN_A.md`: 2-page system architecture defense and scaling analysis for 100,000 users.
- `DECISION_MATRIX.md`: Component-by-component evaluation matrix (Rules vs LLMs).
- `AI_USAGE.md`: Full transparency on AI assistance and verification catches.
- `official_calculator_comparison.csv`: 35 reproducible official comparisons.
- `benchmark_results.json`: Machine-readable performance metrics.

