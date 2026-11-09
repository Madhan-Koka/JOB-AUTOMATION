
import { useState } from "react";

const API_URL = "http://localhost:8000/api/v1/resume-match/";
const UPLOAD_URL = "http://localhost:8000/api/v1/resume-match/upload-pdf";

function ResumeMatch() {
  const [resumeText, setResumeText] = useState("");
  const [jobDescription, setJobDescription] = useState("");

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [uploadMessage, setUploadMessage] = useState("");

  const getErrorMessage = async (response, fallbackMessage) => {
    try {
      const data = await response.json();

      if (typeof data.detail === "string") {
        return data.detail;
      }

      if (Array.isArray(data.detail)) {
        return data.detail
          .map((item) => item.msg || "Validation error")
          .join(", ");
      }

      return fallbackMessage;
    } catch {
      return fallbackMessage;
    }
  };

  const handlePdfUpload = async (event) => {
    const file = event.target.files?.[0];

    if (!file) return;

    setError("");
    setUploadMessage("");
    setResult(null);

    if (file.type !== "application/pdf") {
      setError("Please select a PDF file.");
      event.target.value = "";
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setError("PDF file size must be less than 5 MB.");
      event.target.value = "";
      return;
    }

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(UPLOAD_URL, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const message = await getErrorMessage(
          response,
          "PDF upload failed."
        );
        throw new Error(message);
      }

      let data;

      try {
        data = await response.json();
      } catch {
        throw new Error("The backend returned an invalid response.");
      }

      if (typeof data.resume_text !== "string") {
        throw new Error("Resume text was not found in the response.");
      }

      setResumeText(data.resume_text);

      setUploadMessage(
        `Successfully extracted text from ${data.filename || file.name}`
      );
    } catch (err) {
      setError(err.message || "Unable to upload PDF.");
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  };

  const analyzeResume = async () => {
    if (!resumeText.trim() || !jobDescription.trim()) {
      setError("Please provide your resume and job description.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          resume_text: resumeText,
          job_description: jobDescription,
        }),
      });

      if (!response.ok) {
        const message = await getErrorMessage(
          response,
          "Resume analysis failed."
        );
        throw new Error(message);
      }

      let data;

      try {
        data = await response.json();
      } catch {
        throw new Error("The backend returned an invalid response.");
      }

      setResult(data);
    } catch (err) {
      setError(err.message || "Unable to connect to the backend.");
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return "#16a34a";
    if (score >= 60) return "#ca8a04";
    return "#dc2626";
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.heading}>AI Resume Match Analyzer</h1>

      <p style={styles.subtitle}>Powered by Google Gemini AI</p>

      <div style={styles.inputSection}>
        <label style={styles.label}>Upload Resume PDF</label>

        <input
          type="file"
          accept=".pdf,application/pdf"
          onChange={handlePdfUpload}
          disabled={uploading || loading}
          style={styles.fileInput}
        />

        {uploading && (
          <p style={styles.info}>Extracting resume text...</p>
        )}

        {uploadMessage && (
          <p style={styles.success}>{uploadMessage}</p>
        )}

        <label style={styles.label}>Resume Text</label>

        <textarea
          style={styles.textarea}
          placeholder="Upload your PDF or paste your resume text here..."
          value={resumeText}
          onChange={(e) => setResumeText(e.target.value)}
          rows={12}
        />

        <label style={styles.label}>Job Description</label>

        <textarea
          style={styles.textarea}
          placeholder="Paste the complete job description here..."
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          rows={12}
        />

        <button
          style={{
            ...styles.button,
            opacity: loading || uploading ? 0.6 : 1,
          }}
          onClick={analyzeResume}
          disabled={
            loading ||
            uploading ||
            !resumeText.trim() ||
            !jobDescription.trim()
          }
        >
          {loading ? "Analyzing with Gemini..." : "Analyze Resume"}
        </button>
      </div>

      {error && <div style={styles.error}>{error}</div>}

      {result && (
        <div style={styles.results}>
          <h2 style={styles.resultHeading}>
            Resume Analysis Results
          </h2>

          <div style={styles.scoreCard}>
            <div
              style={{
                ...styles.score,
                color: getScoreColor(
                  Number(result.match_percentage ?? 0)
                ),
              }}
            >
              {result.match_percentage ?? 0}%
            </div>

            <h3>{result.match_level || "Match Analysis"}</h3>

            <p>Resume Match Score</p>
          </div>

          <section style={styles.section}>
            <h3>Matched Skills</h3>

            <div style={styles.skillContainer}>
              {result.matched_skills?.length > 0 ? (
                result.matched_skills.map((skill, index) => (
                  <span key={index} style={styles.matchedSkill}>
                    {skill}
                  </span>
                ))
              ) : (
                <p>No matched skills identified.</p>
              )}
            </div>
          </section>

          <section style={styles.section}>
            <h3>Missing Skills</h3>

            <div style={styles.skillContainer}>
              {result.missing_skills?.length > 0 ? (
                result.missing_skills.map((skill, index) => (
                  <span key={index} style={styles.missingSkill}>
                    {skill}
                  </span>
                ))
              ) : (
                <p>No missing skills identified.</p>
              )}
            </div>
          </section>

          <section style={styles.section}>
            <h3>Experience Analysis</h3>
            <p>
              {result.experience_analysis ||
                "No experience analysis available."}
            </p>
          </section>

          <section style={styles.section}>
            <h3>Project Analysis</h3>
            <p>
              {result.project_analysis ||
                "No project analysis available."}
            </p>
          </section>

          <section style={styles.section}>
            <h3>ATS Keyword Analysis</h3>

            <p>
              Keyword Match Percentage:{" "}
              {result.ats_keyword_analysis
                ?.keyword_match_percentage ?? 0}%
            </p>

            <div>
              <h4>Matched Keywords</h4>

              <ul>
                {(
                  result.ats_keyword_analysis?.matched_keywords ?? []
                ).map((keyword, index) => (
                  <li key={index}>{keyword}</li>
                ))}
              </ul>
            </div>

            <div>
              <h4>Missing Keywords</h4>

              <ul>
                {(
                  result.ats_keyword_analysis?.missing_keywords ?? []
                ).map((keyword, index) => (
                  <li key={index}>{keyword}</li>
                ))}
              </ul>
            </div>
          </section>

          <section style={styles.section}>
            <h3>Strengths</h3>

            <ul>
              {result.strengths?.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          </section>

          <section style={styles.section}>
            <h3>Improvement Areas</h3>

            <ul>
              {result.improvement_areas?.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          </section>

          <section style={styles.section}>
            <h3>Recommendations</h3>

            <ul>
              {result.recommendations?.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          </section>
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    maxWidth: "1000px",
    margin: "30px auto",
    padding: "20px",
    fontFamily: "Arial, sans-serif",
  },
  heading: {
    textAlign: "center",
    color: "#1e293b",
  },
  subtitle: {
    textAlign: "center",
    color: "#64748b",
    marginBottom: "30px",
  },
  inputSection: {
    background: "#f8fafc",
    padding: "25px",
    borderRadius: "12px",
    border: "1px solid #e2e8f0",
  },
  label: {
    display: "block",
    fontWeight: "bold",
    marginBottom: "10px",
    marginTop: "15px",
    color: "#334155",
  },
  fileInput: {
    display: "block",
    width: "100%",
    padding: "12px",
    background: "#ffffff",
    border: "1px solid #cbd5e1",
    borderRadius: "8px",
    boxSizing: "border-box",
  },
  textarea: {
    width: "100%",
    boxSizing: "border-box",
    padding: "12px",
    border: "1px solid #cbd5e1",
    borderRadius: "8px",
    fontSize: "14px",
    resize: "vertical",
    marginBottom: "15px",
  },
  button: {
    width: "100%",
    padding: "14px",
    background: "#2563eb",
    color: "white",
    border: "none",
    borderRadius: "8px",
    fontSize: "16px",
    fontWeight: "bold",
    cursor: "pointer",
    marginTop: "10px",
  },
  error: {
    background: "#fee2e2",
    color: "#b91c1c",
    padding: "15px",
    borderRadius: "8px",
    marginTop: "20px",
  },
  success: {
    color: "#166534",
    background: "#dcfce7",
    padding: "10px",
    borderRadius: "8px",
  },
  info: {
    color: "#1d4ed8",
  },
  results: {
    marginTop: "30px",
    padding: "20px",
    border: "1px solid #e2e8f0",
    borderRadius: "12px",
    background: "#ffffff",
  },
  resultHeading: {
    textAlign: "center",
    color: "#1e293b",
  },
  scoreCard: {
    textAlign: "center",
    background: "#f8fafc",
    padding: "25px",
    borderRadius: "12px",
    margin: "20px 0",
  },
  score: {
    fontSize: "56px",
    fontWeight: "bold",
  },
  section: {
    marginTop: "25px",
    padding: "15px",
    background: "#f8fafc",
    borderRadius: "8px",
    lineHeight: "1.6",
  },
  skillContainer: {
    display: "flex",
    flexWrap: "wrap",
    gap: "10px",
  },
  matchedSkill: {
    background: "#dcfce7",
    color: "#166534",
    padding: "6px 12px",
    borderRadius: "20px",
    fontSize: "14px",
  },
  missingSkill: {
    background: "#fee2e2",
    color: "#991b1b",
    padding: "6px 12px",
    borderRadius: "20px",
    fontSize: "14px",
  },
};

export default ResumeMatch;
