
"""
parser.py - Data schemas and resume/profile parsing utilities.
"""

from pathlib import Path
from typing import List, Optional
import re

from pydantic import BaseModel, Field
import pypdf


class CandidateProfile(BaseModel):
    full_name: str
    email: str
    phone: str
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    raw_resume_text: str = ""


class JobListing(BaseModel):
    id: str
    title: str
    company: str
    location: str = "Remote"
    url: str
    description: str
    source: str = "GenericWeb"


class ApplicationPayload(BaseModel):
    job: JobListing
    tailored_resume_path: Path
    cover_letter: str
    status: str = "PENDING"
    notes: Optional[str] = None


def parse_resume(file_path: str | Path) -> str:
    """Extract raw text from a PDF or plain text resume."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Resume file not found at: {path}")

    if path.suffix.lower() == ".pdf":
        text_content: List[str] = []

        with open(path, "rb") as f:
            reader = pypdf.PdfReader(f)

            for page in reader.pages:
                extracted = page.extract_text()

                if extracted:
                    text_content.append(extracted)

        return "\n".join(text_content).strip()

    elif path.suffix.lower() in [".txt", ".md"]:
        return path.read_text(encoding="utf-8").strip()

    else:
        raise ValueError(f"Unsupported resume format: {path.suffix}")


def extract_email(text: str) -> str:
    """Extract the first email address found in resume text."""
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

    match = re.search(email_pattern, text)

    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    """Extract an Indian mobile number from resume text."""
    phone_pattern = (
        r"(?<!\d)"
        r"(?:\+91[\s-]?)?"
        r"[6-9]\d{2}[\s-]?\d{3}[\s-]?\d{4}"
        r"(?!\d)"
    )

    match = re.search(phone_pattern, text)

    if match:
        return match.group(0).strip()

    return ""


def load_candidate_profile(
    config_data: dict,
    resume_path: Optional[str | Path] = None
) -> CandidateProfile:
    """Build a CandidateProfile using config data and resume text."""

    raw_text = ""

    if resume_path:
        try:
            raw_text = parse_resume(resume_path)
        except Exception as err:
            raw_text = f"Error reading resume file: {err}"

    # Extract contact information from resume text.
    extracted_email = extract_email(raw_text)
    extracted_phone = extract_phone(raw_text)

    # Prefer extracted values; fall back to config values.
    email = extracted_email or config_data.get("email", "")
    phone = extracted_phone or config_data.get("phone", "")

    return CandidateProfile(
        full_name=config_data.get("full_name", ""),
        email=email,
        phone=phone,
        linkedin=config_data.get("linkedin"),
        github=config_data.get("github"),
        portfolio=config_data.get("portfolio"),
        skills=config_data.get("skills", []),
        raw_resume_text=raw_text
    )
