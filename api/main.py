import os
import uuid
import json
import logging
from typing import Union, List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from api.models import (
    ResumeParseResponse, JobDiscoverResponse, JobMatchResult,
    UserPreferencesRequest, UserPreferencesResponse, PreferencesRequiredResponse,
    ApplyJobRequest, ApplyJobResponse, UpdateStatusRequest, UpdateStatusResponse, ApplicationResult,
    GmailConnectRequest, GmailConnectResponse, ProcessedEmailLog, MonitorRunResponse, MonitorStatusResponse
)
from tools.pdf_extractor import extract_text_from_pdf
from tools.db_tools import (
    get_user_profile, get_company_verification_by_name, save_user_preferences, get_user_preferences,
    get_applications, get_application_by_id, save_gmail_credentials, get_gmail_credentials,
    get_email_history, get_email_monitor_stats
)
from tools.job_search import search_jobs, get_job_by_id
from tools.resume_parser import parse_resume_text_with_gemini, extract_resume_details_fallback
from agents.resume_analyzer import resume_analyzer_agent
from agents.verification import company_verification_agent
from agents.tracker import application_tracker_agent
from agents.email_monitor import run_email_monitor_sync
from google.adk import Runner
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from google.genai import types

def load_dotenv():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip("'\"")

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_main")

ROLE_SYNONYMS = {
    "software engineer": [
        "software engineer",
        "backend engineer",
        "python developer",
        "full stack developer",
        "frontend developer",
        "developer",
        "react developer",
        "react frontend developer",
        "frontend engineer"
    ],
    "data scientist": [
        "data scientist",
        "ml engineer",
        "ai engineer",
        "machine learning scientist",
        "ml operations engineer",
        "machine learning engineer"
    ]
}

def is_role_match(pref_role: str, job_title: str) -> float:
    pref_clean = pref_role.lower().strip()
    title_clean = job_title.lower().strip()
    
    if pref_clean in title_clean or title_clean in pref_clean:
        return 1.0
        
    for group_key, synonyms in ROLE_SYNONYMS.items():
        if pref_clean == group_key or pref_clean in synonyms:
            if title_clean == group_key or any(syn in title_clean for syn in synonyms):
                return 1.0
                
    return 0.0

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing SQLite database and applying migrations...")
    from database.connection import init_db
    init_db()
    logger.info("Database initialized successfully.")
    yield

app = FastAPI(title="CareerNavigator AI API", description="FastAPI Backend for CareerNavigator AI Phase 1", version="1.0.0", lifespan=lifespan)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Session Service for ADK Session Memory
session_service = SqliteSessionService(db_path="sessions.db")

@app.post("/api/resume/upload", response_model=ResumeParseResponse)
async def upload_resume(file: UploadFile = File(...)):
    """Uploads a PDF resume, parses its content, and saves the user profile.
    
    This endpoint implements SHA-256 caching and direct parsing (bypassing the ADK agent planning overhead
    to consume at most 1 Gemini request), and provides a 429 quota exhaustion fallback.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported.")
    
    import hashlib
    from tools.db_tools import get_resume_cache, save_resume_cache, save_user_profile
    
    try:
        pdf_bytes = await file.read()
        try:
            resume_text = extract_text_from_pdf(pdf_bytes)
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=f"Invalid or corrupted PDF file: {str(ve)}")
            
        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="PDF file does not contain any readable text.")
            
        resume_hash = hashlib.sha256(resume_text.encode("utf-8")).hexdigest()
        
        # 1. Check cache first
        cached_profile = get_resume_cache(resume_hash)
        if cached_profile:
            logger.info("[Resume Upload] CACHE HIT")
            save_user_profile(
                profile_id="user_default",
                name=cached_profile["name"],
                email=cached_profile.get("email") or "",
                skills=cached_profile["skills"],
                projects=cached_profile["projects"],
                internships=cached_profile["internships"],
                certifications=cached_profile["certifications"]
            )
            return ResumeParseResponse(
                name=cached_profile["name"],
                email=cached_profile.get("email") or "",
                skills=cached_profile["skills"],
                projects=cached_profile["projects"],
                internships=cached_profile["internships"],
                certifications=cached_profile["certifications"],
                message="[Resume Upload] CACHE HIT"
            )
            
        # 2. If not cached, call Gemini parser directly (at most 1 API request)
        parsed_profile = None
        message = ""
        try:
            parsed_profile = parse_resume_text_with_gemini(resume_text)
            logger.info("[Resume Upload] GEMINI PARSE SUCCESS")
            message = "[Resume Upload] GEMINI PARSE SUCCESS"
        except Exception as ge:
            err_str = str(ge)
            logger.warning(f"[Resume Upload] FALLBACK PARSE ACTIVATED ({err_str})")
            parsed_profile = extract_resume_details_fallback(resume_text)
            message = f"[Resume Upload] FALLBACK PARSE ACTIVATED ({err_str})"
            
        # 3. Save parsed profile to database
        save_user_profile(
            profile_id="user_default",
            name=parsed_profile["name"],
            email=parsed_profile.get("email") or "",
            skills=parsed_profile["skills"],
            projects=parsed_profile["projects"],
            internships=parsed_profile["internships"],
            certifications=parsed_profile["certifications"]
        )
        
        # 4. Save to cache table
        save_resume_cache(resume_hash, parsed_profile)
        
        return ResumeParseResponse(
            name=parsed_profile["name"],
            email=parsed_profile.get("email") or "",
            skills=parsed_profile["skills"],
            projects=parsed_profile["projects"],
            internships=parsed_profile["internships"],
            certifications=parsed_profile["certifications"],
            message=message
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error during resume upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/preferences", response_model=UserPreferencesResponse)
async def update_preferences(req: UserPreferencesRequest, profile_id: str = "user_default"):
    """Saves or updates the user preferences (location, salary, work mode, and role)."""
    try:
        save_user_preferences(
            profile_id=profile_id,
            preferred_location=req.preferred_location,
            expected_salary=req.expected_salary,
            work_mode=req.work_mode,
            preferred_role=req.preferred_role
        )
        return UserPreferencesResponse(
            profile_id=profile_id,
            preferred_location=req.preferred_location,
            expected_salary=req.expected_salary,
            work_mode=req.work_mode,
            preferred_role=req.preferred_role,
            message="User preferences saved successfully."
        )
    except Exception as e:
        logger.error(f"Error saving preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/preferences", response_model=UserPreferencesResponse)
async def get_preferences(profile_id: str = "user_default"):
    """Retrieves user preferences from the database."""
    try:
        prefs = get_user_preferences(profile_id)
        if not prefs:
            raise HTTPException(status_code=404, detail="User preferences not configured.")
        return UserPreferencesResponse(
            profile_id=profile_id,
            preferred_location=prefs["preferred_location"],
            expected_salary=prefs["expected_salary"],
            work_mode=prefs["work_mode"],
            preferred_role=prefs["preferred_role"],
            message="User preferences retrieved successfully."
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error retrieving preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/discover", response_model=Union[JobDiscoverResponse, PreferencesRequiredResponse])
async def discover_jobs(profile_id: str = "user_default"):
    """Discovers matching jobs for the user profile, runs Company Verification Agent on each company, and returns ranked results."""
    try:
        profile = get_user_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=400, detail="No user profile found. Please upload a resume first.")
        
        # Get user preferences
        prefs = get_user_preferences(profile_id)
        
        # Check missing preferences
        missing_fields = []
        if not prefs:
            missing_fields = ["preferred_location", "expected_salary", "work_mode"]
        else:
            if not prefs.get("preferred_location") or prefs.get("preferred_location").strip() == "":
                missing_fields.append("preferred_location")
            if not prefs.get("expected_salary") or prefs.get("expected_salary") <= 0:
                missing_fields.append("expected_salary")
            if not prefs.get("work_mode") or prefs.get("work_mode").strip() == "":
                missing_fields.append("work_mode")
                
        if missing_fields:
            logger.info(f"User preferences missing fields: {missing_fields}. Returning requirements.")
            return PreferencesRequiredResponse(
                status="preferences_required",
                missing_fields=missing_fields
            )
        
        skills = profile["skills"]
        logger.info(f"Searching jobs for profile {profile_id} with skills: {skills}")
        
        # Get matching jobs
        jobs = search_jobs(skills)
        matched_jobs_results = []
        
        # Initialize ADK Runner for CompanyVerificationAgent
        runner_verify = Runner(
            agent=company_verification_agent,
            session_service=session_service,
            app_name="CareerNavigator",
            auto_create_session=True
        )
        
        for job in jobs:
            company_name = job["company"]
            
            # Check if company verification is already cached
            cached_verification = get_company_verification_by_name(company_name)
            
            if not cached_verification:
                from tools.company_verifier import verify_company as direct_verify
                from tools.db_tools import save_company_verification as direct_save
                
                v = direct_verify(company_name)
                if v["is_suspicious"]:
                    logger.info(f"Company '{company_name}' flagged as suspicious. Running CompanyVerificationAgent for detailed audit...")
                    user_id = "default_user"
                    session_id = str(uuid.uuid4())
                    verification_msg = f"Verify the safety of the company: {company_name}"
                    content = types.Content(parts=[types.Part(text=verification_msg)])
                    
                    try:
                        async for event in runner_verify.run_async(user_id=user_id, session_id=session_id, new_message=content):
                            pass
                    except Exception as ge:
                        err_str = str(ge)
                        logger.warning(f"[Company Verification] FALLBACK ACTIVATED ({err_str})")
                        # Reasonable default trust/risk assessment with fallback_verified flag
                        safety_flags = v["safety_flags"] + ["fallback_verified"]
                        direct_save(
                            company_id="company_" + company_name.lower().replace(" ", ""),
                            name=company_name,
                            website=f"http://{company_name.lower().replace(' ', '')}.com",
                            trust_score=v["trust_score"],
                            safety_flags=safety_flags,
                            is_suspicious=1 if v["is_suspicious"] else 0,
                            notes=f"[Fallback Verified] {v['notes']} (Agent error: {err_str})"
                        )
                else:
                    logger.info(f"Company '{company_name}' is clean. Saving verification directly.")
                    direct_save(
                        company_id="company_" + company_name.lower().replace(" ", ""),
                        name=company_name,
                        website=f"http://{company_name.lower().replace(' ', '')}.com",
                        trust_score=v["trust_score"],
                        safety_flags=v["safety_flags"],
                        is_suspicious=1 if v["is_suspicious"] else 0,
                        notes=v["notes"]
                    )
                
                cached_verification = get_company_verification_by_name(company_name)
                
            # Calculate match score based on 5 parameters (skills, location, salary, work mode, preferred role)
            job_skills = job["skills_required"]
            matched_skills = [s for s in job_skills if s.lower() in [us.lower() for us in skills]]
            skills_score = len(matched_skills) / len(job_skills) if job_skills else 0.0
            
            # Location check
            pref_loc = prefs["preferred_location"].lower().strip()
            job_loc = job["location"].lower().strip()
            location_score = 1.0 if pref_loc == job_loc or (pref_loc == "remote" and job_loc == "remote") else 0.0
            
            # Salary check
            exp_sal = prefs["expected_salary"]
            job_sal = job["salary"]
            salary_score = 1.0 if job_sal >= exp_sal else (job_sal / exp_sal if exp_sal > 0 else 1.0)
            
            # Work mode check
            pref_mode = prefs["work_mode"].lower().strip()
            job_mode = job["work_mode"].lower().strip()
            work_mode_score = 1.0 if pref_mode == job_mode else 0.0
            
            # Preferred role check using the helper is_role_match
            pref_role = prefs.get("preferred_role")
            if pref_role and pref_role.strip():
                role_score = is_role_match(pref_role, job["title"])
                match_category = "top_match" if role_score > 0.0 else "related"
            else:
                role_score = 1.0
                match_category = "top_match"
                
            # Composite match score: Skills (30%), Location (20%), Salary (15%), Work Mode (15%), Preferred Role (20%)
            match_score = (skills_score * 0.3) + (location_score * 0.2) + (salary_score * 0.15) + (work_mode_score * 0.15) + (role_score * 0.2)
            
            trust_score = cached_verification["trust_score"]
            risk_score = 1.0 - trust_score
            
            # Apply a risk-score penalty to composite score
            composite_score = (match_score * 0.7) + (trust_score * 0.3) - (risk_score * 0.2)
            
            matched_jobs_results.append(
                JobMatchResult(
                    job_id=job["id"],
                    title=job["title"],
                    company=job["company"],
                    location=job["location"],
                    description=job["description"],
                    skills_required=job["skills_required"],
                    match_score=round(match_score, 2),
                    salary_match=round(salary_score, 2),
                    location_match=round(location_score, 2),
                    work_mode_match=round(work_mode_score, 2),
                    role_match=round(role_score, 2),
                    final_rank=0,  # Will be populated after sorting
                    risk_score=round(risk_score, 2),
                    composite_score=round(composite_score, 2),
                    match_category=match_category,
                    safety_flags=cached_verification["safety_flags"],
                    verification_notes=cached_verification["notes"],
                    work_mode=job["work_mode"],
                    salary=job["salary"]
                )
            )
            
        # Separate jobs into top matches and related opportunities
        top_matches = [j for j in matched_jobs_results if j.match_category == "top_match"]
        related_opportunities = [j for j in matched_jobs_results if j.match_category == "related"]
        
        # Sort each section by composite score descending
        top_matches.sort(key=lambda x: x.composite_score, reverse=True)
        related_opportunities.sort(key=lambda x: x.composite_score, reverse=True)
        
        # Populate final_rank (global 1-based position starting with top_matches then related_opportunities)
        rank = 1
        for job_result in top_matches:
            job_result.final_rank = rank
            rank += 1
            
        for job_result in related_opportunities:
            job_result.final_rank = rank
            rank += 1
            
        # Combine back for legacy 'jobs' field (backward compatibility)
        legacy_jobs = top_matches + related_opportunities
            
        return JobDiscoverResponse(
            profile_id=profile_id,
            applicant_name=profile["name"],
            skills=profile["skills"],
            top_matches=top_matches,
            related_opportunities=related_opportunities,
            jobs=legacy_jobs
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error during job discovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/applications/apply", response_model=ApplyJobResponse)
async def apply_to_job(req: ApplyJobRequest):
    """Log a job application by ID, retrieving metadata from the mock job pool and running ApplicationTrackerAgent."""
    job = get_job_by_id(req.job_id)
    if not job:
        raise HTTPException(status_code=400, detail=f"Job with ID '{req.job_id}' not found in mock job pool.")
        
    application_id = "app_" + str(uuid.uuid4())
    company_name = job["company"]
    job_title = job["title"]
    
    try:
        runner = Runner(
            agent=application_tracker_agent,
            session_service=session_service,
            app_name="CareerNavigator",
            auto_create_session=True
        )
        
        user_id = "default_user"
        session_id = str(uuid.uuid4())
        
        message_str = (
            f"Apply to job with ID '{req.job_id}', title '{job_title}', company '{company_name}', "
            f"application_id '{application_id}', apply_url '{req.apply_url or ''}', "
            f"source '{req.source or ''}', and notes '{req.notes or ''}'."
        )
        content = types.Content(parts=[types.Part(text=message_str)])
        
        agent_response_text = []
        try:
            async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            agent_response_text.append(part.text)
        except Exception as ae:
            logger.warning(f"ApplicationTrackerAgent run_async failed: {ae}. Falling back to direct DB insert.")
            agent_response_text.append("Application Tracker Agent is temporarily offline. Recorded in database directly.")
                        
        app_record = get_application_by_id(application_id)
        if not app_record:
            from tools.db_tools import add_application as direct_add
            direct_add(
                application_id=application_id,
                job_id=req.job_id,
                company_name=company_name,
                job_title=job_title,
                status="Applied",
                apply_url=req.apply_url,
                source=req.source,
                notes=req.notes
            )
            app_record = get_application_by_id(application_id)
            
        return ApplyJobResponse(
            application_id=app_record["application_id"],
            job_id=app_record["job_id"],
            company_name=app_record["company_name"],
            job_title=app_record["job_title"],
            application_date=app_record["application_date"],
            status=app_record["status"],
            apply_url=app_record["apply_url"],
            source=app_record["source"],
            notes=app_record["notes"],
            message="".join(agent_response_text) or "Application registered successfully."
        )
    except Exception as e:
        logger.error(f"Error during job application tracking: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/applications/update", response_model=UpdateStatusResponse)
async def update_application(req: UpdateStatusRequest):
    """Updates the status of a job application using ApplicationTrackerAgent."""
    allowed_statuses = ["Applied", "Assessment Received", "Interview Scheduled", "Rejected", "Offer Received"]
    if req.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status '{req.status}'. Allowed values are: {allowed_statuses}")
        
    app_record = get_application_by_id(req.application_id)
    if not app_record:
        raise HTTPException(status_code=404, detail=f"Application with ID '{req.application_id}' not found.")
        
    try:
        runner = Runner(
            agent=application_tracker_agent,
            session_service=session_service,
            app_name="CareerNavigator",
            auto_create_session=True
        )
        
        user_id = "default_user"
        session_id = str(uuid.uuid4())
        
        message_str = f"Update application with ID '{req.application_id}' to status '{req.status}'."
        content = types.Content(parts=[types.Part(text=message_str)])
        
        agent_response_text = []
        try:
            async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            agent_response_text.append(part.text)
        except Exception as ae:
            logger.warning(f"ApplicationTrackerAgent status update failed: {ae}. Falling back to direct DB update.")
            agent_response_text.append("Application Tracker Agent is temporarily offline. Updated status directly.")
                        
        updated_record = get_application_by_id(req.application_id)
        if not updated_record or updated_record["status"] != req.status:
            from tools.db_tools import update_application_status as direct_update
            direct_update(req.application_id, req.status)
            
        return UpdateStatusResponse(
            application_id=req.application_id,
            status=req.status,
            message="".join(agent_response_text) or "Application status updated successfully."
        )
    except Exception as e:
        logger.error(f"Error during application status update: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/applications", response_model=List[ApplicationResult])
async def list_applications():
    """Retrieve all job application records from the database."""
    try:
        records = get_applications()
        results = []
        for r in records:
            results.append(
                ApplicationResult(
                    application_id=r["application_id"],
                    job_id=r["job_id"],
                    company_name=r["company_name"],
                    job_title=r["job_title"],
                    application_date=r["application_date"],
                    status=r["status"],
                    apply_url=r["apply_url"],
                    source=r["source"],
                    notes=r["notes"]
                )
            )
        return results
    except Exception as e:
        logger.error(f"Error listing applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/gmail/connect", response_model=GmailConnectResponse)
async def connect_gmail(req: GmailConnectRequest):
    """Authenticate and connect Gmail. Saves tokens to the database."""
    try:
        # Check if credentials.json is detected in the workspace root
        workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        creds_file_exists = os.path.exists(os.path.join(workspace_root, "credentials.json"))
        
        mode = "Live Gmail Mode" if creds_file_exists else "Mock Mode"
        
        creds_dict = {
            "token": req.token or "mock_oauth_token_val",
            "refresh_token": req.refresh_token or "mock_refresh_token_val",
            "token_uri": req.token_uri or "https://oauth2.googleapis.com/token",
            "client_id": req.client_id or "mock_client_id_val",
            "client_secret": req.client_secret or "mock_client_secret_val",
            "scopes": req.scopes or "https://www.googleapis.com/auth/gmail.readonly",
            "expiry": "2036-07-01 00:00:00"
        }
        save_gmail_credentials(profile_id="user_default", creds_dict=creds_dict)
        
        return GmailConnectResponse(
            status="Connected",
            mode=mode,
            message=f"Gmail successfully connected in {mode}."
        )
    except Exception as e:
        logger.error(f"Error connecting Gmail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/email-monitor/run", response_model=MonitorRunResponse)
async def run_email_monitor():
    """Trigger the email monitor sync once and process recruiter emails."""
    try:
        workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        creds_file_exists = os.path.exists(os.path.join(workspace_root, "credentials.json"))
        
        creds = get_gmail_credentials("user_default")
        
        if creds_file_exists and creds:
            mode_name = "Live Gmail Mode"
            run_creds = creds
        else:
            mode_name = "Mock Mode"
            run_creds = None
            
        results = run_email_monitor_sync(creds=run_creds)
        
        processed = len(results)
        updated = sum(1 for r in results if r["status_updated"])
        
        logs = []
        for r in results:
            logs.append(
                ProcessedEmailLog(
                    email_id=r["email_id"],
                    sender=r["sender"],
                    subject=r["subject"],
                    classification=r["classification"],
                    matched_application_id=r["matched_application_id"],
                    matched_company=r["matched_company"],
                    confidence_score=r["confidence_score"],
                    classification_method=r["classification_method"],
                    status_updated=r["status_updated"]
                )
            )
            
        return MonitorRunResponse(
            mode=mode_name,
            processed_count=processed,
            updated_count=updated,
            logs=logs,
            message=f"Sync successfully completed in {mode_name}. Processed {processed} emails, updated {updated} applications."
        )
    except Exception as e:
        logger.error(f"Error running email monitor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/email-monitor/status", response_model=MonitorStatusResponse)
async def get_email_monitor_status():
    """Retrieve connection status, operational mode, and processing stats."""
    try:
        workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        creds_file_exists = os.path.exists(os.path.join(workspace_root, "credentials.json"))
        
        creds = get_gmail_credentials("user_default")
        
        mode = "Mock Mode"
        connected = False
        if creds:
            connected = True
            if creds_file_exists:
                mode = "Live Gmail Mode"
                
        stats = get_email_monitor_stats()
        
        return MonitorStatusResponse(
            connected=connected,
            mode=mode,
            last_checked=stats.get("last_checked"),
            total_processed=stats.get("total_emails_processed", 0),
            total_updated=stats.get("applications_updated", 0)
        )
    except Exception as e:
        logger.error(f"Error fetching email monitor status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/email-monitor/history")
async def get_email_monitor_history():
    """Retrieve all processed emails from the email history audit log."""
    try:
        return get_email_history()
    except Exception as e:
        logger.error(f"Error fetching email monitor history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


