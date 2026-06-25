"""
The router checks for the Hatchet token at startup. When it is present, dispatching
an underwriting job means calling underwriting_task.run() — one line — which sends
the work to the queue and blocks until the worker finishes. If Hatchet is not
configured, it falls back to synchronous execution so the system works in both modes.
"""
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import LoanApplication, Lender, LenderProgram, MatchResult
from app.schemas import UnderwritingResultsRead
from app.services.matching import run_underwriting

router = APIRouter(prefix="/underwriting", tags=["underwriting"])

_HATCHET_ENABLED = False
if os.getenv("HATCHET_CLIENT_TOKEN"):
    try:
        from app.tasks import underwriting_task, UnderwritingInput
        _HATCHET_ENABLED = True
    except Exception as _hatchet_err:
        print(f"[underwriting] Hatchet init failed, running synchronously: {_hatchet_err}")


@router.post("/{application_id}/run", response_model=UnderwritingResultsRead)
def run_underwriting_for_application(application_id: int, db: Session = Depends(get_db)):
    application = db.query(LoanApplication).filter(LoanApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if _HATCHET_ENABLED:
        underwriting_task.run(UnderwritingInput(application_id=application_id))
        db.expire_all()
    else:
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

    application = db.query(LoanApplication).filter(LoanApplication.id == application_id).first()
    matches = (
        db.query(MatchResult)
        .filter(MatchResult.application_id == application_id)
        .order_by(MatchResult.fit_score.desc())
        .all()
    )
    return {"application": application, "matches": matches}


@router.get("/{application_id}/results", response_model=UnderwritingResultsRead)
def get_results(application_id: int, db: Session = Depends(get_db)):
    application = db.query(LoanApplication).filter(LoanApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    matches = (
        db.query(MatchResult)
        .filter(MatchResult.application_id == application_id)
        .order_by(MatchResult.fit_score.desc())
        .all()
    )
    return {"application": application, "matches": matches}
