"""
Reads each lender PDF, extracts text with pdfplumber, sends it to the Anthropic
API with a structured schema prompt, and inserts the returned JSON into the database.

Run once after creating the database tables:
    python ingest_lenders.py

Requires ANTHROPIC_API_KEY in backend/.env. Clears existing lender data before
inserting so the script is safe to re-run.
"""
import json
import sys
from pathlib import Path

import anthropic
import pdfplumber
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.models import Base, Lender, LenderCriterion, LenderProgram, MatchResult

PDF_DIR = Path(__file__).parent.parent / "Kaaj Lender Background Docs"

LENDER_PDFS = [
    "112025 Rates - STANDARD.pdf",
    "2025 Program Guidelines UPDATED.pdf",
    "Advantage++Broker+2025.pdf",
    "Apex EF Broker Guidelines_082725.pdf",
    "EF Credit Box 4.14.2025.pdf",
]

SCHEMA_PROMPT = """
You are extracting equipment finance lender guidelines from a PDF into structured JSON.

Return a single valid JSON object. No markdown, no explanation, no code fences — raw JSON only.

Schema:
{
  "name": "Lender name",
  "description": "One-sentence description of the lender and program type",
  "contact_email": null or "email@domain.com",
  "contact_phone": null or "phone string",
  "programs": [
    {
      "name": "Program name (e.g. Standard Tier 1, A+ Rate)",
      "description": "What this program is for and its main requirements",
      "applicability_type": "one of: general | with_paynet | without_paynet | corp_only | medical | trucking",
      "priority": 1,
      "min_loan_amount": null or number,
      "max_loan_amount": null or number,
      "min_term_months": null or number,
      "max_term_months": null or number,
      "rate_description": null or "rate string from PDF",
      "criteria": [
        {
          "label": "Human-readable criterion label",
          "field_name": "application_field_name (see list below)",
          "criterion_type": "one of: min_value | max_value | required_true | required_false | excluded_values | allowed_values",
          "threshold_value": null or number,
          "allowed_values": null or ["value1", "value2"],
          "is_hard_reject": true,
          "null_means_pass": false,
          "weight": 1.0,
          "description": null or "brief explanation"
        }
      ]
    }
  ]
}

applicability_type:
- "general": standard personal-guarantee applications
- "with_paynet": only when a PayNet business credit score is available
- "without_paynet": only when no PayNet score is available (higher FICO required)
- "corp_only": no personal guarantor, corporate credit only
- "medical": medical, dental, or veterinary industry only
- "trucking": trucking industry or trucking equipment only

criterion_type:
- "min_value": numeric field must be >= threshold_value
- "max_value": numeric field must be <= threshold_value
- "required_true": boolean field must be true
- "required_false": boolean field must be false (e.g. no bankruptcy)
- "excluded_values": field value must NOT appear in allowed_values list
- "allowed_values": field value must appear in allowed_values list

Valid field_name values:
- guarantor_fico: FICO credit score integer (use for all FICO / credit score requirements)
- paynet_score: PayNet business credit score integer
- years_in_business: years the business has operated (float)
- business_state: two-letter US state code string
- business_industry: industry slug string (see slugs below)
- annual_revenue: annual revenue in dollars
- loan_amount: requested loan amount in dollars
- loan_term_months: loan term in months integer
- equipment_type: equipment type slug string (see slugs below)
- equipment_age_years: age of equipment in years float
- is_private_party_sale: boolean, true if buying from private party
- is_us_citizen: boolean, true if US citizen
- is_homeowner: boolean, true if homeowner
- years_at_current_residence: years at current address float
- has_bankruptcy: boolean, true if any bankruptcy ever on record
- years_since_bankruptcy: years since discharge float (null = no bankruptcy on record)
- has_judgments: boolean
- has_foreclosures: boolean
- has_repossessions: boolean
- has_tax_liens: boolean
- is_trucking: boolean, true if trucking industry or trucking equipment (derived field)
- num_trucks_operating: integer, trucks currently operating
- has_cdl: boolean, true if has CDL
- personal_revolving_debt: total personal revolving debt dollars
- revolving_plus_unsecured_debt: total revolving + unsecured debt dollars

Industry slugs for excluded_values / allowed_values:
automotive_repair, construction, landscaping, industrial_cleaning, manufacturing,
machine_tools, medical_dental, veterinary, trucking, waste_management, agriculture,
restaurant, retail, technology, logging, oil_gas, real_estate, gaming_gambling,
adult_entertainment, cannabis, beauty_salon, tattoo_piercing, car_wash,
firearms_weapons, aesthetic_medical, hazmat, money_services, nonprofit, nail_salon

Equipment type slugs for excluded_values / allowed_values:
class_8_truck, trailer, dump_truck, medium_duty_truck, light_duty_truck,
vocational_truck, construction_equipment, forklift, industrial_machinery,
machine_tools, automotive_repair_equipment, medical_equipment, material_handling,
janitorial_equipment, office_equipment, restaurant_equipment, lawn_turf_equipment,
farm_equipment, audio_visual, logging_equipment, aircraft_boat, electric_vehicle,
atm, copier, signage, furniture, kiosk, leasehold, tanning_beds, fad_medical

Guidance:
- If a lender has tiered programs (Tier 1, Tier 2, etc.), model each tier as a separate program.
  Set priority so the best / most favorable tier is priority 1. Programs are evaluated in
  priority order and the applicant lands in the first one they fully qualify for.
- If a lender has separate tracks (e.g. with-PayNet vs. without-PayNet), create separate programs
  with the correct applicability_type for each track.
- For "no bankruptcy" rules: use field_name "has_bankruptcy", criterion_type "required_false".
- For "bankruptcy must be discharged X years ago" rules: use field_name "years_since_bankruptcy",
  criterion_type "min_value", threshold_value X, null_means_pass true (null = no bankruptcy = pass).
- Weights: 2.0 for FICO and PayNet, 1.5 for TIB and bankruptcy, 1.0 for state/industry/flags, 0.5 for loan limits.
"""


def extract_text(path: Path) -> str:
    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def parse_lender(client: anthropic.Anthropic, text: str) -> dict:
    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8192,
        messages=[
            {
                "role": "user",
                "content": f"{SCHEMA_PROMPT}\n\nPDF content:\n\n{text}",
            }
        ],
    )
    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(raw)


def insert_lender(db: Session, data: dict) -> None:
    lender = Lender(
        name=data["name"],
        description=data.get("description"),
        contact_email=data.get("contact_email"),
        contact_phone=data.get("contact_phone"),
    )
    db.add(lender)
    db.flush()

    for i, prog in enumerate(data.get("programs", []), 1):
        program = LenderProgram(
            lender_id=lender.id,
            name=prog["name"],
            description=prog.get("description"),
            applicability_type=prog.get("applicability_type", "general"),
            priority=prog.get("priority", i),
            min_loan_amount=prog.get("min_loan_amount"),
            max_loan_amount=prog.get("max_loan_amount"),
            min_term_months=prog.get("min_term_months"),
            max_term_months=prog.get("max_term_months"),
            rate_description=prog.get("rate_description"),
        )
        db.add(program)
        db.flush()

        for crit in prog.get("criteria", []):
            db.add(LenderCriterion(
                program_id=program.id,
                label=crit.get("label", crit.get("field_name", "Criterion")),
                field_name=crit["field_name"],
                criterion_type=crit["criterion_type"],
                threshold_value=crit.get("threshold_value"),
                allowed_values=crit.get("allowed_values"),
                is_hard_reject=crit.get("is_hard_reject", True),
                null_means_pass=crit.get("null_means_pass", False),
                weight=crit.get("weight", 1.0),
                description=crit.get("description"),
            ))


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    client = anthropic.Anthropic()

    with SessionLocal() as db:
        existing = db.query(Lender).count()
        if existing > 0:
            print(f"Clearing {existing} existing lenders...")
            db.query(MatchResult).delete()
            db.query(LenderCriterion).delete()
            db.query(LenderProgram).delete()
            db.query(Lender).delete()
            db.flush()

        for pdf_name in LENDER_PDFS:
            path = PDF_DIR / pdf_name
            if not path.exists():
                print(f"Skipping {pdf_name} — file not found at {path}")
                continue
            print(f"Processing {pdf_name}...")
            try:
                text = extract_text(path)
                data = parse_lender(client, text)
                insert_lender(db, data)
                print(f"  Inserted: {data['name']} ({len(data.get('programs', []))} programs)")
            except json.JSONDecodeError as exc:
                print(f"  JSON parse error for {pdf_name}: {exc}")
                db.rollback()
                sys.exit(1)
            except Exception as exc:
                print(f"  Error processing {pdf_name}: {exc}")
                db.rollback()
                sys.exit(1)

        db.commit()

    print("Done.")
