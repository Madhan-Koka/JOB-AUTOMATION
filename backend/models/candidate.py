from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class CandidateProfileRecord(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200), default="")
    email: Mapped[str] = mapped_column(String(320), default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    linkedin: Mapped[str | None] = mapped_column(String(500), nullable=True)
    github: Mapped[str | None] = mapped_column(String(500), nullable=True)
    portfolio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    skills_json: Mapped[str] = mapped_column(Text, default="[]")
    raw_resume_text: Mapped[str] = mapped_column(Text, default="")
    resume_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resume_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
