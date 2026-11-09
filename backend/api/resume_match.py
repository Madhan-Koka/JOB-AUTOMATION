
import os
import json
import time
import logging
from io import BytesIO

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from google import genai
from google.genai import types, errors
from pypdf import PdfReader

load_dotenv(override=True)

router = APIRouter()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing from backend .env")

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-3.5-flash-lite"
MAX_RETRIES = 3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResumeMatchRequest(BaseModel):
    resume_text: str
    job_description: str


def generate_gemini_response(prompt: str):
    """
    Generate Gemini response with retries for temporary
    service unavailable and rate limit errors.
    """

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )

            return response.text

        except errors.APIError as e:
            status_code = getattr(e, "code", None)

            # Retry only temporary errors
            if status_code in [429, 500, 502, 503, 504]:
                if attempt < MAX_RETRIES - 1:
                    wait_time = 2 ** (attempt + 1)

                    logger.warning(
                        "Gemini API error %s. "
                        "Retrying in %s seconds. Attempt %s/%s",
                        status_code,
                        wait_time,
                        attempt + 1,
                        MAX_RETRIES,
                    )

                    time.sleep(wait_time)
                    continue

                logger.error(
                    "Gemini API failed after %s attempts: %s",
                    MAX_RETRIES,
                    e,
                )

                raise HTTPException(
                    status_code=503,
                    detail=(
                        "Gemini AI service is temporarily busy. "
                        "Please try again in a few minutes."
                    ),
                )

            logger.error("Gemini API error: %s", e)

            raise HTTPException(
                status_code=500,
                detail=f"Gemini API error: {e.message}",
            )

    raise HTTPException(
        status_code=503,
        detail="Gemini service unavailable. Please try again later.",
    )


@router.post("/")
async def analyze_resume(request: ResumeMatchRequest):

    if not request.resume_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Resume text cannot be empty.",
        )

    if not request.job_description.strip():
        raise HTTPException(
            status_code=400,
            detail="Job description cannot be empty.",
        )

    prompt = f"""
You are an expert ATS resume analyzer and technical recruiter.

Analyze the resume against the job description.

RESUME:
{request.resume_text}

JOB DESCRIPTION:
{request.job_description}

Return ONLY valid JSON using this exact structure:

{{
    "match_percentage": 0,
    "match_level": "Low",
    "matched_skills": [],
    "missing_skills": [],
    "experience_analysis": "",
    "project_analysis": "",
    "ats_keyword_analysis": {{
        "matched_keywords": [],
        "missing_keywords": [],
        "keyword_match_percentage": 0
    }},
    "recommendations": [],
    "strengths": [],
    "improvement_areas": []
}}

Instructions:
- Match percentage must be between 0 and 100.
- Match level should be Low, Medium, or High.
- Identify relevant technical and non-technical skills.
- Analyze experience relevance.
- Analyze project relevance.
- Identify missing ATS keywords.
- Give actionable resume improvement suggestions.
- Do not invent experience or skills.
- Return valid JSON only.
"""

    try:
        response_text = generate_gemini_response(prompt)

        result = json.loads(response_text)

        # Ensure percentage stays within valid range
        result["match_percentage"] = max(
            0,
            min(100, int(result.get("match_percentage", 0))),
        )

        return result

    except json.JSONDecodeError:
        logger.exception("Gemini returned invalid JSON")

        raise HTTPException(
            status_code=500,
            detail="Gemini returned an invalid response. Please retry.",
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception("Unexpected resume analysis error")

        raise HTTPException(
            status_code=500,
            detail="Unexpected error during resume analysis.",
        )


@router.post("/upload-pdf")
async def upload_resume_pdf(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    pdf_bytes = await file.read()

    if len(pdf_bytes) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="PDF file must be smaller than 5 MB.",
        )

    try:
        pdf_reader = PdfReader(BytesIO(pdf_bytes))

        extracted_text = ""

        for page in pdf_reader.pages:
            page_text = page.extract_text()

            if page_text:
                extracted_text += page_text + "\n"

        extracted_text = extracted_text.strip()

        if not extracted_text:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No text could be extracted from this PDF. "
                    "It may be a scanned document requiring OCR."
                ),
            )

        return {
            "filename": file.filename,
            "resume_text": extracted_text,
            "message": "Resume text extracted successfully.",
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception("PDF extraction failed")

        raise HTTPException(
            status_code=500,
            detail="Failed to extract text from PDF.",
        )
