# CareerNavigator AI - Architecture Documentation (Phase 1)

CareerNavigator AI is a multi-agent system designed to guide job seekers by automated resume analysis, matching them with relevant job opportunities, and verifying company legitimacy to mitigate risk.

## System Topology

```mermaid
graph TD
    Client[FastAPI Client / API Request] -->|Uploads Resume / Invokes Job Match| API[FastAPI Endpoints / api/main.py]
    
    subgraph Google ADK Agentic Layer
        API -->|Orchestrated via| Runner[ADK Runner / sessions.db]
        Runner --> ResumeAnalyzer[ResumeAnalyzerAgent / agents/resume_analyzer.py]
        Runner --> JobDiscovery[JobDiscoveryAgent / agents/discovery.py]
        Runner --> CompanyVerification[CompanyVerificationAgent / agents/verification.py]
    end
    
    subgraph Model Context Protocol (MCP)
        ResumeAnalyzer -->|Stdio Connection| ResumeMcpServer[Resume MCP Server / mcp_servers/resume_server.py]
    end
    
    subgraph Storage Layer
        ResumeAnalyzer -->|Persists User Profiles| SQLite[(SQLite Database / career_navigator.db)]
        JobDiscovery -->|Reads User Profiles| SQLite
        CompanyVerification -->|Caches Verification Status| SQLite
    end
    
    subgraph External System Simulation
        JobDiscovery -->|Queries Mock Jobs| JobSearch[Job Search API / tools/job_search.py]
        CompanyVerification -->|Analyzes Security Signals| CompanyVerifier[Company Verifier / tools/company_verifier.py]
    end
```

---

## 1. Google ADK Agentic Layer

Google's **Agent Development Kit (ADK)** acts as the orchestrator core. The system defines three main specialist agents:

*   **ResumeAnalyzerAgent**: Responsible for converting unstructured resume texts into structured user profiles. It delegates raw text processing to the **Resume MCP Server** tools and saves the finalized structure into the SQLite database.
*   **JobDiscoveryAgent**: Queries job boards using the user's extracted skills, matches requirements against applicant experience, and ranks postings by match score.
*   **CompanyVerificationAgent**: Verifies the companies offering the jobs by scanning trust markers (e.g. domain age, keywords, known scams) and storing the security logs in the database.

---

## 2. Model Context Protocol (MCP) Integration

Model Context Protocol (MCP) is utilized to decouple specialized capability providers from the main agent loop. 

*   **Resume MCP Server (`mcp_servers/resume_server.py`)**: Runs as a separate process communicating via stdio. It exposes the `parse_resume_text` tool, which leverages Gemini's structured JSON output capability to parse skills, projects, internships, and certifications.
*   **Connection Lifecycle**: The `McpToolset` handles Stdio connection parameter setup and automatically registers tools on the `ResumeAnalyzerAgent` during runner sessions.

---

## 3. Storage Layer (SQLite)

We use SQLite for local datastore. The tables designed for Phase 1 are:

### `user_profiles`
Stores structured profiles extracted from resumes.
*   `id` (TEXT, Primary Key): Unique user ID (e.g. `user_default`).
*   `name` (TEXT): Applicant's full name.
*   `email` (TEXT): Applicant's email.
*   `skills` (TEXT): JSON list of skills.
*   `projects` (TEXT): JSON list of projects.
*   `internships` (TEXT): JSON list of internships.
*   `certifications` (TEXT): JSON list of certifications.

### `companies`
Caches company trust evaluation records.
*   `id` (TEXT, Primary Key): Unique company ID.
*   `name` (TEXT): Company name.
*   `website` (TEXT): Mock company URL.
*   `trust_score` (REAL): Float between 0.0 and 1.0.
*   `safety_flags` (TEXT): JSON list of red flags.
*   `is_suspicious` (INTEGER): Binary warning flag (0 or 1).
*   `notes` (TEXT): Security summary.

### `user_preferences`
Stores job preferences collected during candidate profile setup.
*   `id` (TEXT, Primary Key): Unique user ID (e.g. `user_default`).
*   `preferred_location` (TEXT): Location name (e.g. "New York", "Remote").
*   `expected_salary` (REAL): Target expected annual salary.
*   `work_mode` (TEXT): Work mode preference (e.g. "Remote", "Hybrid", "Onsite").
*   `preferred_role` (TEXT, Optional): Preferred job title or role keyword.

---

## 4. End-to-End Workflow

1.  **Resume Ingestion**: The user uploads a PDF resume to `/api/resume/upload`.
2.  **Text Extraction & Parsing**: FastAPI extracts PDF contents to text. The `ResumeAnalyzerAgent` invokes `parse_resume_text` on the Resume MCP Server.
3.  **Database Storage**: The agent stores the parsed structure in SQLite via the `save_user_profile` tool.
4.  **Profile Setup & Preferences**: The user submits their mandatory and optional job preferences to `/api/preferences` which are stored in the SQLite `user_preferences` table.
5.  **Job Search & Match**: The user requests matching jobs at `/api/jobs/discover`. If user preferences have not yet been configured, the system rejects the request with an HTTP 400 error.
6.  **Multi-Criteria Scoring & Ranking**: The system calculates a weighted Job Match Score utilizing 5 dimensions:
    - **Resume Skills (40%)**: Ratio of overlapping skills.
    - **Preferred Location (20%)**: Match between job location and candidate location.
    - **Expected Salary (15%)**: 1.0 if job salary meets or exceeds expectations; else scaled.
    - **Work Mode (15%)**: Match between job work mode and candidate work mode.
    - **Preferred Role (10%)**: Presence of the preferred role keyword in the job title.
    
    $$\text{Match Score} = (0.4 \times \text{Skills Score}) + (0.2 \times \text{Location Score}) + (0.15 \times \text{Salary Score}) + (0.15 \times \text{Work Mode Score}) + (0.10 \times \text{Role Score})$$
    
    For each job, the system also checks legitimacy. If suspicious, the `CompanyVerificationAgent` is launched to execute a deep audit. The final composite rank is calculated as:
    
    $$\text{Composite Score} = (0.7 \times \text{Match Score}) + (0.3 \times \text{Trust Score})$$
    
    Ranked job postings are returned to the client in descending order of composite score.
