
import re
from pathlib import Path
from typing import Any

from parser import parse_resume


# Skills recognized by the resume parser.
KNOWN_SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "SQL", "PostgreSQL", "MySQL",
    "FastAPI", "Django", "Flask", "React", "Node.js", "REST API", "AWS",
    "Azure", "Docker", "Kubernetes", "Git", "Machine Learning", "Pandas",
    "NumPy", "Playwright", "Selenium", "HTML", "CSS", "Linux", "Jenkins",
    "Redis", "LangChain", "LLM", "RAG", "Prompt Engineering"
]


# Email extraction.
EMAIL_RE = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.IGNORECASE
)


# Indian mobile number extraction.
# Supports:
# 7893499335
# +91 7893499335
# +91-7893499335
# 91 7893499335
PHONE_RE = re.compile(
    r"(?<!\d)(?:\+91[\s-]?|91[\s-]?)?[6-9]\d{9}(?!\d)"
)


# URL extraction.
URL_RE = re.compile(
    r"https?://[^\s|,;]+",
    re.IGNORECASE
)


def extract_candidate_data(file_path: Path) -> dict[str, Any]:
    """Extract candidate details and skills from a resume."""

    text = parse_resume(file_path)

    emails = EMAIL_RE.findall(text)
    phones = PHONE_RE.findall(text)
    urls = URL_RE.findall(text)

    linkedin = next(
        (url for url in urls if "linkedin.com" in url.lower()),
        None
    )

    github = next(
        (url for url in urls if "github.com" in url.lower()),
        None
    )

    portfolio = next(
        (
            url for url in urls
            if "linkedin.com" not in url.lower()
            and "github.com" not in url.lower()
        ),
        None
    )

    # Skill extraction.
    found_skills = []
    lowered = text.lower()

    for skill in KNOWN_SKILLS:
        if skill.lower() in lowered:
            found_skills.append(skill)

    # Conservative name extraction.
    first_nonempty = next(
        (line.strip() for line in text.splitlines() if line.strip()),
        ""
    )

    possible_name = (
        first_nonempty[:200]
        if len(first_nonempty.split()) <= 5
        and "@" not in first_nonempty
        else ""
    )

    # Normalize phone number.
    extracted_phone = phones[0].strip() if phones else ""

    return {
        "full_name": possible_name,
        "email": emails[0] if emails else "",
        "phone": extracted_phone,
        "linkedin": linkedin,
        "github": github,
        "portfolio": portfolio,
        "skills": found_skills,
        "raw_resume_text": text,
    }
