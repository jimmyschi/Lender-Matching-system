"""
Every lending rule is a database row, not a line of code. That design is what
makes the whole system extensible without redeployment.

After underwriting runs, each lender gets a MatchResult row. The criterion_results
column stores a JSON snapshot of every individual pass and fail — that's how the
UI can render the per-criterion table instantly on reload without re-running the engine.
pass/fail without re-running the engine.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, JSON,
    String, Text, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Lender(Base):
    __tablename__ = "lenders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    contact_email: Mapped[Optional[str]] = mapped_column(String(200))
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    programs: Mapped[list["LenderProgram"]] = relationship(
        "LenderProgram", back_populates="lender", cascade="all, delete-orphan"
    )


class LenderProgram(Base):
    """
    A credit program offered by a lender (e.g., 'Standard Tier 1', 'A+ Rate').

    applicability_type controls which applications are eligible to be evaluated
    against this program:
      general       - all applications
      with_paynet   - only when a PayNet score is provided
      without_paynet - only when no PayNet score is provided
      corp_only     - only when the application has no personal guarantor
      medical       - only when business_industry is a medical category
      trucking      - only when the equipment or industry is trucking

    priority determines the order programs are attempted within a lender.
    Lower numbers are tried first (best tier). The engine stops at the first
    program where all hard-reject criteria pass.
    """
    __tablename__ = "lender_programs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    lender_id: Mapped[int] = mapped_column(Integer, ForeignKey("lenders.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    applicability_type: Mapped[str] = mapped_column(String(50), default="general")
    priority: Mapped[int] = mapped_column(Integer, default=10)
    min_loan_amount: Mapped[Optional[float]] = mapped_column(Float)
    max_loan_amount: Mapped[Optional[float]] = mapped_column(Float)
    min_term_months: Mapped[Optional[int]] = mapped_column(Integer)
    max_term_months: Mapped[Optional[int]] = mapped_column(Integer)
    rate_description: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    lender: Mapped["Lender"] = relationship("Lender", back_populates="programs")
    criteria: Mapped[list["LenderCriterion"]] = relationship(
        "LenderCriterion", back_populates="program", cascade="all, delete-orphan"
    )


class LenderCriterion(Base):
    """
    A single evaluable rule within a program.

    field_name maps to a key in the application dict built by app_to_dict().
    criterion_type determines the evaluation logic:
      min_value       - field >= threshold_value
      max_value       - field <= threshold_value
      required_true   - field must be truthy
      required_false  - field must be falsy
      excluded_values - field must not appear in allowed_values list
      allowed_values  - field must appear in allowed_values list

    null_means_pass: when True, a null field value counts as passing this
    criterion. Used for fields like years_since_bankruptcy (null = no BK = pass)
    and equipment_age_years (null = unknown age = acceptable).

    weight affects the fit score calculation for eligible applications. Higher
    weight means this criterion has more influence on the 0-100 score.
    is_hard_reject=True means a failed criterion immediately disqualifies the
    application from this program.
    """
    __tablename__ = "lender_criteria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    program_id: Mapped[int] = mapped_column(Integer, ForeignKey("lender_programs.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    criterion_type: Mapped[str] = mapped_column(String(50), nullable=False)
    threshold_value: Mapped[Optional[float]] = mapped_column(Float)
    allowed_values: Mapped[Optional[list]] = mapped_column(JSON)
    is_hard_reject: Mapped[bool] = mapped_column(Boolean, default=True)
    null_means_pass: Mapped[bool] = mapped_column(Boolean, default=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    program: Mapped["LenderProgram"] = relationship("LenderProgram", back_populates="criteria")


class LoanApplication(Base):
    """
    A complete loan application submitted for underwriting.

    status lifecycle: draft -> submitted -> underwriting -> completed.
    Fields with Optional types are nullable because not every application
    involves trucking, bankruptcy history, etc. The matching engine handles
    nulls per criterion via null_means_pass.
    """
    __tablename__ = "loan_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="submitted")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    business_name: Mapped[str] = mapped_column(String(200), nullable=False)
    business_state: Mapped[str] = mapped_column(String(2), nullable=False)
    business_industry: Mapped[str] = mapped_column(String(100), nullable=False)
    years_in_business: Mapped[float] = mapped_column(Float, nullable=False)
    annual_revenue: Mapped[Optional[float]] = mapped_column(Float)
    is_startup: Mapped[bool] = mapped_column(Boolean, default=False)

    guarantor_fico: Mapped[int] = mapped_column(Integer, nullable=False)
    paynet_score: Mapped[Optional[int]] = mapped_column(Integer)
    is_corp_only: Mapped[bool] = mapped_column(Boolean, default=False)

    has_bankruptcy: Mapped[bool] = mapped_column(Boolean, default=False)
    years_since_bankruptcy: Mapped[Optional[float]] = mapped_column(Float)
    has_judgments: Mapped[bool] = mapped_column(Boolean, default=False)
    has_foreclosures: Mapped[bool] = mapped_column(Boolean, default=False)
    has_repossessions: Mapped[bool] = mapped_column(Boolean, default=False)
    has_tax_liens: Mapped[bool] = mapped_column(Boolean, default=False)

    loan_amount: Mapped[float] = mapped_column(Float, nullable=False)
    loan_term_months: Mapped[int] = mapped_column(Integer, nullable=False)

    equipment_type: Mapped[str] = mapped_column(String(100), nullable=False)
    equipment_age_years: Mapped[Optional[float]] = mapped_column(Float)
    is_private_party_sale: Mapped[bool] = mapped_column(Boolean, default=False)

    is_us_citizen: Mapped[bool] = mapped_column(Boolean, default=True)
    is_homeowner: Mapped[bool] = mapped_column(Boolean, default=False)
    years_at_current_residence: Mapped[Optional[float]] = mapped_column(Float)
    has_cdl: Mapped[bool] = mapped_column(Boolean, default=False)
    num_trucks_operating: Mapped[Optional[int]] = mapped_column(Integer)
    personal_revolving_debt: Mapped[Optional[float]] = mapped_column(Float)
    revolving_plus_unsecured_debt: Mapped[Optional[float]] = mapped_column(Float)

    match_results: Mapped[list["MatchResult"]] = relationship(
        "MatchResult", back_populates="application", cascade="all, delete-orphan"
    )


class MatchResult(Base):
    """
    The underwriting outcome for one lender against one application.

    criterion_results is a JSON list of evaluation details, stored as a snapshot
    so the UI can render pass/fail breakdowns without re-running the engine or
    joining back to criteria rows. Each entry contains criterion_id, label,
    passed, actual_value, required_value, explanation, and is_hard_reject.
    """
    __tablename__ = "match_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    application_id: Mapped[int] = mapped_column(Integer, ForeignKey("loan_applications.id"), nullable=False)
    lender_id: Mapped[int] = mapped_column(Integer, ForeignKey("lenders.id"), nullable=False)
    program_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("lender_programs.id"))
    is_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    fit_score: Mapped[float] = mapped_column(Float, default=0)
    matched_program_name: Mapped[Optional[str]] = mapped_column(String(200))
    rejection_reasons: Mapped[Optional[list]] = mapped_column(JSON)
    criterion_results: Mapped[Optional[list]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    application: Mapped["LoanApplication"] = relationship("LoanApplication", back_populates="match_results")
    lender: Mapped["Lender"] = relationship("Lender")
    program: Mapped[Optional["LenderProgram"]] = relationship("LenderProgram")
