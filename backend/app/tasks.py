"""
This is the Hatchet task definition. The @hatchet.task decorator registers this
function as a named workflow step. It takes the application ID as input, opens its
own database session, runs the matching engine, saves results, and returns.
"""
from pydantic import BaseModel
from hatchet_sdk import Hatchet
from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models import Lender, LenderProgram, LoanApplication, MatchResult
from app.services.matching import run_underwriting

hatchet = Hatchet()


class UnderwritingInput(BaseModel):
    application_id: int


@hatchet.task(name="run-underwriting", input_validator=UnderwritingInput)
def underwriting_task(input: UnderwritingInput, ctx) -> dict:
    application_id = input.application_id

    with SessionLocal() as db:
        application = db.get(LoanApplication, application_id)
        if application is None:
            raise ValueError(f"Application {application_id} not found")

        lenders = (
            db.query(Lender)
            .options(joinedload(Lender.programs).joinedload(LenderProgram.criteria))
            .all()
        )

        db.query(MatchResult).filter(MatchResult.application_id == application_id).delete()

        results = run_underwriting(application, lenders)

        for r in results:
            db.add(MatchResult(
                application_id=application_id,
                lender_id=r["lender_id"],
                program_id=r["program_id"],
                is_eligible=r["is_eligible"],
                fit_score=r["fit_score"],
                matched_program_name=r["matched_program_name"],
                rejection_reasons=r["rejection_reasons"],
                criterion_results=r["criterion_results"],
            ))

        application.status = "completed"
        db.commit()

    return {"application_id": application_id, "matches_evaluated": len(results)}
