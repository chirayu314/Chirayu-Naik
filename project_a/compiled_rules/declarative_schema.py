"""
Declarative schema for LLM-compiled tax rules.
This provides a safe, restricted representation of statutory tax logic,
preventing any arbitrary code execution (no eval, no exec).
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class TaxSlab(BaseModel):
    upper_limit: float = Field(description="Upper limit of the slab in INR. Use -1 or null for infinity.")
    rate: float = Field(description="Tax rate as a decimal (e.g. 0.05 for 5%)")


class RebateRule(BaseModel):
    income_threshold: float
    max_rebate: float
    marginal_relief: bool = False
    marginal_relief_threshold: Optional[float] = None


class SurchargeBracket(BaseModel):
    threshold: float
    rate: float


class DeclarativeRegimeRules(BaseModel):
    regime: str
    standard_deduction: float
    allows_hra: bool = False
    allows_80c: bool = False
    allows_80ccd_1b: bool = False
    allows_80d: bool = False
    allows_home_loan: bool = False
    slabs: List[TaxSlab]
    rebate_87a: RebateRule
    surcharge_brackets: List[SurchargeBracket]


class DeclarativeTaxYearSpecification(BaseModel):
    financial_year: str
    assessment_year: str
    old_regime: DeclarativeRegimeRules
    new_regime: DeclarativeRegimeRules
    cess_rate: float = 0.04
    statutory_rounding_multiple: int = 10
    provenance: str = Field(
        default="AUDITED_PRE_COMPILED",
        description="Source of compilation: 'LLM_COMPILED_LIVE', 'AUDITED_PRE_COMPILED', or 'MANUAL'"
    )

