# FY 2025-26 (AY 2026-27)
# Source: Finance Act 2025 / Union Budget 2025 provisions

# Old tax regime: Individual below 60 years (unchanged)
OLD_REGIME_SLABS = [
    (250000, 0.00),
    (500000, 0.05),
    (1000000, 0.20),
    (float("inf"), 0.30)
]

# New tax regime: Revised under Finance Act 2025
NEW_REGIME_SLABS = [
    (400000, 0.00),
    (800000, 0.05),
    (1200000, 0.10),
    (1600000, 0.15),
    (2000000, 0.20),
    (2400000, 0.25),
    (float("inf"), 0.30)
]

OLD_STANDARD_DEDUCTION = 50000
NEW_STANDARD_DEDUCTION = 75000

# Section 87A rebate parameters
REBATE_87A_OLD_LIMIT = 500000
REBATE_87A_OLD_MAX = 12500

REBATE_87A_NEW_LIMIT = 1200000
REBATE_87A_NEW_MAX = 60000

