from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import LoanApplication, Lender, LenderProgram, MatchResult
from app.schemas import UnderwritingResultsRead, MatchResultRead
from app.services.matching import run_underwriting

router = APIRouter(prefix="/underwriting", tags=["underwriting"])


@router.post("/{application_id}/run", response_model=UnderwritingResultsRead)
def run_underwriting_for_application(application_id: int, db: Session = Depends(get_db)):
    application = db.query(LoanApplication).filter(LoanApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    lenders = (
        db.query(Lender)
        .options(joinedload(Lender.programs).joinedload(LenderProgram.criteria))
        .all()
    )

    db.query(MatchResult).filter(MatchResult.application_id == application_id).delete()

    results = run_underwriting(application, lenders)

    saved = []
    for r in results:
        match = MatchResult(
            application_id=application_id,
            lender_id=r["lender_id"],
            program_id=r["program_id"],
            is_eligible=r["is_eligible"],
            fit_score=r["fit_score"],
            matched_program_name=r["matched_program_name"],
            rejection_reasons=r["rejection_reasons"],
            criterion_results=r["criterion_results"],
        )
        db.add(match)
        saved.append(match)

    application.status = "completed"
    db.commit()
    for m in saved:
        db.refresh(m)

    return {"application": application, "matches": saved}


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
