"""
Versioned tax rules loader for Indian income tax rules across financial years.
FY 2024-25 (AY 2025-26) and FY 2025-26 (AY 2026-27).
"""

from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

from project_a.config.tax_rules_2024_25 import (
    OLD_REGIME_SLABS as OLD_SLABS_2024_25,
    NEW_REGIME_SLABS as NEW_SLABS_2024_25,
)
from project_a.config.tax_rules_2025_26 import (
    OLD_REGIME_SLABS as OLD_SLABS_2025_26,
    NEW_REGIME_SLABS as NEW_SLABS_2025_26,
    REBATE_87A_NEW_LIMIT as REBATE_NEW_LIMIT_2025_26,
    REBATE_87A_NEW_MAX as REBATE_NEW_MAX_2025_26,
)


@dataclass(frozen=True)
class TaxRulesConfig:
    financial_year: str
    assessment_year: str
    old_slabs: List[Tuple[float, float]]
    new_slabs: List[Tuple[float, float]]
    old_standard_deduction: float
    new_standard_deduction: float
    rebate_87a_old_limit: float
    rebate_87a_old_max: float
    rebate_87a_new_limit: float
    rebate_87a_new_max: float
    cess_rate: float = 0.04


RULES_REGISTRY: Dict[str, TaxRulesConfig] = {
    "2024-25": TaxRulesConfig(
        financial_year="2024-25",
        assessment_year="2025-26",
        old_slabs=OLD_SLABS_2024_25,
        new_slabs=NEW_SLABS_2024_25,
        old_standard_deduction=50000.0,
        new_standard_deduction=75000.0,
        rebate_87a_old_limit=500000.0,
        rebate_87a_old_max=12500.0,
        rebate_87a_new_limit=700000.0,
        rebate_87a_new_max=25000.0,
        cess_rate=0.04,
    ),
    "2025-26": TaxRulesConfig(
        financial_year="2025-26",
        assessment_year="2026-27",
        old_slabs=OLD_SLABS_2025_26,
        new_slabs=NEW_SLABS_2025_26,
        old_standard_deduction=50000.0,
        new_standard_deduction=75000.0,
        rebate_87a_old_limit=500000.0,
        rebate_87a_old_max=12500.0,
        rebate_87a_new_limit=REBATE_NEW_LIMIT_2025_26,
        rebate_87a_new_max=REBATE_NEW_MAX_2025_26,
        cess_rate=0.04,
    ),
}


def get_tax_rules(financial_year: str = "2024-25") -> TaxRulesConfig:
    """Retrieve versioned tax configuration by financial year."""
    clean_fy = financial_year.strip()
    if clean_fy not in RULES_REGISTRY:
        supported = ", ".join(RULES_REGISTRY.keys())
        raise ValueError(f"Unsupported financial year '{financial_year}'. Supported: {supported}")
    return RULES_REGISTRY[clean_fy]

