"""
Seed script to populate the database with the 5 lender policies extracted from
the provided PDF guidelines. Run once after creating the database:

    python seed_data.py

Each lender's programs and criteria are derived directly from the source PDFs.
The applicability_type on each program controls which applications are routed
to it before criteria are evaluated (see matching.py for the full dispatch
logic). Priority determines order within a lender — lower number = better
tier, tried first.

Field names in criteria map directly to the keys returned by app_to_dict() in
matching.py. Adding a new lender means adding a block below and re-running
this script. Adding a new criterion type means adding an eval branch in
matching.py plus a row here.
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from app.models import Base, Lender, LenderProgram, LenderCriterion

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://kaaj:kaaj@localhost:5432/kaaj")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

STEARNS_EXCLUDED_INDUSTRIES = [
    "gaming_gambling", "hazmat", "oil_gas", "money_services",
    "adult_entertainment", "firearms_weapons", "beauty_salon",
    "tattoo_piercing", "aesthetic_medical", "real_estate",
    "trucking", "restaurant", "car_wash",
]

APEX_EXCLUDED_STATES = ["CA", "NV", "ND", "VT"]

APEX_EXCLUDED_EQUIPMENT = [
    "aircraft_boat", "atm", "audio_visual", "electric_vehicle",
    "fad_medical", "furniture", "kiosk", "leasehold",
    "logging_equipment", "signage", "tanning_beds", "copier",
]

APEX_EXCLUDED_INDUSTRIES = [
    "cannabis", "gaming_gambling", "nonprofit",
    "nail_salon", "oil_gas", "trucking",
]

APEX_APLUS_ALLOWED_INDUSTRIES = [
    "landscaping", "automotive_repair", "construction",
    "industrial_cleaning", "medical_dental", "veterinary", "waste_management",
]

APEX_APLUS_ALLOWED_EQUIPMENT = [
    "forklift", "industrial_machinery", "machine_tools", "vocational_truck",
    "construction_equipment", "medical_equipment",
]


def seed(db):
    existing = db.query(Lender).count()
    if existing > 0:
        print(f"Database already has {existing} lenders. Delete them first to re-seed.")
        return

    _seed_stearns(db)
    _seed_apex(db)
    _seed_advantage_plus(db)
    _seed_citizens_bank(db)
    _seed_falcon(db)

    db.commit()
    print("Seed complete.")


def _add_program(db, lender_id, name, description, applicability_type, priority,
                 min_loan=None, max_loan=None, rate_desc=None,
                 min_term=None, max_term=None):
    p = LenderProgram(
        lender_id=lender_id,
        name=name,
        description=description,
        applicability_type=applicability_type,
        priority=priority,
        min_loan_amount=min_loan,
        max_loan_amount=max_loan,
        min_term_months=min_term,
        max_term_months=max_term,
        rate_description=rate_desc,
    )
    db.add(p)
    db.flush()
    return p


def _add_criterion(db, program_id, label, field_name, criterion_type,
                   threshold=None, allowed_values=None, is_hard_reject=True,
                   null_means_pass=False, weight=1.0, description=None):
    db.add(LenderCriterion(
        program_id=program_id,
        label=label,
        field_name=field_name,
        criterion_type=criterion_type,
        threshold_value=threshold,
        allowed_values=allowed_values,
        is_hard_reject=is_hard_reject,
        null_means_pass=null_means_pass,
        weight=weight,
        description=description,
    ))


def _stearns_base_criteria(db, program_id):
    _add_criterion(db, program_id,
        label="No Bankruptcy in Last 7 Years",
        field_name="years_since_bankruptcy",
        criterion_type="min_value",
        threshold=7,
        null_means_pass=True,
        weight=1.5,
        description="Stearns requires no bankruptcy within the past 7 years. Null means no bankruptcy on record.")
    _add_criterion(db, program_id,
        label="Personal Revolving Debt Limit",
        field_name="personal_revolving_debt",
        criterion_type="max_value",
        threshold=30000,
        null_means_pass=True,
        weight=0.5,
        description="Personal revolving balances must not exceed $30,000.")
    _add_criterion(db, program_id,
        label="Total Revolving and Unsecured Debt Limit",
        field_name="revolving_plus_unsecured_debt",
        criterion_type="max_value",
        threshold=50000,
        null_means_pass=True,
        weight=0.5,
        description="Combined revolving and unsecured debt (excluding student loans) must not exceed $50,000.")
    _add_criterion(db, program_id,
        label="Industry Not Restricted",
        field_name="business_industry",
        criterion_type="excluded_values",
        allowed_values=STEARNS_EXCLUDED_INDUSTRIES,
        weight=1.0,
        description="Stearns does not finance: gaming, hazmat, oil and gas, MSBs, adult entertainment, "
                    "weapons, beauty or tanning salons, tattoo and piercing, aesthetic, real estate, "
                    "trucking (OTR), restaurants, or car washes.")


def _seed_stearns(db):
    lender = Lender(
        name="Stearns Bank",
        description="Equipment Finance — Tier-based credit box with standard, no-PayNet, and corp-only tracks.",
        contact_email=None,
        contact_phone=None,
    )
    db.add(lender)
    db.flush()
    lid = lender.id

    standard_tiers = [
        (1, "Standard Tier 1 (with PayNet)", 725, 685, 3),
        (2, "Standard Tier 2 (with PayNet)", 710, 675, 3),
        (3, "Standard Tier 3 (with PayNet)", 700, 665, 2),
    ]
    for priority, name, fico_min, paynet_min, tib_min in standard_tiers:
        p = _add_program(db, lid, name,
            description=f"Requires PayNet score. FICO {fico_min}+, PayNet {paynet_min}+, {tib_min}+ years in business.",
            applicability_type="with_paynet",
            priority=priority)
        _add_criterion(db, p.id, "Minimum FICO Score", "guarantor_fico", "min_value",
                       threshold=fico_min, weight=2.0)
        _add_criterion(db, p.id, "Minimum PayNet Score", "paynet_score", "min_value",
                       threshold=paynet_min, weight=1.5)
        _add_criterion(db, p.id, "Minimum Time in Business", "years_in_business", "min_value",
                       threshold=tib_min, weight=1.5,
                       description=f"Minimum {tib_min} years in business required for this tier.")
        _stearns_base_criteria(db, p.id)

    no_paynet_tiers = [
        (4, "No-PayNet Tier 1", 735, 5),
        (5, "No-PayNet Tier 2", 720, 3),
        (6, "No-PayNet Tier 3", 710, 2),
    ]
    for priority, name, fico_min, tib_min in no_paynet_tiers:
        p = _add_program(db, lid, name,
            description=f"Applies when no PayNet score is available. Higher FICO required: {fico_min}+, {tib_min}+ years in business.",
            applicability_type="without_paynet",
            priority=priority)
        _add_criterion(db, p.id, "Minimum FICO Score", "guarantor_fico", "min_value",
                       threshold=fico_min, weight=2.0)
        _add_criterion(db, p.id, "Minimum Time in Business", "years_in_business", "min_value",
                       threshold=tib_min, weight=1.5)
        _stearns_base_criteria(db, p.id)

    corp_tiers = [
        (7, "Corp Only Tier 1", 700, 10),
        (8, "Corp Only Tier 2", 690, 5),
        (9, "Corp Only Tier 3", 680, 5),
    ]
    for priority, name, paynet_min, tib_min in corp_tiers:
        p = _add_program(db, lid, name,
            description=f"Corporate-only application with no personal guarantor. "
                        f"PayNet {paynet_min}+, {tib_min}+ years in business.",
            applicability_type="corp_only",
            priority=priority)
        _add_criterion(db, p.id, "Minimum PayNet Score", "paynet_score", "min_value",
                       threshold=paynet_min, weight=2.0)
        _add_criterion(db, p.id, "Minimum Time in Business", "years_in_business", "min_value",
                       threshold=tib_min, weight=1.5)
        _stearns_base_criteria(db, p.id)


def _apex_base_criteria(db, program_id):
    _add_criterion(db, program_id,
        label="State Not Restricted",
        field_name="business_state",
        criterion_type="excluded_values",
        allowed_values=APEX_EXCLUDED_STATES,
        weight=1.0,
        description="Apex does not lend in California, Nevada, North Dakota, or Vermont.")
    _add_criterion(db, program_id,
        label="Equipment Type Not Restricted",
        field_name="equipment_type",
        criterion_type="excluded_values",
        allowed_values=APEX_EXCLUDED_EQUIPMENT,
        weight=1.0,
        description="Apex does not finance: aircraft/boats, ATMs, audio/visual, electric vehicles, "
                    "fad medical, furniture, kiosks, leasehold improvements, logging equipment, "
                    "signage, tanning beds, or copiers.")
    _add_criterion(db, program_id,
        label="Industry Not Restricted",
        field_name="business_industry",
        criterion_type="excluded_values",
        allowed_values=APEX_EXCLUDED_INDUSTRIES,
        weight=1.0,
        description="Apex does not lend to: cannabis, casino/gambling, churches/non-profits, "
                    "nail salons, petroleum/oil and gas, or trucking businesses.")
    _add_criterion(db, program_id,
        label="Equipment Age Limit",
        field_name="equipment_age_years",
        criterion_type="max_value",
        threshold=15,
        null_means_pass=True,
        weight=0.5,
        description="Apex does not finance equipment older than 15 years.")


def _seed_apex(db):
    lender = Lender(
        name="Apex Commercial Capital",
        description="Equipment Finance — A+/A/B/C credit tiers plus medical and corp-only programs. "
                    "Does not lend in CA, NV, ND, or VT.",
        contact_email="credit@apexcommercial.com",
        contact_phone="267-470-3118",
    )
    db.add(lender)
    db.flush()
    lid = lender.id

    p_aplus = _add_program(db, lid, "A+ Rate",
        description="Premium tier for specific approved industries. FICO 720+, PayNet 670+, 5 years TIB. "
                    "Equipment must be 5 years old or newer. No private party sales.",
        applicability_type="general",
        priority=1,
        min_loan=10000, max_loan=500000,
        min_term=24, max_term=60,
        rate_desc="$10K-$49,999: 6.75% | $50K-$500K: 6.50%")
    _add_criterion(db, p_aplus.id, "Minimum FICO Score", "guarantor_fico", "min_value",
                   threshold=720, weight=2.0)
    _add_criterion(db, p_aplus.id, "Minimum PayNet Score", "paynet_score", "min_value",
                   threshold=670, weight=1.5)
    _add_criterion(db, p_aplus.id, "Minimum Time in Business", "years_in_business", "min_value",
                   threshold=5, weight=1.5)
    _add_criterion(db, p_aplus.id, "Maximum Equipment Age", "equipment_age_years", "max_value",
                   threshold=5, null_means_pass=True, weight=1.0,
                   description="A+ program requires collateral no older than 5 years.")
    _add_criterion(db, p_aplus.id, "No Private Party Sale", "is_private_party_sale", "required_false",
                   weight=1.0, description="A+ program does not allow private party sales.")
    _add_criterion(db, p_aplus.id, "Approved Industry", "business_industry", "allowed_values",
                   allowed_values=APEX_APLUS_ALLOWED_INDUSTRIES, weight=1.5,
                   description="A+ rate available for: landscaping, automotive repair, construction, "
                               "industrial cleaning, medical/dental, veterinary, waste management.")
    _apex_base_criteria(db, p_aplus.id)

    standard_tiers = [
        (2, "Standard A Rate", 700, 660, 5, 500000,
         "$10K-$49,999: 7.75% | $50K-$500K: 7.25%"),
        (3, "Standard B Rate", 670, 650, 3, 250000,
         "$10K-$49,999: 8.75% | $50K-$250K: 8.25%"),
        (4, "Standard C Rate", 640, 640, 2, 100000,
         "$10K-$49,999: 12.00% | $50K-$100K: 11.00%"),
    ]
    for priority, name, fico_min, paynet_min, tib_min, max_loan, rate_desc in standard_tiers:
        p = _add_program(db, lid, name,
            description=f"Personal guarantee required. FICO {fico_min}+, PayNet {paynet_min}+, {tib_min}+ years TIB.",
            applicability_type="general",
            priority=priority,
            min_loan=10000, max_loan=max_loan,
            min_term=24, max_term=60,
            rate_desc=rate_desc)
        _add_criterion(db, p.id, "Minimum FICO Score", "guarantor_fico", "min_value",
                       threshold=fico_min, weight=2.0)
        _add_criterion(db, p.id, "Minimum PayNet Score", "paynet_score", "min_value",
                       threshold=paynet_min, null_means_pass=False, weight=1.5)
        _add_criterion(db, p.id, "Minimum Time in Business", "years_in_business", "min_value",
                       threshold=tib_min, weight=1.5)
        _add_criterion(db, p.id, "Maximum Loan Amount", "loan_amount", "max_value",
                       threshold=max_loan, weight=0.5)
        _apex_base_criteria(db, p.id)

    p_med_a = _add_program(db, lid, "Medical A Rate",
        description="For licensed medical practices (MD, DO, DMD, DDS, OD, DPM, DVM). "
                    "FICO 700+, 5 years licensed.",
        applicability_type="medical",
        priority=1,
        min_loan=10000, max_loan=500000,
        min_term=24, max_term=60,
        rate_desc="$10K-$49,999: 7.25% | $50K-$500K: 7.00%")
    _add_criterion(db, p_med_a.id, "Minimum FICO Score", "guarantor_fico", "min_value",
                   threshold=700, weight=2.0)
    _add_criterion(db, p_med_a.id, "Minimum Time in Business", "years_in_business", "min_value",
                   threshold=5, weight=1.5,
                   description="Practice must be licensed and operating for at least 5 years.")
    _apex_base_criteria(db, p_med_a.id)

    p_med_b = _add_program(db, lid, "Medical B Rate",
        description="For newer licensed medical practices. FICO 670+, 2 years licensed.",
        applicability_type="medical",
        priority=2,
        min_loan=10000, max_loan=250000,
        min_term=24, max_term=60,
        rate_desc="$10K-$49,999: 8.00% | $50K-$250K: 7.50%")
    _add_criterion(db, p_med_b.id, "Minimum FICO Score", "guarantor_fico", "min_value",
                   threshold=670, weight=2.0)
    _add_criterion(db, p_med_b.id, "Minimum Time in Business", "years_in_business", "min_value",
                   threshold=2, weight=1.5)
    _apex_base_criteria(db, p_med_b.id)

    p_corp = _add_program(db, lid, "Corp Only — 7.00% Buy Rate",
        description="No personal guarantee. Annual sales $3M+, 5+ years TIB, "
                    "full financials and bank statements required.",
        applicability_type="corp_only",
        priority=1,
        min_loan=10000,
        rate_desc="7.00% buy rate")
    _add_criterion(db, p_corp.id, "Minimum Time in Business", "years_in_business", "min_value",
                   threshold=5, weight=1.5)
    _add_criterion(db, p_corp.id, "Minimum Annual Revenue", "annual_revenue", "min_value",
                   threshold=3000000, weight=2.0,
                   description="Annual sales must be at least $3,000,000.")
    _apex_base_criteria(db, p_corp.id)


def _seed_advantage_plus(db):
    lender = Lender(
        name="Advantage+ Financing",
        description="Non-trucking equipment financing up to $75,000. "
                    "A to B- credit range, startup-friendly. US citizens only.",
        contact_email="SalesSupport@advantageplusfinancing.com",
        contact_phone="(262) 439-7600",
    )
    db.add(lender)
    db.flush()
    lid = lender.id

    p = _add_program(db, lid, "Standard Non-Trucking Program",
        description="Non-trucking applications up to $75,000. FICO 680+, 3+ years industry experience. "
                    "No BK, judgments, foreclosures, repossessions, or tax liens. US citizens only.",
        applicability_type="general",
        priority=1,
        min_loan=10000, max_loan=75000,
        min_term=None, max_term=60,
        rate_desc="A to B- credit range")
    _add_criterion(db, p.id, "Minimum FICO Score", "guarantor_fico", "min_value",
                   threshold=680, weight=2.0,
                   description="Minimum 680 FICO v5 (Equifax). Startups require 700+.")
    _add_criterion(db, p.id, "Minimum Industry Experience", "years_in_business", "min_value",
                   threshold=3, weight=1.5,
                   description="3 years minimum industry experience required.")
    _add_criterion(db, p.id, "Maximum Loan Amount", "loan_amount", "max_value",
                   threshold=75000, weight=0.5)
    _add_criterion(db, p.id, "Minimum Loan Amount", "loan_amount", "min_value",
                   threshold=10000, weight=0.5)
    _add_criterion(db, p.id, "Maximum Loan Term", "loan_term_months", "max_value",
                   threshold=60, weight=0.5)
    _add_criterion(db, p.id, "No Bankruptcy", "has_bankruptcy", "required_false",
                   weight=1.5, description="Advantage+ does not finance borrowers with any bankruptcy history.")
    _add_criterion(db, p.id, "No Judgments", "has_judgments", "required_false", weight=1.0)
    _add_criterion(db, p.id, "No Foreclosures", "has_foreclosures", "required_false", weight=1.0)
    _add_criterion(db, p.id, "No Repossessions", "has_repossessions", "required_false", weight=1.0)
    _add_criterion(db, p.id, "No Tax Liens", "has_tax_liens", "required_false", weight=1.0)
    _add_criterion(db, p.id, "US Citizen Required", "is_us_citizen", "required_true", weight=1.0)
    _add_criterion(db, p.id, "Non-Trucking Equipment Only", "is_trucking", "required_false",
                   weight=1.5,
                   description="Advantage+ ICP covers non-trucking applications only.")


def _seed_citizens_bank(db):
    lender = Lender(
        name="Citizens Bank",
        description="Equipment Finance Program 2025. Finances trucks, trailers, construction, "
                    "and other commercial equipment. Does not lend in California.",
        contact_email="joey.walter@thecitizensbank.net",
        contact_phone="501-451-5113",
    )
    db.add(lender)
    db.flush()
    lid = lender.id

    def citizens_base(program_id):
        _add_criterion(db, program_id, "Minimum FICO Score (TransUnion)", "guarantor_fico",
                       "min_value", threshold=700, weight=2.0,
                       description="Citizens Bank uses TransUnion credit score. Minimum 700 required.")
        _add_criterion(db, program_id, "State Not Restricted", "business_state",
                       "excluded_values", allowed_values=["CA"], weight=1.0,
                       description="Citizens Bank does not lend in California.")
        _add_criterion(db, program_id, "No Cannabis Business", "business_industry",
                       "excluded_values", allowed_values=["cannabis"], weight=1.0)
        _add_criterion(db, program_id, "US Citizen Required", "is_us_citizen",
                       "required_true", weight=1.0)
        _add_criterion(db, program_id, "Bankruptcy Discharged 5+ Years Ago",
                       "years_since_bankruptcy", "min_value",
                       threshold=5, null_means_pass=True, weight=1.0,
                       description="Prior bankruptcy must be discharged for at least 5 years.")

    p1 = _add_program(db, lid, "App-Only Tier 1 — General Program",
        description="App-only up to $75,000 total relationship. 2+ years TIB, homeowner required.",
        applicability_type="general",
        priority=1,
        max_loan=75000,
        rate_desc="10 points max (1 split to Citizens)")
    _add_criterion(db, p1.id, "Minimum Time in Business", "years_in_business", "min_value",
                   threshold=2, weight=1.5)
    _add_criterion(db, p1.id, "Homeownership Required", "is_homeowner", "required_true",
                   weight=1.0, description="Homeownership required for the general program.")
    _add_criterion(db, p1.id, "Maximum Loan Amount", "loan_amount", "max_value",
                   threshold=75000, weight=0.5)
    citizens_base(p1.id)

    p2 = _add_program(db, lid, "App-Only Tier 2 — Startup Program",
        description="Startup program up to $50,000. No TIB requirement but homeowner required. "
                    "Class A CDL required for trucking. 5 years verifiable industry experience if non-trucking.",
        applicability_type="general",
        priority=2,
        max_loan=50000,
        rate_desc="7 points max (1 split to Citizens)")
    _add_criterion(db, p2.id, "Homeownership Required", "is_homeowner", "required_true",
                   weight=1.0, description="Homeownership required for startup program.")
    _add_criterion(db, p2.id, "Maximum Loan Amount", "loan_amount", "max_value",
                   threshold=50000, weight=0.5)
    citizens_base(p2.id)

    p3 = _add_program(db, lid, "App-Only Tier 2 — Non-Homeowner Program",
        description="For non-homeowners. Must have 5+ years at current residence and 2+ years TIB.",
        applicability_type="general",
        priority=3,
        max_loan=75000,
        rate_desc="7 points max (1 split to Citizens)")
    _add_criterion(db, p3.id, "Non-Homeowner Applicant", "is_homeowner", "required_false",
                   weight=0.5,
                   description="This program is specifically for non-homeowners.")
    _add_criterion(db, p3.id, "5+ Years at Current Residence", "years_at_current_residence",
                   "min_value", threshold=5, null_means_pass=False, weight=1.0)
    _add_criterion(db, p3.id, "Minimum Time in Business", "years_in_business", "min_value",
                   threshold=2, weight=1.5)
    _add_criterion(db, p3.id, "Maximum Loan Amount", "loan_amount", "max_value",
                   threshold=75000, weight=0.5)
    citizens_base(p3.id)

    p4 = _add_program(db, lid, "Tier 3 — Full Financial Review",
        description="Transactions $75,000 to $1,000,000 or those not fitting app-only tiers. "
                    "Full financials required: 2 years business tax returns, personal tax returns, "
                    "personal financial statement, debt schedule, and 3 months bank statements.",
        applicability_type="general",
        priority=4,
        min_loan=75000, max_loan=1000000,
        rate_desc="Full financial underwriting")
    _add_criterion(db, p4.id, "Minimum Loan Amount", "loan_amount", "min_value",
                   threshold=75000, weight=0.5)
    _add_criterion(db, p4.id, "Maximum Loan Amount", "loan_amount", "max_value",
                   threshold=1000000, weight=0.5)
    citizens_base(p4.id)


def _seed_falcon(db):
    lender = Lender(
        name="Falcon Equipment Finance",
        description="A Division of Falcon National Bank. A through E credit ratings, "
                    "min $15,000. 3+ years TIB, FICO 680+, PayNet 660+.",
        contact_email="ETickner@FalconEquipmentFinance.com",
        contact_phone="651-332-6517",
    )
    db.add(lender)
    db.flush()
    lid = lender.id

    p_standard = _add_program(db, lid, "Standard Commercial Program",
        description="3+ years TIB, FICO 680+, PayNet 660+. "
                    "App-only up to $150K trucking, $250K commercial, $350K manufacturing. "
                    "Bankruptcies must be discharged 15+ years ago.",
        applicability_type="general",
        priority=1,
        min_loan=15000,
        rate_desc="A: 7.75-9.00% | B: 8.25-9.75% | C: 9.00-10.50% | D: 10.00-11.75% | E: 12.00-13.75%")
    _add_criterion(db, p_standard.id, "Minimum FICO Score", "guarantor_fico", "min_value",
                   threshold=680, weight=2.0)
    _add_criterion(db, p_standard.id, "Minimum PayNet Score", "paynet_score", "min_value",
                   threshold=660, null_means_pass=False, weight=1.5)
    _add_criterion(db, p_standard.id, "Minimum Time in Business", "years_in_business", "min_value",
                   threshold=3, weight=1.5)
    _add_criterion(db, p_standard.id, "Minimum Loan Amount", "loan_amount", "min_value",
                   threshold=15000, weight=0.5)
    _add_criterion(db, p_standard.id, "Bankruptcy Discharged 15+ Years Ago",
                   "years_since_bankruptcy", "min_value",
                   threshold=15, null_means_pass=True, weight=1.0,
                   description="Falcon requires bankruptcies to be dismissed or discharged 15 or more years ago.")

    p_trucking = _add_program(db, lid, "Trucking Program — A/B Credit Only",
        description="For trucking applicants (A and B credit only). FICO 700+, PayNet 680+, "
                    "5+ years TIB, 5+ trucks currently operating. "
                    "Class 8 trucks and trailers must be 10 years or newer. Reefer trailers under 7 years.",
        applicability_type="trucking",
        priority=1,
        min_loan=15000,
        rate_desc="A: 7.75-9.00% | B: 8.25-9.75%")
    _add_criterion(db, p_trucking.id, "Minimum FICO Score", "guarantor_fico", "min_value",
                   threshold=700, weight=2.0)
    _add_criterion(db, p_trucking.id, "Minimum PayNet Score", "paynet_score", "min_value",
                   threshold=680, null_means_pass=False, weight=1.5)
    _add_criterion(db, p_trucking.id, "Minimum Time in Business", "years_in_business", "min_value",
                   threshold=5, weight=1.5,
                   description="Trucking applicants must have 5+ years in business.")
    _add_criterion(db, p_trucking.id, "Minimum Fleet Size", "num_trucks_operating", "min_value",
                   threshold=5, null_means_pass=False, weight=1.0,
                   description="Must currently be operating at least 5 trucks.")
    _add_criterion(db, p_trucking.id, "Minimum Loan Amount", "loan_amount", "min_value",
                   threshold=15000, weight=0.5)
    _add_criterion(db, p_trucking.id, "Bankruptcy Discharged 15+ Years Ago",
                   "years_since_bankruptcy", "min_value",
                   threshold=15, null_means_pass=True, weight=1.0)


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed(db)
