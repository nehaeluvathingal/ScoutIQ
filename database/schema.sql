-- SQL DDL schema for CareerNavigator AI

CREATE TABLE IF NOT EXISTS user_profiles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    skills TEXT NOT NULL,          -- JSON list of skills
    projects TEXT NOT NULL,        -- JSON list of projects
    internships TEXT NOT NULL,     -- JSON list of internships
    certifications TEXT NOT NULL,  -- JSON list of certifications
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS companies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    website TEXT,
    trust_score REAL,
    safety_flags TEXT,             -- JSON list of warning flags
    is_suspicious INTEGER,         -- 0 or 1
    notes TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_preferences (
    id TEXT PRIMARY KEY,
    preferred_location TEXT NOT NULL,
    expected_salary REAL NOT NULL,
    work_mode TEXT NOT NULL,       -- Remote, Hybrid, Onsite
    preferred_role TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS applications (
    application_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    company_name TEXT NOT NULL,
    job_title TEXT NOT NULL,
    application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL CHECK(status IN ('Applied', 'Assessment Received', 'Interview Scheduled', 'Rejected', 'Offer Received')) DEFAULT 'Applied',
    apply_url TEXT,
    source TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS resume_cache (
    resume_hash TEXT PRIMARY KEY,
    parsed_profile TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gmail_credentials (
    profile_id TEXT PRIMARY KEY,
    token TEXT NOT NULL,
    refresh_token TEXT,
    token_uri TEXT,
    client_id TEXT,
    client_secret TEXT,
    scopes TEXT,
    expiry TIMESTAMP
);

CREATE TABLE IF NOT EXISTS email_history (
    email_id TEXT PRIMARY KEY,
    sender TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    received_date TEXT,
    classification TEXT NOT NULL,
    matched_application_id TEXT,
    confidence_score REAL,
    classification_method TEXT NOT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

