# AI Usage Note

## 1. AI Tools Utilized and Workflows
During the implementation of Project A (Income Tax Engine), AI tools were used for the following specific development tasks:
- **Code Inspection & Architecture Review**: Analyzing the initial repository structure (`project_a/`), identifying missing modules, and scaffolding the versioned configuration registry.
- **Statutory Source Research**: Cross-referencing Union Budget 2025 / Finance Act 2025 tax slabs (0-4L, 4-8L, 8-12L, etc.) and enhanced Section 87A rebate rules (up to ₹12L).
- **Test Generation**: Generating edge case parameter sets for slab thresholds, marginal relief bounds, and 55 natural language scenarios (English and Hinglish).
- **Declarative Schema Modeling**: Drafting the Pydantic schema for `DeclarativeTaxYearSpecification`.

---

## 2. Where the AI Was Wrong and How It Was Caught

### Incident 1: Regex Alternation Order in Indian Number Extraction
- **The AI Mistake**:
  When generating the token regex pattern for Indian numeric amounts, the AI proposed:
  ```python
  NUM_TOKEN_PATTERN = r"(?:(?:rs\.?|inr|₹)\s*)?(?:\d{1,3}(?:,\d{2,3})*(?:\.\d+)?|\d+(?:\.\d+)?(?:\s*(?:crores?|cr|lakhs?|lacs?|lk|l|k|thousands?|hazar))?)"
  ```
  Because Python's regular expression engine evaluates alternatives from left to right, the first branch `\d{1,3}(?:,\d{2,3})*(?:\.\d+)?` matched only the digits `"12"` in `"12 lakh"`. It prematurely consumed `"12"` and left `"lakh"` uncaptured in the string. As a result, `parse_indian_number("12")` returned `12.0` instead of `1,200,000.0`.
- **How It Was Caught**:
  When running `pytest project_a/tests/test_natural_language.py`, 22 test cases immediately failed with assertions such as:
  ```text
  AssertionError: assert 12.0 == 1200000.0
  AssertionError: assert 15.0 == 1500000.0
  ```
- **The Fix**:
  The alternation order was corrected to prioritize the unit-bearing pattern before standalone numbers:
  ```python
  NUM_TOKEN_PATTERN = r"(?:(?:rs\.?|inr|₹)\s*)?(?:\d+(?:\.\d+)?\s*(?:crores?|cr|lakhs?|lacs?|lac|lk|l|k|thousands?|hazar)\b|\d{1,3}(?:,\d{2,3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
  ```
  After this change, all 55 natural-language tests passed immediately.

### Incident 2: Miscalculated FY 2025-26 Slab Tax for ₹15 Lakh
- **The AI Mistake**:
  When writing the parameterized test `test_direct_law_change_comparison`, the AI drafted an expected tax of `44,200` for a gross salary of ₹15,00,000 under FY 2025-26 New Regime.
- **How It Was Caught**:
  The deterministic engine computed `97,500`. Reviewing the statutory math confirmed the engine was correct and the AI test expectation was wrong:
  - Gross Salary: ₹15,00,000
  - Standard Deduction (Sec 16(ia)): ₹75,000 → Taxable Income = ₹14,25,000
  - Slabs (Finance Act 2025):
    - 0 – 4L: Nil
    - 4L – 8L (4L @ 5%): ₹20,000
    - 8L – 12L (4L @ 10%): ₹40,000
    - 12L – 14.25L (2.25L @ 15%): ₹33,750
    - Total Slab Tax = ₹93,750
    - 4% Health & Education Cess = ₹3,750
    - Final Tax Liability = ₹97,500
- **The Fix**:
  The test was updated with the verified statutory number, and all 236 unit tests passed.

---

## 3. Human Engineering Oversight & Verification
Every equation, statutory reference, and test expectation was verified against:
- Income-tax Act, 1961 (Sections 10(13A), 16(ia), 24(b), 80C, 80CCD(1B), 80D, 87A, 115BAC, 288A, 288B).
- Finance (No. 2) Act, 2024.
- Finance Act, 2025 / Union Budget 2025.
- Income Tax Department official tax calculator schedules.

