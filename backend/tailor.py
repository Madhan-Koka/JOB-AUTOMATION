
"""
tailor.py - Tailors resume content and generates customized application text.
"""

from pathlib import Path
import re

from parser import CandidateProfile, JobListing, ApplicationPayload


class ApplicationTailor:
    def __init__(self, output_dir: str | Path = "tailored_outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def find_matching_skills(
        self,
        profile: CandidateProfile,
        job: JobListing,
    ) -> list[str]:
        """Find candidate skills mentioned in the job description."""

        job_text = job.description.lower()

        matched_skills = [
            skill
            for skill in profile.skills
            if skill.strip() and skill.lower() in job_text
        ]

        return matched_skills

    def generate_tailored_summary(
        self,
        profile: CandidateProfile,
        job: JobListing,
    ) -> str:
        """Generate a job-focused summary using only candidate-provided skills."""

        matched_skills = self.find_matching_skills(profile, job)

        if matched_skills:
            skills_text = ", ".join(matched_skills)

            summary = (
                f"Candidate profile aligned with the {job.title} role, "
                f"highlighting relevant skills in {skills_text}. "
                f"Interested in contributing these skills to "
                f"{job.company}'s engineering team."
            )
        else:
            available_skills = profile.skills[:5]

            if available_skills:
                skills_text = ", ".join(available_skills)

                summary = (
                    f"Candidate profile for the {job.title} role, "
                    f"with skills including {skills_text}. "
                    f"Interested in contributing to "
                    f"{job.company}'s engineering team."
                )
            else:
                summary = (
                    f"Candidate profile targeting the {job.title} role "
                    f"at {job.company}."
                )

        return summary

    def generate_tailored_resume(
        self,
        profile: CandidateProfile,
        job: JobListing,
        original_resume_path: Path,
    ) -> Path:
        """
        Create a separate tailored resume text file.

        The original resume content is preserved. A job-specific summary
        and matched skills section are added at the beginning.
        """

        original_resume_path = Path(original_resume_path)

        if not original_resume_path.exists():
            raise FileNotFoundError(
                f"Original resume not found: {original_resume_path}"
            )

        raw_resume_text = profile.raw_resume_text.strip()

        if not raw_resume_text:
            if original_resume_path.suffix.lower() in [".txt", ".md"]:
                raw_resume_text = original_resume_path.read_text(
                    encoding="utf-8"
                ).strip()
            else:
                from parser import parse_resume

                raw_resume_text = parse_resume(original_resume_path)

        tailored_summary = self.generate_tailored_summary(profile, job)
        matched_skills = self.find_matching_skills(profile, job)

        skills_section = (
            ", ".join(matched_skills)
            if matched_skills
            else "No direct skill matches identified"
        )

        tailored_resume_text = (
            "PROFESSIONAL SUMMARY\n"
            f"{tailored_summary}\n\n"
            "JOB-RELEVANT SKILLS\n"
            f"{skills_section}\n\n"
            "ORIGINAL RESUME CONTENT\n"
            "----------------------\n"
            f"{raw_resume_text}\n"
        )

        safe_company = re.sub(
            r"[^a-zA-Z0-9_-]",
            "_",
            job.company.strip(),
        )

        safe_job_id = re.sub(
            r"[^a-zA-Z0-9_-]",
            "_",
            job.id.strip(),
        )

        resume_file = (
            self.output_dir
            / f"TailoredResume_{safe_company}_{safe_job_id}.txt"
        )

        resume_file.write_text(
            tailored_resume_text,
            encoding="utf-8",
        )

        return resume_file

    def generate_cover_letter(
        self,
        profile: CandidateProfile,
        job: JobListing,
    ) -> str:
        """Generate a customized cover letter using matching skills."""

        matched_skills = self.find_matching_skills(profile, job)

        if matched_skills:
            skills_summary = ", ".join(matched_skills)
            skills_sentence = (
                f"My background includes skills in {skills_summary}, "
                "which are relevant to this position."
            )
        else:
            skills_summary = ", ".join(profile.skills[:4])

            if skills_summary:
                skills_sentence = (
                    f"My technical skills include {skills_summary}. "
                    "I am interested in applying them in this role."
                )
            else:
                skills_sentence = (
                    "I am interested in contributing to this position "
                    "and continuing to develop my professional skills."
                )

        cover_letter = (
            f"Dear Hiring Team at {job.company},\n\n"
            f"I am writing to express my interest in the "
            f"{job.title} position.\n\n"
            f"{skills_sentence}\n\n"
            f"I am interested in the opportunity to contribute to "
            f"{job.company} and further develop my skills while "
            f"supporting the team's goals.\n\n"
            f"Thank you for considering my application. "
            f"I look forward to the opportunity to discuss "
            f"my qualifications.\n\n"
            f"Sincerely,\n"
            f"{profile.full_name}\n"
            f"Email: {profile.email}\n"
            f"Phone: {profile.phone}\n"
        )

        if profile.linkedin:
            cover_letter += f"LinkedIn: {profile.linkedin}\n"

        if profile.github:
            cover_letter += f"GitHub: {profile.github}\n"

        if profile.portfolio:
            cover_letter += f"Portfolio: {profile.portfolio}\n"

        return cover_letter

    def create_tailored_artifacts(
        self,
        profile: CandidateProfile,
        job: JobListing,
        original_resume_path: Path,
    ) -> ApplicationPayload:
        """Create a tailored resume and cover letter."""

        tailored_resume_path = self.generate_tailored_resume(
            profile=profile,
            job=job,
            original_resume_path=original_resume_path,
        )

        cover_letter_text = self.generate_cover_letter(
            profile=profile,
            job=job,
        )

        safe_company = re.sub(
            r"[^a-zA-Z0-9_-]",
            "_",
            job.company.strip(),
        )

        safe_job_id = re.sub(
            r"[^a-zA-Z0-9_-]",
            "_",
            job.id.strip(),
        )

        cover_letter_file = (
            self.output_dir
            / f"CoverLetter_{safe_company}_{safe_job_id}.txt"
        )

        cover_letter_file.write_text(
            cover_letter_text,
            encoding="utf-8",
        )

        return ApplicationPayload(
            job=job,
            tailored_resume_path=tailored_resume_path,
            cover_letter=cover_letter_text,
            status="PREPARED",
            notes=(
                f"Tailored resume stored at {tailored_resume_path.name}. "
                f"Cover letter stored at {cover_letter_file.name}. "
                "Generated artifacts require candidate review."
            ),
        )
