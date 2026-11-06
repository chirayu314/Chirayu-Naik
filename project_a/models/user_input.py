from pydantic import BaseModel, Field, model_validator
from typing import Literal, Optional


class TaxpayerInput(BaseModel):
    # Basic information
    gross_salary: float = Field(ge=0, description="Annual gross salary income")
    regime: Literal["old", "new"] = Field(description="Tax regime: 'old' or 'new'")
    financial_year: Literal["2024-25", "2025-26"] = Field(
        default="2024-25", description="Financial Year for tax calculation"
    )
    is_resident: bool = Field(default=True, description="Whether taxpayer is resident in India")

    # Optional CTC representation for parsing disambiguation
    ctc: Optional[float] = Field(default=None, ge=0, description="Cost to Company (if specified)")

    # HRA information
    basic_salary: float = Field(default=0, ge=0)
    da: float = Field(default=0, ge=0)
    da_forms_part_of_retirement_benefits: bool = False
    hra_received: float = Field(default=0, ge=0)
    annual_rent: float = Field(default=0, ge=0)
    city_type: Literal["metro", "non_metro"] = "non_metro"

    # Deductions
    section_80c: float = Field(default=0, ge=0)
    section_80ccd_1b: float = Field(default=0, ge=0)

    # Section 80D
    self_family_medical: float = Field(default=0, ge=0)
    parents_medical: float = Field(default=0, ge=0)
    self_is_senior: bool = False
    parents_are_senior: bool = False

    # Home loan
    home_loan_interest: float = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_sanity(self) -> "TaxpayerInput":
        if self.basic_salary > self.gross_salary and self.gross_salary > 0:
            raise ValueError(
                f"Basic salary ({self.basic_salary}) cannot exceed gross salary ({self.gross_salary})"
            )
        return self
