
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine

# Import models so SQLAlchemy registers their tables
from models import CandidateProfileRecord, JobApplicationRecord

from api.resume import router as resume_router
from api.profile import router as profile_router
from api.jobs import router as jobs_router
from api.applications import router as applications_router
from api.resume_match import router as resume_match_router

# Create database tables if they do not already exist
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="JobPilot API",
    description=(
        "Backend API for JobPilot, an intelligent job application automation "
        "platform. Provides resume upload and parsing, candidate profile "
        "management, job discovery, resume-job matching, and application tracking. "
        "Future capabilities include resume tailoring, application autofill, "
        "user-approved submission, and submission verification."
    ),
    version="0.1.0",
)


# Configure frontend-backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register API routers
app.include_router(resume_router)
app.include_router(profile_router)
app.include_router(jobs_router)
app.include_router(applications_router)

# Resume Match API
app.include_router(
    resume_match_router,
    prefix="/api/v1/resume-match",
    tags=["Resume Match"],
)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
