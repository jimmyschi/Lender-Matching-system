"""
Pydantic schemas for request/response validation and serialization.

Each domain object has a Base (shared fields), a Create (input), and a Read
(output with id and timestamps) variant. Nested reads are used where the UI
needs related data in one response (e.g., LenderRead includes programs and
their criteria so the policy page can render without extra round trips).
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class LenderCriterionBase(BaseModel):
    label: str
    field_name: str
    criterion_type: str
    threshold_value: Optional[float] = None
    allowed_values: Optional[list[str]] = None
    is_hard_reject: bool = True
    null_means_pass: bool = False
    weight: float = 1.0
    description: Optional[str] = None


class LenderCriterionCreate(LenderCriterionBase):
    pass


class LenderCriterionRead(LenderCriterionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    program_id: int
    created_at: datetime


class LenderProgramBase(BaseModel):
    name: str
    description: Optional[str] = None
    applicability_type: str = "general"
    priority: int = 10
    min_loan_amount: Optional[float] = None
    max_loan_amount: Optional[float] = None
    min_term_months: Optional[int] = None
    max_term_months: Optional[int] = None
    rate_description: Optional[str] = None


class LenderProgramCreate(LenderProgramBase):
    criteria: list[LenderCriterionCreate] = []


class LenderProgramRead(LenderProgramBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    lender_id: int
    created_at: datetime
    updated_at: datetime
    criteria: list[LenderCriterionRead] = []


class LenderBase(BaseModel):
    name: str
    description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None


class LenderCreate(LenderBase):
    programs: list[LenderProgramCreate] = []


class LenderRead(LenderBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
    programs: list[LenderProgramRead] = []


class LenderSummary(LenderBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class LoanApplicationBase(BaseModel):
    business_name: str
    business_state: str
    business_industry: str
    years_in_business: float
    annual_revenue: Optional[float] = None
    is_startup: bool = False

    guarantor_fico: int
    paynet_score: Optional[int] = None
    is_corp_only: bool = False

    has_bankruptcy: bool = False
    years_since_bankruptcy: Optional[float] = None
    has_judgments: bool = False
    has_foreclosures: bool = False
    has_repossessions: bool = False
    has_tax_liens: bool = False

    loan_amount: float
    loan_term_months: int

    equipment_type: str
    equipment_age_years: Optional[float] = None
    is_private_party_sale: bool = False

    is_us_citizen: bool = True
    is_homeowner: bool = False
    years_at_current_residence: Optional[float] = None
    has_cdl: bool = False
    num_trucks_operating: Optional[int] = None
    personal_revolving_debt: Optional[float] = None
    revolving_plus_unsecured_debt: Optional[float] = None


class LoanApplicationCreate(LoanApplicationBase):
    pass


class LoanApplicationRead(LoanApplicationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    created_at: datetime
    updated_at: datetime


class CriterionResultItem(BaseModel):
    criterion_id: int
    criterion_label: str
    passed: bool
    actual_value: str
    required_value: str
    explanation: str
    is_hard_reject: bool


class MatchResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    application_id: int
    lender_id: int
    program_id: Optional[int]
    is_eligible: bool
    fit_score: float
    matched_program_name: Optional[str]
    rejection_reasons: Optional[list[str]]
    criterion_results: Optional[list[dict]]
    created_at: datetime
    lender: LenderSummary


class UnderwritingResultsRead(BaseModel):
    application: LoanApplicationRead
    matches: list[MatchResultRead]
