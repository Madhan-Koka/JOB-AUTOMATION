
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.application import JobApplicationRecord


router = APIRouter(
    prefix="/api/v1/applications",
    tags=["applications"]
)


# Allowed application statuses
ApplicationStatus = Literal[
    "Saved",
    "Applied",
    "Interview",
    "Rejected",
    "Offer"
]


class ApplicationCreate(BaseModel):
    job_title: str
    company: str
    location: str | None = None
    job_url: str | None = None
    status: ApplicationStatus = "Saved"
    applied_date: date | None = None
    notes: str = ""


class ApplicationUpdate(BaseModel):
    job_title: str | None = None
    company: str | None = None
    location: str | None = None
    job_url: str | None = None
    status: ApplicationStatus | None = None
    applied_date: date | None = None
    notes: str | None = None


def serialize(record: JobApplicationRecord):
    return {
        "id": record.id,
        "job_title": record.job_title,
        "company": record.company,
        "location": record.location,
        "job_url": record.job_url,
        "status": record.status,
        "applied_date": (
            record.applied_date.isoformat()
            if record.applied_date else None
        ),
        "notes": record.notes,
        "created_at": (
            record.created_at.isoformat()
            if record.created_at else None
        ),
    }


# Create application
@router.post("")
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db)
):
    record = JobApplicationRecord(**payload.model_dump())

    db.add(record)
    db.commit()
    db.refresh(record)

    return serialize(record)


# Get all applications
@router.get("")
def get_applications(db: Session = Depends(get_db)):
    records = (
        db.query(JobApplicationRecord)
        .order_by(JobApplicationRecord.created_at.desc())
        .all()
    )

    return [serialize(record) for record in records]


# Get application by ID
@router.get("/{application_id}")
def get_application(
    application_id: int,
    db: Session = Depends(get_db)
):
    record = db.query(JobApplicationRecord).filter(
        JobApplicationRecord.id == application_id
    ).first()

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    return serialize(record)


# Update application
@router.put("/{application_id}")
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db)
):
    record = db.query(JobApplicationRecord).filter(
        JobApplicationRecord.id == application_id
    ).first()

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    update_data = payload.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)

    return serialize(record)


# Delete application
@router.delete("/{application_id}")
def delete_application(
    application_id: int,
    db: Session = Depends(get_db)
):
    record = db.query(JobApplicationRecord).filter(
        JobApplicationRecord.id == application_id
    ).first()

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    db.delete(record)
    db.commit()

    return {
        "message": "Application deleted successfully",
        "id": application_id
    }
