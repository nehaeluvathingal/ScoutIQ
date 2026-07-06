import os
import json
import pytest
import sqlite3
from database import connection
from tools import db_tools, company_verifier, job_search, pdf_extractor

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch, tmp_path):
    """Overrides the database path with a temporary file for tests."""
    test_db = os.path.join(tmp_path, "test_career_navigator.db")
    monkeypatch.setattr(connection, "DB_PATH", test_db)
    connection.init_db()
    yield

def test_database_initialization():
    """Verifies that user_profiles and companies tables exist."""
    conn = connection.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_profiles'")
    assert cursor.fetchone() is not None
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='companies'")
    assert cursor.fetchone() is not None
    conn.close()

def test_db_tools_profile_saving_and_retrieval():
    """Tests saving and retrieving user profiles in the database."""
    db_tools.save_user_profile(
        profile_id="user_test",
        name="Alice Tester",
        email="alice@example.com",
        skills=["Python", "FastAPI", "React"],
        projects=["Task Manager Pro", "RAG Agent"],
        internships=["Backend Developer Intern"],
        certifications=["AWS Cloud Practitioner"]
    )
    
    profile = db_tools.get_user_profile("user_test")
    assert profile is not None
    assert profile["name"] == "Alice Tester"
    assert "FastAPI" in profile["skills"]
    assert len(profile["projects"]) == 2
    assert profile["internships"][0] == "Backend Developer Intern"

def test_company_verifier():
    """Tests company verification trust scores and safety flags."""
    # Test clean company
    clean = company_verifier.verify_company("Google Inc.")
    assert clean["trust_score"] == 0.95
    assert not clean["is_suspicious"]
    assert len(clean["safety_flags"]) == 0
    
    # Test suspicious company
    suspicious = company_verifier.verify_company("Shadowy Finance Group")
    assert suspicious["trust_score"] == 0.1
    assert suspicious["is_suspicious"]
    assert len(suspicious["safety_flags"]) > 0
    assert "Cryptocurrency" in suspicious["safety_flags"][0] or any("Crypto" in f for f in suspicious["safety_flags"])

def test_db_tools_company_verification_cache():
    """Tests saving and retrieving company verifications in the database."""
    db_tools.save_company_verification(
        company_id="company_google",
        name="Google Inc.",
        website="http://google.com",
        trust_score=0.98,
        safety_flags=["No flags"],
        is_suspicious=0,
        notes="Highly trusted corporate entity."
    )
    
    cached = db_tools.get_company_verification_by_name("Google Inc.")
    assert cached is not None
    assert cached["trust_score"] == 0.98
    assert not cached["is_suspicious"]
    assert cached["notes"] == "Highly trusted corporate entity."

def test_job_search_filters_correctly():
    """Tests that job_search matches job postings by skill."""
    # Search for Python jobs
    python_jobs = job_search.search_jobs(["Python"])
    assert len(python_jobs) > 0
    # Ensure they contain python in skills
    for job in python_jobs:
        assert "Python" in job["skills_required"] or "Python" in job["title"]

def test_pdf_extractor_raises_on_invalid_bytes():
    """Tests that the PDF extractor raises an exception on invalid bytes."""
    with pytest.raises(ValueError):
        pdf_extractor.extract_text_from_pdf(b"invalid pdf bytes")

def test_db_tools_application_helpers():
    """Tests logging, retrieving, and updating job applications in database."""
    # 1. Add application
    db_tools.add_application(
        application_id="app_test_123",
        job_id="job_001",
        company_name="SecureTech Solutions",
        job_title="Software Engineer (FastAPI & Python)",
        status="Applied",
        apply_url="https://linkedin.com/jobs/123",
        source="LinkedIn",
        notes="Saved note for testing."
    )
    
    # 2. Get application by ID
    app = db_tools.get_application_by_id("app_test_123")
    assert app is not None
    assert app["job_id"] == "job_001"
    assert app["company_name"] == "SecureTech Solutions"
    assert app["job_title"] == "Software Engineer (FastAPI & Python)"
    assert app["status"] == "Applied"
    assert app["apply_url"] == "https://linkedin.com/jobs/123"
    assert app["source"] == "LinkedIn"
    assert app["notes"] == "Saved note for testing."
    
    # 3. Update status
    db_tools.update_application_status("app_test_123", "Assessment Received")
    app_updated = db_tools.get_application_by_id("app_test_123")
    assert app_updated["status"] == "Assessment Received"
    
    # 4. List applications
    all_apps = db_tools.get_applications()
    assert len(all_apps) > 0
    assert any(a["application_id"] == "app_test_123" for a in all_apps)

def test_db_tools_resume_cache_helpers():
    """Tests saving and retrieving parsed resume cache in database."""
    mock_profile = {
        "name": "Cache Tester",
        "email": "cache@example.com",
        "skills": ["Python", "SQL"],
        "projects": ["Cache project"],
        "internships": ["Cache Intern"],
        "certifications": ["Cache Cert"]
    }
    
    # 1. Save cache
    db_tools.save_resume_cache("test_hash_xyz", mock_profile)
    
    # 2. Retrieve cache
    cached = db_tools.get_resume_cache("test_hash_xyz")
    assert cached is not None
    assert cached["name"] == "Cache Tester"
    assert cached["email"] == "cache@example.com"
    assert "Python" in cached["skills"]
