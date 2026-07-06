import os
import pytest
from fastapi.testclient import TestClient
from database import connection
from api.main import app
from tools import pdf_extractor
from google.adk import Runner
from google.adk.events.event import Event
from google.genai import types
from tools.db_tools import save_user_profile, save_company_verification

# Define the TestClient
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch, tmp_path):
    """Overrides the database path and mocks the ADK Runner calls to prevent network/rate limits during tests."""
    test_db = os.path.join(tmp_path, "test_career_navigator.db")
    monkeypatch.setattr(connection, "DB_PATH", test_db)
    connection.init_db()
    
    # Mock extract_text_from_pdf to return simple mock resume text
    mock_resume_text = (
        "Name: Jane Doe\n"
        "Email: jane.doe@example.com\n"
        "Skills: Python, FastAPI, Machine Learning\n"
        "Projects: Stock dashboard using python\n"
        "Internships: Intern at TechCorp\n"
        "Certifications: AWS Developer"
    )
    import api.main
    mock_parsed_profile = {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "skills": ["Python", "FastAPI", "Machine Learning"],
        "projects": ["Stock dashboard using python"],
        "internships": ["Intern at TechCorp"],
        "certifications": ["AWS Developer"]
    }
    monkeypatch.setattr(api.main, "extract_text_from_pdf", lambda b: mock_resume_text)
    monkeypatch.setattr(api.main, "parse_resume_text_with_gemini", lambda t: mock_parsed_profile)
    
    # Mock ADK Runner.run_async to simulate agent behavior without calling the live Gemini API (prevents 429 Quota errors)
    async def mock_run_async(self, user_id, session_id, new_message=None, **kwargs):
        if self.agent.name == "ResumeAnalyzerAgent":
            save_user_profile(
                profile_id="user_default",
                name="Jane Doe",
                email="jane.doe@example.com",
                skills=["Python", "FastAPI", "Machine Learning"],
                projects=["Stock dashboard using python"],
                internships=["Intern at TechCorp"],
                certifications=["AWS Developer"]
            )
            yield Event(
                content=types.Content(parts=[types.Part(text="Resume successfully parsed and saved by mock agent.")]),
                author="ResumeAnalyzerAgent"
            )
        elif self.agent.name == "CompanyVerificationAgent":
            save_company_verification(
                company_id="company_shadowyfinancegroup",
                name="Shadowy Finance Group",
                website="http://shadowyfinancegroup.com",
                trust_score=0.1,
                safety_flags=["Cryptocurrency payment", "Anonymous location"],
                is_suspicious=1,
                notes="High risk of scam."
            )
            yield Event(
                content=types.Content(parts=[types.Part(text="Company verified by mock agent.")]),
                author="CompanyVerificationAgent"
            )
        elif self.agent.name == "ApplicationTrackerAgent":
            msg_text = ""
            if new_message and new_message.parts:
                msg_text = new_message.parts[0].text or ""
                
            from tools.db_tools import add_application, update_application_status
            if "Apply to job" in msg_text:
                import re
                job_id_match = re.search(r"ID '([^']+)'", msg_text)
                title_match = re.search(r"title '([^']+)'", msg_text)
                company_match = re.search(r"company '([^']+)'", msg_text)
                app_id_match = re.search(r"application_id '([^']+)'", msg_text)
                url_match = re.search(r"apply_url '([^']*)'", msg_text)
                src_match = re.search(r"source '([^']*)'", msg_text)
                notes_match = re.search(r"notes '([^']*)'", msg_text)
                
                job_id = job_id_match.group(1) if job_id_match else "job_unknown"
                title = title_match.group(1) if title_match else "title_unknown"
                company = company_match.group(1) if company_match else "company_unknown"
                app_id = app_id_match.group(1) if app_id_match else "app_unknown"
                url = url_match.group(1) if url_match else None
                source = src_match.group(1) if src_match else None
                notes = notes_match.group(1) if notes_match else None
                
                add_application(
                    application_id=app_id,
                    job_id=job_id,
                    company_name=company,
                    job_title=title,
                    status="Applied",
                    apply_url=url if url else None,
                    source=source if source else None,
                    notes=notes if notes else None
                )
            elif "Update application" in msg_text:
                import re
                app_id_match = re.search(r"ID '([^']+)'", msg_text)
                status_match = re.search(r"status '([^']+)'", msg_text)
                
                app_id = app_id_match.group(1) if app_id_match else "app_unknown"
                status = status_match.group(1) if status_match else "Applied"
                
                update_application_status(app_id, status)
                
            yield Event(
                content=types.Content(parts=[types.Part(text="Application tracker action simulated by mock agent.")]),
                author="ApplicationTrackerAgent"
            )
        else:
            yield Event(
                content=types.Content(parts=[types.Part(text="Mock generic event.")]),
                author="MockAgent"
            )
            
    monkeypatch.setattr(Runner, "run_async", mock_run_async)
    
    yield

def test_resume_upload_endpoint():
    """Tests the /api/resume/upload endpoint with a mock PDF file."""
    # Create fake PDF bytes
    fake_pdf_content = b"%PDF-1.4 mock pdf content"
    
    # Perform file upload POST request
    response = client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", fake_pdf_content, "application/pdf")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert "skills" in data
    assert "FastAPI" in data["skills"]
    assert "GEMINI PARSE SUCCESS" in data["message"]

def test_resume_upload_caching():
    """Tests that uploading the exact same resume twice results in a CACHE HIT on the second upload."""
    fake_pdf_content = b"%PDF-1.4 mock pdf content for cache test"
    
    # First upload (causes a Gemini Parse)
    res1 = client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", fake_pdf_content, "application/pdf")}
    )
    assert res1.status_code == 200
    assert "GEMINI PARSE SUCCESS" in res1.json()["message"]
    
    # Second upload (should hit cache)
    res2 = client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", fake_pdf_content, "application/pdf")}
    )
    assert res2.status_code == 200
    assert "CACHE HIT" in res2.json()["message"]

def test_resume_upload_quota_exhausted_fallback(monkeypatch):
    """Tests that a 429 quota exhaustion or API error automatically falls back to rule-based parsing and returns 200."""
    fake_pdf_content = b"%PDF-1.4 mock pdf content for fallback test"
    
    # Force parse_resume_text_with_gemini to throw an exception simulating 429
    import api.main
    monkeypatch.setattr(api.main, "parse_resume_text_with_gemini", lambda t: exec("raise(Exception('429 Quota Exceeded'))"))
    
    response = client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", fake_pdf_content, "application/pdf")}
    )
    
    assert response.status_code == 200
    data = response.json()
    # It should fallback to rule-based parsing successfully
    assert "FALLBACK PARSE ACTIVATED" in data["message"]
    assert "Jane Doe" in data["name"]  # Name successfully extracted by rule-based fallback
    assert "Python" in data["skills"]

def test_resume_upload_invalid_pdf(monkeypatch):
    """Tests that uploading a corrupted or invalid PDF returns HTTP 400 with a clear error message instead of 500."""
    import api.main
    monkeypatch.setattr(api.main, "extract_text_from_pdf", lambda b: exec("raise(ValueError('Pypdf failed to read header'))"))
    
    fake_pdf_content = b"invalid pdf bytes"
    
    response = client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", fake_pdf_content, "application/pdf")}
    )
    
    assert response.status_code == 400
    assert "Invalid or corrupted PDF file" in response.json()["detail"]

def test_resume_upload_no_adk_agent():
    """Verifies that uploading a resume parses directly and saves without initiating a multi-step ADK agent."""
    fake_pdf_content = b"%PDF-1.4 mock pdf content for direct test"
    
    response = client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", fake_pdf_content, "application/pdf")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "GEMINI PARSE SUCCESS" in data["message"] or "CACHE HIT" in data["message"]

def test_preferences_endpoints():
    """Tests the POST and GET /api/preferences endpoints."""
    # Post preferences
    pref_payload = {
        "preferred_location": "New York",
        "expected_salary": 100000.0,
        "work_mode": "Remote",
        "preferred_role": "Software Engineer"
    }
    post_res = client.post("/api/preferences", json=pref_payload)
    assert post_res.status_code == 200
    assert post_res.json()["preferred_location"] == "New York"
    assert post_res.json()["expected_salary"] == 100000.0
    
    # Get preferences
    get_res = client.get("/api/preferences")
    assert get_res.status_code == 200
    assert get_res.json()["preferred_location"] == "New York"
    assert get_res.json()["work_mode"] == "Remote"
    assert get_res.json()["preferred_role"] == "Software Engineer"

def test_job_discovery_endpoint():
    """Tests the /api/jobs/discover endpoint after setting up a profile and preferences."""
    # 1. Upload a resume to establish the user profile
    fake_pdf_content = b"%PDF-1.4 mock pdf content"
    client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", fake_pdf_content, "application/pdf")}
    )
    
    # 2. Configure user preferences
    pref_payload = {
        "preferred_location": "New York",
        "expected_salary": 100000.0,
        "work_mode": "Remote",
        "preferred_role": "Software Engineer"
    }
    client.post("/api/preferences", json=pref_payload)
    
    # 3. Call the discovery endpoint
    response = client.post("/api/jobs/discover")
    assert response.status_code == 200
    data = response.json()
    assert data["profile_id"] == "user_default"
    assert "top_matches" in data
    assert "related_opportunities" in data
    assert "jobs" in data
    
    # Verify legacy compatibility
    assert len(data["jobs"]) == len(data["top_matches"]) + len(data["related_opportunities"])
    
    # Ensure ranked sorting by composite score globally
    jobs = data["jobs"]
    for i in range(len(jobs) - 1):
        assert jobs[i]["composite_score"] >= jobs[i+1]["composite_score"]
        assert jobs[i]["final_rank"] == i + 1

def test_job_discovery_role_matching_and_synonyms():
    """Tests that role synonym mapping and classification work as expected."""
    # 1. Setup profile and preferences for a Data Scientist
    fake_pdf_content = b"%PDF-1.4 mock pdf content"
    client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", fake_pdf_content, "application/pdf")}
    )
    
    pref_payload = {
        "preferred_location": "Seattle",
        "expected_salary": 100000.0,
        "work_mode": "Remote",
        "preferred_role": "Data Scientist"
    }
    client.post("/api/preferences", json=pref_payload)
    
    # 2. Run discovery
    response = client.post("/api/jobs/discover")
    assert response.status_code == 200
    data = response.json()
    
    # "Data Scientist" and "Machine Learning Scientist" should be in top_matches
    # "Software Engineer" should be in related_opportunities
    top_titles = [j["title"].lower() for j in data["top_matches"]]
    related_titles = [j["title"].lower() for j in data["related_opportunities"]]
    
    # Verify that data science roles are categorized as top matches
    assert any("data scientist" in t for t in top_titles)
    assert any("machine learning scientist" in t for t in top_titles)
    
    # Verify that software engineer is categorized as related opportunity
    assert any("software engineer" in r for r in related_titles)
    
    # Verify match categories
    for job in data["top_matches"]:
        assert job["match_category"] == "top_match"
        assert job["role_match"] == 1.0
        
    for job in data["related_opportunities"]:
        assert job["match_category"] == "related"
        assert job["role_match"] == 0.0

def test_job_discovery_bangalore_location_match():
    """Tests location matching with Bangalore jobs and work mode preferences."""
    # 1. Setup profile with specific skills
    fake_pdf_content = b"%PDF-1.4 mock pdf content"
    client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", fake_pdf_content, "application/pdf")}
    )
    
    # 2. Set preferences to Bangalore, Hybrid, Data Scientist
    pref_payload = {
        "preferred_location": "Bangalore",
        "expected_salary": 90000.0,
        "work_mode": "Hybrid",
        "preferred_role": "Data Scientist"
    }
    client.post("/api/preferences", json=pref_payload)
    
    response = client.post("/api/jobs/discover")
    assert response.status_code == 200
    data = response.json()
    
    # Verify location matching scores
    for job in data["top_matches"] + data["related_opportunities"]:
        if job["location"].lower() == "bangalore":
            assert job["location_match"] == 1.0
        else:
            assert job["location_match"] == 0.0

    # Verify that the ML Scientist job in Bangalore with Hybrid work mode is ranked highly
    bangalore_hybrid_ml = None
    for j in data["top_matches"]:
        if j["location"].lower() == "bangalore" and j["work_mode_match"] == 1.0 and "machine learning" in j["title"].lower():
            bangalore_hybrid_ml = j
            break
            
    assert bangalore_hybrid_ml is not None
    assert bangalore_hybrid_ml["location_match"] == 1.0
    assert bangalore_hybrid_ml["work_mode_match"] == 1.0
    assert bangalore_hybrid_ml["role_match"] == 1.0
    assert bangalore_hybrid_ml["final_rank"] == 1  # Should rank first due to perfect matches on all preferences

def test_job_discovery_endpoint_no_profile():
    """Tests that the discovery endpoint returns 400 when no profile exists."""
    response = client.post("/api/jobs/discover")
    assert response.status_code == 400
    assert "No user profile found" in response.json()["detail"]

def test_job_discovery_endpoint_no_preferences():
    """Tests that the discovery endpoint returns preferences_required status when no preferences are configured."""
    # 1. Upload a resume to establish the user profile
    fake_pdf_content = b"%PDF-1.4 mock pdf content"
    client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", fake_pdf_content, "application/pdf")}
    )
    
    # 2. Call the discovery endpoint directly without setting preferences
    response = client.post("/api/jobs/discover")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "preferences_required"
    assert "preferred_location" in data["missing_fields"]
    assert "expected_salary" in data["missing_fields"]
    assert "work_mode" in data["missing_fields"]

def test_application_tracking_workflow():
    """Tests the full application tracking workflow: creation, retrieval, updates, source tracking, and notes."""
    # 1. Apply for a job
    apply_payload = {
        "job_id": "job_001",
        "apply_url": "https://linkedin.com/jobs/123",
        "source": "LinkedIn",
        "notes": "Spoke to recruiter on LinkedIn."
    }
    
    response = client.post("/api/applications/apply", json=apply_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["application_id"].startswith("app_")
    assert data["job_id"] == "job_001"
    assert data["company_name"] == "SecureTech Solutions"
    assert data["job_title"] == "Software Engineer (FastAPI & Python)"
    assert data["status"] == "Applied"
    assert data["source"] == "LinkedIn"
    assert data["apply_url"] == "https://linkedin.com/jobs/123"
    assert data["notes"] == "Spoke to recruiter on LinkedIn."
    
    app_id = data["application_id"]
    
    # 2. Retrieve applications list
    list_response = client.get("/api/applications")
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert len(list_data) > 0
    
    found_app = None
    for app in list_data:
        if app["application_id"] == app_id:
            found_app = app
            break
            
    assert found_app is not None
    assert found_app["job_title"] == "Software Engineer (FastAPI & Python)"
    assert found_app["source"] == "LinkedIn"
    assert found_app["notes"] == "Spoke to recruiter on LinkedIn."
    
    # 3. Update application status
    update_payload = {
        "application_id": app_id,
        "status": "Interview Scheduled"
    }
    update_response = client.post("/api/applications/update", json=update_payload)
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "Interview Scheduled"
    
    # Verify status update in retrieval
    list_response2 = client.get("/api/applications")
    list_data2 = list_response2.json()
    updated_app = next(app for app in list_data2 if app["application_id"] == app_id)
    assert updated_app["status"] == "Interview Scheduled"
    
    # 4. Attempt status update with invalid value
    invalid_update_payload = {
        "application_id": app_id,
        "status": "InvalidStatus"
    }
    invalid_response = client.post("/api/applications/update", json=invalid_update_payload)
    assert invalid_response.status_code == 400
    assert "Invalid status" in invalid_response.json()["detail"]
    
    # 5. Attempt application with invalid job_id
    invalid_apply_payload = {
        "job_id": "job_999"
    }
    invalid_apply_response = client.post("/api/applications/apply", json=invalid_apply_payload)
    assert invalid_apply_response.status_code == 400
    assert "not found" in invalid_apply_response.json()["detail"]

def test_job_discovery_company_verification_fallback(monkeypatch):
    """Tests that job discovery completes successfully with default assessments when CompanyVerificationAgent fails (e.g. 429 quota/503/connection errors)."""
    # 1. Setup profile and preferences
    fake_pdf_content = b"%PDF-1.4 mock pdf content"
    client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", fake_pdf_content, "application/pdf")}
    )
    
    pref_payload = {
        "preferred_location": "Seattle",
        "expected_salary": 100000.0,
        "work_mode": "Remote",
        "preferred_role": "Software Engineer"
    }
    client.post("/api/preferences", json=pref_payload)
    
    # 2. Mock Runner.run_async to raise Exception simulating API failure (429/503/etc)
    async def mock_run_async_fail(self, user_id, session_id, new_message=None, **kwargs):
        if self.agent.name == "CompanyVerificationAgent":
            raise Exception("503 Service Unavailable: High demand")
        else:
            yield Event(
                content=types.Content(parts=[types.Part(text="Mock")]),
                author="Mock"
            )
            
    monkeypatch.setattr(Runner, "run_async", mock_run_async_fail)
    
    # 3. Call discovery endpoint
    response = client.post("/api/jobs/discover")
    assert response.status_code == 200
    data = response.json()
    
    # "Shadowy Finance Group" should be in the results (since they are suspicious and run verification)
    shadowy_job = None
    all_jobs = data["jobs"]
    for j in all_jobs:
        if j["company"] == "Shadowy Finance Group":
            shadowy_job = j
            break
            
    assert shadowy_job is not None
    # Verify fallback fields
    assert "fallback_verified" in shadowy_job["safety_flags"]
    assert shadowy_job["risk_score"] == 0.9  # Default risk score for Shadowy Finance (1.0 - 0.1)
    assert "[Fallback Verified]" in shadowy_job["verification_notes"]


def test_gmail_authentication_mock():
    """Tests Gmail connection using mock tokens and checks response."""
    payload = {
        "token": "test_token_abc123",
        "refresh_token": "test_refresh_xyz789",
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "scopes": "https://www.googleapis.com/auth/gmail.readonly"
    }
    
    # 1. Connect
    response = client.post("/api/gmail/connect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Connected"
    assert data["mode"] == "Mock Mode" # default when credentials.json is missing
    
    # 2. Check status
    status_res = client.get("/api/email-monitor/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["connected"] is True
    assert status_data["mode"] == "Mock Mode"

def test_email_classification_and_status_updates(monkeypatch):
    """Tests rule-based and Gemini email classification and matching update loop."""
    # 1. Set up an application to match
    from tools.db_tools import add_application, get_application_by_id
    add_application(
        application_id="app_securetech_001",
        job_id="job_001",
        company_name="SecureTech Solutions",
        job_title="Software Engineer",
        status="Applied"
    )
    
    # 2. Trigger run monitor
    run_res = client.post("/api/email-monitor/run")
    assert run_res.status_code == 200
    run_data = run_res.json()
    assert run_data["processed_count"] > 0
    
    # Check if mock email 001 from hr@securetech.com was classified as "Interview Scheduled"
    # and matched to app_securetech_001
    updated_app = get_application_by_id("app_securetech_001")
    assert updated_app is not None
    assert updated_app["status"] == "Interview Scheduled"
    assert updated_app["last_email_id"] == "mock_email_001"

def test_duplicate_email_prevention():
    """Verifies that running the monitor sync a second time does not reprocess already processed emails."""
    # First run (processes all mock emails)
    res1 = client.post("/api/email-monitor/run")
    assert res1.status_code == 200
    assert res1.json()["processed_count"] > 0
    
    # Second run (should process 0 emails because they are logged in history)
    res2 = client.post("/api/email-monitor/run")
    assert res2.status_code == 200
    run_data = res2.json()
    assert run_data["processed_count"] == 0
    assert run_data["updated_count"] == 0

def test_invalid_oauth_token_handling(monkeypatch):
    """Verifies that live Gmail monitor falls back gracefully when live credentials throw auth/connection errors."""
    from tools.db_tools import save_gmail_credentials
    # Setup dummy live credentials
    save_gmail_credentials("user_default", {
        "token": "expired_token",
        "refresh_token": "expired_refresh",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "client_id",
        "client_secret": "client_secret",
        "scopes": "https://www.googleapis.com/auth/gmail.readonly"
    })
    
    # Force credentials.json check to return True to trigger Live mode path
    import os
    original_exists = os.path.exists
    def mock_exists(path, *args, **kwargs):
        path_str = str(path)
        if "credentials.json" in path_str:
            return True
        return original_exists(path, *args, **kwargs)
    monkeypatch.setattr(os.path, "exists", mock_exists)
    
    # Trigger run monitor
    # It should throw a client build exception because the token is expired/fake,
    # but the API endpoint should catch it and return 200 with 0 processed emails instead of crashing with 500.
    run_res = client.post("/api/email-monitor/run")
    assert run_res.status_code == 200
    data = run_res.json()
    assert "Live Gmail Mode" in data["mode"]
    assert data["processed_count"] == 0


