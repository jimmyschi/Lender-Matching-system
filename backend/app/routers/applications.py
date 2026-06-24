from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import LoanApplication
from app.schemas import LoanApplicationCreate, LoanApplicationRead

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("/", response_model=list[LoanApplicationRead])
def list_applications(db: Session = Depends(get_db)):
    return db.query(LoanApplication).order_by(LoanApplication.created_at.desc()).all()


@router.post("/", response_model=LoanApplicationRead, status_code=201)
def create_application(payload: LoanApplicationCreate, db: Session = Depends(get_db)):
    app = LoanApplication(**payload.model_dump())
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


@router.get("/{application_id}", response_model=LoanApplicationRead)
def get_application(application_id: int, db: Session = Depends(get_db)):
    app = db.query(LoanApplication).filter(LoanApplication.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.put("/{application_id}", response_model=LoanApplicationRead)
def update_application(
    application_id: int,
    payload: LoanApplicationCreate,
    db: Session = Depends(get_db),
):
    app = db.query(LoanApplication).filter(LoanApplication.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    for key, value in payload.model_dump().items():
        setattr(app, key, value)
    db.commit()
    db.refresh(app)
    return app


@router.delete("/{application_id}", status_code=204)
def delete_application(application_id: int, db: Session = Depends(get_db)):
    app = db.query(LoanApplication).filter(LoanApplication.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(app)
    db.commit()
