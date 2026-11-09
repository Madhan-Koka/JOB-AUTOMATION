
from typing import Optional

from fastapi import APIRouter, Query
from parser import JobListing

router = APIRouter()

SAMPLE_JOBS = [
    JobListing(
        id="JOB001",
        title="Software Engineer",
        company="Google",
        location="Bangalore, India",
        url="https://careers.google.com/",
        description=(
            "Develop scalable software applications using Python, Java, "
            "data structures, algorithms, and REST APIs. "
            "Experience: 0-1 years. Entry-level opportunity."
        ),
        source="Google Careers",
    ),
    JobListing(
        id="JOB002",
        title="AI Engineer",
        company="Microsoft",
        location="Hyderabad, India",
        url="https://careers.microsoft.com/",
        description=(
            "Build AI and machine learning applications using Python, "
            "LLMs, APIs, and cloud technologies. "
            "Experience: 0-1 years. Entry-level opportunity."
        ),
        source="Microsoft Careers",
    ),
    JobListing(
        id="JOB003",
        title="Python Developer",
        company="Amazon",
        location="Chennai, India",
        url="https://www.amazon.jobs/",
        description=(
            "Develop backend services using Python, FastAPI, SQL databases, "
            "REST APIs, and cloud infrastructure. "
            "Experience: 1-2 years."
        ),
        source="Amazon Jobs",
    ),
    JobListing(
        id="JOB004",
        title="Machine Learning Engineer",
        company="Adobe",
        location="Remote",
        url="https://careers.adobe.com/",
        description=(
            "Develop machine learning models and AI-powered solutions "
            "using Python, ML fundamentals, and data processing. "
            "Experience: 1-2 years."
        ),
        source="Adobe Careers",
    ),
]


@router.get("/")
def get_jobs(
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    experience: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    filtered_jobs = SAMPLE_JOBS.copy()

    if search:
        keyword = search.lower()

        filtered_jobs = [
            job
            for job in filtered_jobs
            if keyword in job.title.lower()
            or keyword in job.company.lower()
            or keyword in job.description.lower()
        ]

    if role:
        role_keyword = role.lower()

        filtered_jobs = [
            job
            for job in filtered_jobs
            if role_keyword in job.title.lower()
        ]

    if location:
        location_keyword = location.lower()

        filtered_jobs = [
            job
            for job in filtered_jobs
            if location_keyword in job.location.lower()
        ]

    if experience:
        experience_keyword = experience.lower()

        filtered_jobs = [
            job
            for job in filtered_jobs
            if experience_keyword in job.description.lower()
        ]

    if source:
        source_keyword = source.lower()

        filtered_jobs = [
            job
            for job in filtered_jobs
            if source_keyword in job.source.lower()
        ]

    total = len(filtered_jobs)

    paginated_jobs = filtered_jobs[offset:offset + limit]

    return {
        "jobs": [job.model_dump() for job in paginated_jobs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
