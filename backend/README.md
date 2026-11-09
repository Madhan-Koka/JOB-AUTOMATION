# Job Automation Platform — Phase 1 Backend

This starter retains the existing parser/scraper/tailor/applier/logger modules and adds a FastAPI layer for:
- resume upload and parsing
- generic candidate profile extraction
- candidate profile retrieval and editing
- SQLite persistence for local development

## Setup (Windows PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Open:
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## APIs

- `POST /api/v1/resumes/upload` — multipart upload (PDF/TXT/MD, max 5 MB)
- `GET /api/v1/profile` — retrieve current local candidate profile
- `PUT /api/v1/profile` — update candidate fields
- `GET /health` — API health check

## Important

- This is a local single-user development baseline. Authentication and per-user data isolation are not implemented yet.
- Resume parsing uses conservative regex/keyword extraction. Name and skill extraction can be imperfect; the profile should be reviewed by the user.
- SQLite is used to reduce setup friction. Move to PostgreSQL and migrations before multi-user deployment.
- The current upload endpoint stores files locally. Configure private object storage and retention/deletion controls for deployment.
- No applications are submitted by these new endpoints. Keep human review and approval before any external application submission.
- Never commit `.env`, credentials, or resumes to Git.
