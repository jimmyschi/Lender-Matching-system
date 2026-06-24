from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import Lender, LenderProgram, LenderCriterion
from app.schemas import (
    LenderCreate, LenderRead, LenderSummary,
    LenderProgramCreate, LenderProgramRead,
    LenderCriterionCreate, LenderCriterionRead,
)

router = APIRouter(prefix="/lenders", tags=["lenders"])


@router.get("/", response_model=list[LenderSummary])
def list_lenders(db: Session = Depends(get_db)):
    return db.query(Lender).order_by(Lender.name).all()


@router.post("/", response_model=LenderRead, status_code=201)
def create_lender(payload: LenderCreate, db: Session = Depends(get_db)):
    lender = Lender(
        name=payload.name,
        description=payload.description,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
    )
    db.add(lender)
    db.flush()

    for prog_data in payload.programs:
        program = LenderProgram(lender_id=lender.id, **prog_data.model_dump(exclude={"criteria"}))
        db.add(program)
        db.flush()
        for crit_data in prog_data.criteria:
            db.add(LenderCriterion(program_id=program.id, **crit_data.model_dump()))

    db.commit()
    db.refresh(lender)
    return _load_lender(lender.id, db)


@router.get("/{lender_id}", response_model=LenderRead)
def get_lender(lender_id: int, db: Session = Depends(get_db)):
    lender = _load_lender(lender_id, db)
    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")
    return lender


@router.put("/{lender_id}", response_model=LenderRead)
def update_lender(lender_id: int, payload: LenderCreate, db: Session = Depends(get_db)):
    lender = db.query(Lender).filter(Lender.id == lender_id).first()
    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")
    lender.name = payload.name
    lender.description = payload.description
    lender.contact_email = payload.contact_email
    lender.contact_phone = payload.contact_phone
    db.commit()
    return _load_lender(lender_id, db)


@router.delete("/{lender_id}", status_code=204)
def delete_lender(lender_id: int, db: Session = Depends(get_db)):
    lender = db.query(Lender).filter(Lender.id == lender_id).first()
    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")
    db.delete(lender)
    db.commit()


@router.post("/{lender_id}/programs", response_model=LenderProgramRead, status_code=201)
def add_program(lender_id: int, payload: LenderProgramCreate, db: Session = Depends(get_db)):
    if not db.query(Lender).filter(Lender.id == lender_id).first():
        raise HTTPException(status_code=404, detail="Lender not found")
    program = LenderProgram(lender_id=lender_id, **payload.model_dump(exclude={"criteria"}))
    db.add(program)
    db.flush()
    for crit_data in payload.criteria:
        db.add(LenderCriterion(program_id=program.id, **crit_data.model_dump()))
    db.commit()
    db.refresh(program)
    return program


@router.put("/{lender_id}/programs/{program_id}", response_model=LenderProgramRead)
def update_program(
    lender_id: int,
    program_id: int,
    payload: LenderProgramCreate,
    db: Session = Depends(get_db),
):
    program = db.query(LenderProgram).filter(
        LenderProgram.id == program_id, LenderProgram.lender_id == lender_id
    ).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    for key, value in payload.model_dump(exclude={"criteria"}).items():
        setattr(program, key, value)
    db.commit()
    db.refresh(program)
    return program


@router.delete("/{lender_id}/programs/{program_id}", status_code=204)
def delete_program(lender_id: int, program_id: int, db: Session = Depends(get_db)):
    program = db.query(LenderProgram).filter(
        LenderProgram.id == program_id, LenderProgram.lender_id == lender_id
    ).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    db.delete(program)
    db.commit()


@router.post("/{lender_id}/programs/{program_id}/criteria", response_model=LenderCriterionRead, status_code=201)
def add_criterion(
    lender_id: int,
    program_id: int,
    payload: LenderCriterionCreate,
    db: Session = Depends(get_db),
):
    program = db.query(LenderProgram).filter(
        LenderProgram.id == program_id, LenderProgram.lender_id == lender_id
    ).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    criterion = LenderCriterion(program_id=program_id, **payload.model_dump())
    db.add(criterion)
    db.commit()
    db.refresh(criterion)
    return criterion


@router.put("/{lender_id}/programs/{program_id}/criteria/{criterion_id}", response_model=LenderCriterionRead)
def update_criterion(
    lender_id: int,
    program_id: int,
    criterion_id: int,
    payload: LenderCriterionCreate,
    db: Session = Depends(get_db),
):
    criterion = db.query(LenderCriterion).filter(LenderCriterion.id == criterion_id).first()
    if not criterion:
        raise HTTPException(status_code=404, detail="Criterion not found")
    for key, value in payload.model_dump().items():
        setattr(criterion, key, value)
    db.commit()
    db.refresh(criterion)
    return criterion


@router.delete("/{lender_id}/programs/{program_id}/criteria/{criterion_id}", status_code=204)
def delete_criterion(
    lender_id: int,
    program_id: int,
    criterion_id: int,
    db: Session = Depends(get_db),
):
    criterion = db.query(LenderCriterion).filter(LenderCriterion.id == criterion_id).first()
    if not criterion:
        raise HTTPException(status_code=404, detail="Criterion not found")
    db.delete(criterion)
    db.commit()


def _load_lender(lender_id: int, db: Session):
    return (
        db.query(Lender)
        .options(joinedload(Lender.programs).joinedload(LenderProgram.criteria))
        .filter(Lender.id == lender_id)
        .first()
    )
