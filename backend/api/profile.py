import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import get_db
from models.candidate import CandidateProfileRecord

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])

class CandidateProfileUpdate(BaseModel):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None
    skills: list[str] = Field(default_factory=list)

def serialize(record: CandidateProfileRecord):
    return {
        "id": record.id,
        "full_name": record.full_name,
        "email": record.email,
        "phone": record.phone,
        "linkedin": record.linkedin,
        "github": record.github,
        "portfolio": record.portfolio,
        "skills": json.loads(record.skills_json or "[]"),
        "resume_filename": record.resume_filename,
    }

@router.get("")
def get_profile(db: Session = Depends(get_db)):
    record = db.query(CandidateProfileRecord).first()
    if record is None:
        raise HTTPException(status_code=404, detail="No candidate profile yet. Upload a resume first.")
    return serialize(record)

@router.put("")
def update_profile(payload: CandidateProfileUpdate, db: Session = Depends(get_db)):
    record = db.query(CandidateProfileRecord).first()
    if record is None:
        record = CandidateProfileRecord()
        db.add(record)

    record.full_name = payload.full_name.strip()
    record.email = payload.email.strip()
    record.phone = payload.phone.strip()
    record.linkedin = payload.linkedin
    record.github = payload.github
    record.portfolio = payload.portfolio
    record.skills_json = json.dumps(payload.skills)

    db.commit()
    db.refresh(record)
    return serialize(record)
