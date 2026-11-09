
import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from models.candidate import CandidateProfileRecord
from services.resume_extraction import extract_candidate_data
from parser import CandidateProfile, JobListing
from tailor import ApplicationTailor


router = APIRouter(prefix="/api/v1/resumes", tags=["resumes"])

UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads" / "resumes"
MAX_BYTES = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    original_name = Path(file.filename or "resume").name
    suffix = Path(original_name).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail="Supported formats: PDF, TXT, MD",
        )

    content = await file.read(MAX_BYTES + 1)

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if len(content) > MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Resume must be 5 MB or smaller",
        )

    if suffix == ".pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="File does not appear to be a valid PDF",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    stored_name = f"{uuid.uuid4().hex}{suffix}"
    stored_path = UPLOAD_DIR / stored_name
    stored_path.write_bytes(content)

    try:
        extracted = extract_candidate_data(stored_path)
    except Exception as exc:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422,
            detail=f"Could not parse resume: {exc}",
        ) from exc

    record = db.query(CandidateProfileRecord).first()

    if record is None:
        record = CandidateProfileRecord()
        db.add(record)

    record.full_name = extracted["full_name"]
    record.email = extracted["email"]
    record.phone = extracted["phone"]
    record.linkedin = extracted["linkedin"]
    record.github = extracted["github"]
    record.portfolio = extracted["portfolio"]
    record.skills_json = json.dumps(extracted["skills"])
    record.raw_resume_text = extracted["raw_resume_text"]
    record.resume_filename = original_name
    record.resume_path = str(stored_path)

    db.commit()
    db.refresh(record)

    return {
        "resume_id": record.id,
        "filename": original_name,
        "status": "PARSED",
        "profile": {
            "id": record.id,
            "full_name": record.full_name,
            "email": record.email,
            "phone": record.phone,
            "linkedin": record.linkedin,
            "github": record.github,
            "portfolio": record.portfolio,
            "skills": json.loads(record.skills_json or "[]"),
            "resume_filename": record.resume_filename,
        },
        "extraction_note": (
            "Review and correct parsed fields before using them "
            "for applications."
        ),
    }


@router.post("/tailor")
def tailor_resume(
    job: JobListing,
    db: Session = Depends(get_db),
):
    """Generate a tailored resume and cover letter for a selected job."""

    record = db.query(CandidateProfileRecord).first()

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Please upload a resume before tailoring.",
        )

    if not record.resume_path:
        raise HTTPException(
            status_code=404,
            detail="No uploaded resume file was found.",
        )

    original_resume_path = Path(record.resume_path)

    if not original_resume_path.exists():
        raise HTTPException(
            status_code=404,
            detail="The stored resume file could not be found.",
        )

    profile = CandidateProfile(
        full_name=record.full_name or "",
        email=record.email or "",
        phone=record.phone or "",
        linkedin=record.linkedin,
        github=record.github,
        portfolio=record.portfolio,
        skills=json.loads(record.skills_json or "[]"),
        raw_resume_text=record.raw_resume_text or "",
    )

    try:
        tailor = ApplicationTailor()

        result = tailor.create_tailored_artifacts(
            profile=profile,
            job=job,
            original_resume_path=original_resume_path,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Resume tailoring failed: {exc}",
        ) from exc

    return {
        "job_id": result.job.id,
        "company": result.job.company,
        "job_title": result.job.title,
        "status": result.status,
        "tailored_resume_path": str(result.tailored_resume_path),
        "cover_letter": result.cover_letter,
        "notes": result.notes,
        "message": (
            "Tailored documents generated. Review them before applying."
        ),
    }
