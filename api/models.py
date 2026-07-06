from pydantic import BaseModel
from typing import List, Optional

class ResumeParseResponse(BaseModel):
    name: str
    email: str
    skills: List[str]
    projects: List[str]
    internships: List[str]
    certifications: List[str]
    message: str

class JobMatchResult(BaseModel):
    job_id: str
    title: str
    company: str
    location: str
    description: str
    skills_required: List[str]
    match_score: float
    salary_match: float
    location_match: float
    work_mode_match: float
    role_match: float
    final_rank: int
    risk_score: float
    composite_score: float
    match_category: str  # "top_match" or "related"
    safety_flags: List[str]
    verification_notes: str
    work_mode: str
    salary: float


class JobDiscoverResponse(BaseModel):
    profile_id: str
    applicant_name: str
    skills: List[str]
    top_matches: List[JobMatchResult]
    related_opportunities: List[JobMatchResult]
    jobs: List[JobMatchResult]  # Retained for backward compatibility

class UserPreferencesRequest(BaseModel):
    preferred_location: str
    expected_salary: float
    work_mode: str  # Remote, Hybrid, Onsite
    preferred_role: Optional[str] = None

class UserPreferencesResponse(BaseModel):
    profile_id: str
    preferred_location: str
    expected_salary: float
    work_mode: str
    preferred_role: Optional[str]
    message: str

class PreferencesRequiredResponse(BaseModel):
    status: str  # "preferences_required"
    missing_fields: List[str]

class ApplyJobRequest(BaseModel):
    job_id: str
    apply_url: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None

class ApplyJobResponse(BaseModel):
    application_id: str
    job_id: str
    company_name: str
    job_title: str
    application_date: str
    status: str
    apply_url: Optional[str]
    source: Optional[str]
    notes: Optional[str]
    message: str

class UpdateStatusRequest(BaseModel):
    application_id: str
    status: str

class UpdateStatusResponse(BaseModel):
    application_id: str
    status: str
    message: str

class ApplicationResult(BaseModel):
    application_id: str
    job_id: str
    company_name: str
    job_title: str
    application_date: str
    status: str
    apply_url: Optional[str]
    source: Optional[str]
    notes: Optional[str]

class GmailConnectRequest(BaseModel):
    token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_uri: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    scopes: Optional[str] = None

class GmailConnectResponse(BaseModel):
    status: str
    mode: str
    message: str

class ProcessedEmailLog(BaseModel):
    email_id: str
    sender: str
    subject: str
    classification: str
    matched_application_id: Optional[str]
    matched_company: Optional[str]
    confidence_score: float
    classification_method: str
    status_updated: bool

class MonitorRunResponse(BaseModel):
    mode: str
    processed_count: int
    updated_count: int
    logs: List[ProcessedEmailLog]
    message: str

class MonitorStatusResponse(BaseModel):
    connected: bool
    mode: str
    last_checked: Optional[str]
    total_processed: int
    total_updated: int

