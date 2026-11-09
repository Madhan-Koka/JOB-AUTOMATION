import { useEffect, useState } from "react";
import "./App.css";
import ResumeMatch from "./ResumeMatch";

const API = "http://localhost:8000";

const APPLICATION_STATUS_OPTIONS = [
  "Saved",
  "Applied",
  "Interview",
  "Rejected",
  "Offer",
];

function App() {
  const [profile, setProfile] = useState(null);
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const [jobs, setJobs] = useState([]);
  const [jobsLoading, setJobsLoading] = useState(true);
  const [jobsError, setJobsError] = useState("");

  // Job search and filter state
  const [searchTerm, setSearchTerm] = useState("");
  const [locationFilter, setLocationFilter] = useState("All Locations");

  // Application tracking filter
  const [applicationFilter, setApplicationFilter] =
    useState("All Statuses");

  // Application tracking data from backend
  const [applications, setApplications] = useState([]);
  const [applicationsLoading, setApplicationsLoading] = useState(true);
  const [applicationsError, setApplicationsError] = useState("");

  // Load saved jobs from localStorage
  const [savedJobs, setSavedJobs] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("jobpilot_saved_jobs")) || [];
    } catch {
      return [];
    }
  });

  // Fetch candidate profile
  useEffect(() => {
    fetch(`${API}/api/v1/profile`)
      .then((res) => {
        if (!res.ok) {
          throw new Error("Unable to fetch profile");
        }
        return res.json();
      })
      .then(setProfile)
      .catch(() => setMessage("Backend is not reachable."));
  }, []);

  // Fetch jobs from Jobs API
  useEffect(() => {
    fetch(`${API}/api/v1/jobs/`)
      .then((res) => {
        if (!res.ok) {
          throw new Error("Unable to fetch jobs");
        }
        return res.json();
      })
      .then((data) => {
        setJobs(data.jobs || []);
      })
      .catch(() => {
        setJobsError("Unable to load jobs. Please check the backend.");
      })
      .finally(() => {
        setJobsLoading(false);
      });
  }, []);

  // Fetch applications from backend database
  useEffect(() => {
    async function fetchApplications() {
      try {
        const res = await fetch(`${API}/api/v1/applications`);

        if (!res.ok) {
          throw new Error("Unable to load applications");
        }

        const data = await res.json();
        setApplications(data);
      } catch (error) {
        setApplicationsError(error.message);
      } finally {
        setApplicationsLoading(false);
      }
    }

    fetchApplications();
  }, []);

  // Save shortlist to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem(
      "jobpilot_saved_jobs",
      JSON.stringify(savedJobs)
    );
  }, [savedJobs]);

  // Upload resume
  async function uploadResume() {
    if (!file) {
      setMessage("Please select a PDF resume.");
      return;
    }

    setLoading(true);
    setMessage("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API}/api/v1/resumes/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Upload failed");
      }

      setProfile(data.profile);
      setMessage("Resume uploaded and parsed successfully!");
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  // Get a unique identifier for each job
  function getJobId(job) {
    return String(job.id || job.url || job.title);
  }

  // Get unique job locations
  const locations = [
    "All Locations",
    ...new Set(jobs.map((job) => job.location).filter(Boolean)),
  ];

  // Filter jobs based on search and location
  const filteredJobs = jobs.filter((job) => {
    const search = searchTerm.toLowerCase();

    const matchesSearch =
      (job.title || "").toLowerCase().includes(search) ||
      (job.company || "").toLowerCase().includes(search);

    const matchesLocation =
      locationFilter === "All Locations" ||
      job.location === locationFilter;

    return matchesSearch && matchesLocation;
  });

  // Clear all job filters
  function clearFilters() {
    setSearchTerm("");
    setLocationFilter("All Locations");
  }

  // Add or remove a job from shortlist
  function toggleSaveJob(job) {
    const jobId = getJobId(job);

    const isSaved = savedJobs.some(
      (savedJob) => getJobId(savedJob) === jobId
    );

    if (isSaved) {
      setSavedJobs((previousJobs) =>
        previousJobs.filter(
          (savedJob) => getJobId(savedJob) !== jobId
        )
      );
    } else {
      setSavedJobs((previousJobs) => [...previousJobs, job]);
    }
  }

  // Check whether a job is saved
  function isJobSaved(job) {
    const jobId = getJobId(job);

    return savedJobs.some(
      (savedJob) => getJobId(savedJob) === jobId
    );
  }

  // Find application record for a job
  function findApplication(job) {
    return applications.find(
      (application) =>
        (job.url && application.job_url === job.url) ||
        (
          application.job_title === job.title &&
          application.company === job.company
        )
    );
  }

  // Get application status for a job
  function getApplicationStatus(job) {
    return findApplication(job)?.status || "Saved";
  }

  // Create or update application status using backend
  async function updateApplicationStatus(job, newStatus) {
    const existing = findApplication(job);

    const payload = {
      job_title: job.title || "",
      company: job.company || "",
      location: job.location || "",
      job_url: job.url || "",
      status: newStatus,
      applied_date:
        existing?.applied_date ||
        (newStatus !== "Saved"
          ? new Date().toISOString().split("T")[0]
          : null),
      notes: existing?.notes || "",
    };

    try {
      const res = await fetch(
        existing
          ? `${API}/api/v1/applications/${existing.id}`
          : `${API}/api/v1/applications`,
        {
          method: existing ? "PUT" : "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        }
      );

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to save application");
      }

      const savedApplication = await res.json();

      setApplications((previous) =>
        existing
          ? previous.map((application) =>
              application.id === savedApplication.id
                ? savedApplication
                : application
            )
          : [...previous, savedApplication]
      );

      setApplicationsError("");

      // Automatically add tracked jobs to shortlist
      setSavedJobs((previousJobs) => {
        const alreadySaved = previousJobs.some(
          (savedJob) => getJobId(savedJob) === getJobId(job)
        );

        if (alreadySaved) {
          return previousJobs;
        }

        return [...previousJobs, job];
      });
    } catch (error) {
      setApplicationsError(error.message);
    }
  }

  // Update application date or notes using backend
  async function updateApplicationField(application, field, value) {
    const backendField =
      field === "applicationDate" ? "applied_date" : field;

    const updatedApplication = {
      ...application,
      [backendField]: value || null,
    };

    // Update UI immediately
    setApplications((previous) =>
      previous.map((item) =>
        item.id === application.id ? updatedApplication : item
      )
    );

    try {
      const res = await fetch(
        `${API}/api/v1/applications/${application.id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            [backendField]: value || null,
          }),
        }
      );

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to update application");
      }

      const savedApplication = await res.json();

      setApplications((previous) =>
        previous.map((item) =>
          item.id === savedApplication.id
            ? savedApplication
            : item
        )
      );

      setApplicationsError("");
    } catch (error) {
      setApplicationsError(error.message);
    }
  }

  // Delete application from backend database
  async function deleteApplication(application) {
    try {
      const res = await fetch(
        `${API}/api/v1/applications/${application.id}`,
        {
          method: "DELETE",
        }
      );

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to delete application");
      }

      setApplications((previous) =>
        previous.filter((item) => item.id !== application.id)
      );

      setApplicationsError("");
    } catch (error) {
      setApplicationsError(error.message);
    }
  }

  // Get all tracked applications
  const trackedApplications = applications.map((application) => ({
    ...application,
    applicationDate: application.applied_date || "",
    job: {
      id: application.id,
      title: application.job_title,
      company: application.company,
      location: application.location,
      url: application.job_url,
    },
  }));

  // Filter tracked applications by status
  const filteredApplications = trackedApplications.filter(
    (application) =>
      applicationFilter === "All Statuses" ||
      application.status === applicationFilter
  );

  // Dashboard counts
  const totalApplications = trackedApplications.filter(
    (application) => application.status !== "Saved"
  ).length;

  const totalInterviews = trackedApplications.filter(
    (application) => application.status === "Interview"
  ).length;

  const totalOffers = trackedApplications.filter(
    (application) => application.status === "Offer"
  ).length;

  const totalRejected = trackedApplications.filter(
    (application) => application.status === "Rejected"
  ).length;

  return (
    <div className="app">
      <aside className="sidebar">
        <h2 className="brand">✦ JobPilot</h2>

        <p className="menu-label">WORKSPACE</p>

        <a className="nav active" href="#dashboard">
          ▦ Dashboard
        </a>

        <a className="nav" href="#resume">
          ▤ Resume Manager
        </a>

        <a className="nav" href="#resume-match">
          ✨ Resume Match Analyzer
        </a>

        <a className="nav" href="#jobs">
          ⌕ Job Search
        </a>

        <a className="nav" href="#shortlist">
          ⭐ My Shortlist
        </a>

        <a className="nav" href="#applications">
          ▣ Applications
        </a>

        <a className="nav" href="#profile">
          ♙ My Profile
        </a>

        <div className="sidebar-footer">
          <div className="avatar">KM</div>
          <div>
            <strong>Koka Madhan</strong>
            <small>Candidate</small>
          </div>
        </div>
      </aside>

      <main className="main" id="dashboard">
        <header className="topbar">
          <div>
            <small>Workspace / Dashboard</small>
            <h2>Dashboard</h2>
          </div>

          <span className="connected">● Backend connected</span>
        </header>

        <section className="welcome">
          <div>
            <span className="eyebrow">YOUR CAREER WORKSPACE</span>
            <h1>Welcome back, Madhan! 👋</h1>
            <p>
              Manage your resume and prepare for your next career move.
            </p>
          </div>

          <span className="rocket">🚀</span>
        </section>

        {/* Dashboard statistics */}
        <section className="stats">
          <div className="stat">
            <span>▤</span>
            <p>Resumes Uploaded</p>
            <h2>{profile?.resume_filename ? 1 : 0}</h2>
          </div>

          <div className="stat">
            <span>⌕</span>
            <p>Jobs Discovered</p>
            <h2>{jobs.length}</h2>
          </div>

          <div className="stat">
            <span>▣</span>
            <p>Applications</p>
            <h2>{totalApplications}</h2>
          </div>

          <div className="stat">
            <span>🎯</span>
            <p>Interviews</p>
            <h2>{totalInterviews}</h2>
          </div>

          <div className="stat">
            <span>🎉</span>
            <p>Offers</p>
            <h2>{totalOffers}</h2>
          </div>

          <div className="stat">
            <span>❌</span>
            <p>Rejected</p>
            <h2>{totalRejected}</h2>
          </div>

          <div className="stat">
            <span>✦</span>
            <p>Profile Skills</p>
            <h2>{profile?.skills?.length || 0}</h2>
          </div>
        </section>

        {/* Resume and Profile */}
        <section className="columns">
          <div className="panel" id="resume">
            <h3>Resume Manager</h3>

            <p className="muted">
              Upload your resume to get started
            </p>

            <div className="upload-box">
              <div className="upload-icon">↑</div>

              <h3>Upload your resume</h3>

              <p className="muted">
                Choose a PDF file from your computer
              </p>

              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setFile(e.target.files[0])}
              />

              {file && <p>{file.name}</p>}

              <button onClick={uploadResume} disabled={loading}>
                {loading ? "Uploading..." : "Upload & Parse Resume"}
              </button>

              {message && <p className="message">{message}</p>}
            </div>

            {profile?.resume_filename && (
              <div className="file-row">
                <span className="pdf">PDF</span>

                <div>
                  <strong>{profile.resume_filename}</strong>
                  <small>Resume uploaded</small>
                </div>

                <span className="parsed">Parsed</span>
              </div>
            )}
          </div>

          <div className="panel" id="profile">
            <h3>Candidate Profile</h3>

            <p className="muted">
              Information extracted from your resume
            </p>

            <div className="details">
              <label>Full Name</label>
              <strong>{profile?.full_name || "Not available"}</strong>

              <label>Email</label>
              <strong>{profile?.email || "Not extracted"}</strong>

              <label>Phone</label>
              <strong>{profile?.phone || "Not extracted"}</strong>
            </div>

            <label className="skill-label">Technical Skills</label>

            <div className="skills">
              {profile?.skills?.map((skill) => (
                <span key={skill}>{skill}</span>
              ))}
            </div>
          </div>
        </section>

        {/* Resume Match Analyzer */}
        <section id="resume-match">
          <ResumeMatch />
        </section>

        {/* Recommended Jobs */}
        <section className="panel" id="jobs">
          <h3>Recommended Jobs</h3>

          <p className="muted">
            Search and filter jobs retrieved from your backend API
          </p>

          <div className="job-filters">
            <input
              type="text"
              placeholder="Search job title or company..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />

            <select
              value={locationFilter}
              onChange={(e) => setLocationFilter(e.target.value)}
            >
              {locations.map((location) => (
                <option key={location} value={location}>
                  {location}
                </option>
              ))}
            </select>

            <button onClick={clearFilters}>Clear Filters</button>
          </div>

          <p className="muted">
            Showing {filteredJobs.length} of {jobs.length} jobs
          </p>

          {jobsLoading && <p className="muted">Loading jobs...</p>}

          {jobsError && <p className="message">{jobsError}</p>}

          {!jobsLoading && !jobsError && jobs.length === 0 && (
            <div className="empty">
              <h3>No jobs available</h3>
              <p>Jobs will appear here when they are available.</p>
            </div>
          )}

          {!jobsLoading &&
            !jobsError &&
            jobs.length > 0 &&
            filteredJobs.length === 0 && (
              <div className="empty">
                <h3>No matching jobs found</h3>
                <p>Try changing your search or location filter.</p>
              </div>
            )}

          <div className="job-list">
            {filteredJobs.map((job, index) => (
              <div
                className="file-row job-row"
                key={getJobId(job) || index}
              >
                <div className="job-icon">💼</div>

                <div className="job-info">
                  <strong>{job.title}</strong>

                  <small>
                    {job.company} · {job.location}
                  </small>

                  <small>Source: {job.source || "Sample"}</small>

                  <small>
                    Current Status: {getApplicationStatus(job)}
                  </small>
                </div>

                <div className="job-actions">
                  <button
                    className="save-job"
                    onClick={() => toggleSaveJob(job)}
                  >
                    {isJobSaved(job) ? "★ Saved" : "☆ Save Job"}
                  </button>

                  <select
                    value={getApplicationStatus(job)}
                    onChange={(e) =>
                      updateApplicationStatus(job, e.target.value)
                    }
                    aria-label={`Application status for ${job.title}`}
                  >
                    {APPLICATION_STATUS_OPTIONS.map((status) => (
                      <option key={status} value={status}>
                        {status}
                      </option>
                    ))}
                  </select>

                  <a
                    className="job-apply"
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Apply
                  </a>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Saved Jobs / Shortlist */}
        <section className="panel" id="shortlist">
          <h3>My Shortlist ⭐</h3>

          <p className="muted">
            Jobs you have bookmarked for later
          </p>

          <p className="muted">{savedJobs.length} saved job(s)</p>

          {savedJobs.length === 0 && (
            <div className="empty">
              <span>☆</span>
              <h3>No saved jobs yet</h3>
              <p>
                Click Save Job on a listing to add it to your shortlist.
              </p>
            </div>
          )}

          <div className="job-list">
            {savedJobs.map((job, index) => (
              <div
                className="file-row job-row"
                key={getJobId(job) || index}
              >
                <div className="job-icon">⭐</div>

                <div className="job-info">
                  <strong>{job.title}</strong>

                  <small>
                    {job.company} · {job.location}
                  </small>

                  <small>Source: {job.source || "Sample"}</small>

                  <small>
                    Current Status: {getApplicationStatus(job)}
                  </small>
                </div>

                <div className="job-actions">
                  <button
                    className="save-job"
                    onClick={() => toggleSaveJob(job)}
                  >
                    Remove
                  </button>

                  <select
                    value={getApplicationStatus(job)}
                    onChange={(e) =>
                      updateApplicationStatus(job, e.target.value)
                    }
                    aria-label={`Application status for ${job.title}`}
                  >
                    {APPLICATION_STATUS_OPTIONS.map((status) => (
                      <option key={status} value={status}>
                        {status}
                      </option>
                    ))}
                  </select>

                  <a
                    className="job-apply"
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Apply
                  </a>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Application Tracking */}
        <section className="panel applications" id="applications">
          <h3>Application Tracking</h3>

          <p className="muted">
            Track your job application progress, dates, and notes
          </p>

          {applicationsLoading && (
            <p className="muted">Loading applications...</p>
          )}

          {applicationsError && (
            <p className="message">{applicationsError}</p>
          )}

          {/* Application statistics */}
          <div className="stats">
            <div className="stat">
              <p>Total Applied</p>
              <h2>{totalApplications}</h2>
            </div>

            <div className="stat">
              <p>Interviews</p>
              <h2>{totalInterviews}</h2>
            </div>

            <div className="stat">
              <p>Offers</p>
              <h2>{totalOffers}</h2>
            </div>

            <div className="stat">
              <p>Rejected</p>
              <h2>{totalRejected}</h2>
            </div>
          </div>

          {/* Application status filter */}
          <div className="job-filters">
            <select
              value={applicationFilter}
              onChange={(e) => setApplicationFilter(e.target.value)}
              aria-label="Filter applications by status"
            >
              <option value="All Statuses">All Statuses</option>

              {APPLICATION_STATUS_OPTIONS.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </div>

          <p className="muted">
            Showing {filteredApplications.length} of{" "}
            {trackedApplications.length} tracked job(s)
          </p>

          {trackedApplications.length === 0 && !applicationsLoading && (
            <div className="empty">
              <span>▣</span>
              <h3>No applications tracked yet</h3>
              <p>
                Select a status such as Applied or Interview from a job listing
                to start tracking it.
              </p>
            </div>
          )}

          {trackedApplications.length > 0 &&
            filteredApplications.length === 0 && (
              <div className="empty">
                <h3>No applications with this status</h3>
                <p>Choose another status from the filter.</p>
              </div>
            )}

          {/* Application cards */}
          <div className="application-list">
            {filteredApplications.map((application) => {
              const job = application.job;

              return (
                <div
                  className="application-card"
                  key={application.id}
                >
                  {/* Card heading */}
                  <div className="application-card-header">
                    <div className="application-company-icon">
                      📋
                    </div>

                    <div className="application-heading">
                      <h4>{job.title}</h4>

                      <p>
                        {job.company} <span>·</span> {job.location}
                      </p>
                    </div>

                    <span
                      className={`application-status-badge status-${application.status.toLowerCase()}`}
                    >
                      {application.status}
                    </span>
                  </div>

                  {/* Date and notes */}
                  <div className="application-card-body">
                    <div className="application-field">
                      <label>Application Date</label>

                      <input
                        type="date"
                        value={application.applicationDate || ""}
                        onChange={(e) =>
                          updateApplicationField(
                            application,
                            "applicationDate",
                            e.target.value
                          )
                        }
                      />
                    </div>

                    <div className="application-field">
                      <label>Application Notes</label>

                      <textarea
                        rows="3"
                        placeholder="Recruiter details, interview feedback, follow-up reminders..."
                        value={application.notes || ""}
                        onChange={(e) =>
                          updateApplicationField(
                            application,
                            "notes",
                            e.target.value
                          )
                        }
                      />
                    </div>
                  </div>

                  {/* Card actions */}
                  <div className="application-card-footer">
                    <select
                      value={application.status}
                      onChange={(e) =>
                        updateApplicationStatus(job, e.target.value)
                      }
                      aria-label={`Update status for ${job.title}`}
                    >
                      {APPLICATION_STATUS_OPTIONS.map((status) => (
                        <option key={status} value={status}>
                          {status}
                        </option>
                      ))}
                    </select>

                    <a
                      className="job-apply"
                      href={job.url || "#"}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      View Job ↗
                    </a>

                    <button
                      className="application-delete"
                      onClick={() => deleteApplication(application)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <footer>
          JobPilot · AI-powered job application workspace
        </footer>
      </main>
    </div>
  );
}

export default App;