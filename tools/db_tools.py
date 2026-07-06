import json
import logging
from database.connection import get_db_connection

logger = logging.getLogger("db_tools")

def save_user_profile(profile_id: str, name: str, email: str, skills: list, projects: list, internships: list, certifications: list) -> None:
    """Saves or updates a user profile in the SQLite database.
    
    All list fields are stored as JSON strings.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO user_profiles (id, name, email, skills, projects, internships, certifications, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                profile_id,
                name,
                email,
                json.dumps(skills),
                json.dumps(projects),
                json.dumps(internships),
                json.dumps(certifications)
            )
        )
        conn.commit()
        logger.info(f"User profile saved successfully for user: {profile_id}")
    except Exception as e:
        logger.error(f"Error saving user profile: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_user_profile(profile_id: str) -> dict:
    """Retrieves a user profile from the database, parsing JSON list fields back to Python lists."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profiles WHERE id = ?", (profile_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "skills": json.loads(row["skills"]),
            "projects": json.loads(row["projects"]),
            "internships": json.loads(row["internships"]),
            "certifications": json.loads(row["certifications"]),
            "updated_at": row["updated_at"]
        }
    except Exception as e:
        logger.error(f"Error retrieving user profile: {e}")
        raise e
    finally:
        conn.close()

def save_company_verification(company_id: str, name: str, website: str, trust_score: float, safety_flags: list, is_suspicious: int, notes: str) -> None:
    """Caches a company verification record in the database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO companies (id, name, website, trust_score, safety_flags, is_suspicious, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                company_id,
                name,
                website,
                trust_score,
                json.dumps(safety_flags),
                is_suspicious,
                notes
            )
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Error saving company verification: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_company_verification_by_name(name: str) -> dict:
    """Retrieves a cached company verification record by name."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Case insensitive check
        cursor.execute("SELECT * FROM companies WHERE LOWER(name) = LOWER(?)", (name,))
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            "id": row["id"],
            "name": row["name"],
            "website": row["website"],
            "trust_score": row["trust_score"],
            "safety_flags": json.loads(row["safety_flags"]),
            "is_suspicious": bool(row["is_suspicious"]),
            "notes": row["notes"],
            "updated_at": row["updated_at"]
        }
    except Exception as e:
        logger.error(f"Error retrieving company verification: {e}")
        raise e
    finally:
        conn.close()

def save_user_preferences(profile_id: str, preferred_location: str, expected_salary: float, work_mode: str, preferred_role: str = None) -> None:
    """Saves or updates user preferences in the SQLite database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO user_preferences (id, preferred_location, expected_salary, work_mode, preferred_role, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (profile_id, preferred_location, expected_salary, work_mode, preferred_role)
        )
        conn.commit()
        logger.info(f"User preferences saved successfully for user: {profile_id}")
    except Exception as e:
        logger.error(f"Error saving user preferences: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_user_preferences(profile_id: str) -> dict:
    """Retrieves user preferences from the database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_preferences WHERE id = ?", (profile_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            "id": row["id"],
            "preferred_location": row["preferred_location"],
            "expected_salary": row["expected_salary"],
            "work_mode": row["work_mode"],
            "preferred_role": row["preferred_role"],
            "updated_at": row["updated_at"]
        }
    except Exception as e:
        logger.error(f"Error retrieving user preferences: {e}")
        raise e
    finally:
        conn.close()

def add_application(application_id: str, job_id: str, company_name: str, job_title: str, status: str = 'Applied', apply_url: str = None, source: str = None, notes: str = None) -> None:
    """Inserts or replaces a new job application in the database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO applications (application_id, job_id, company_name, job_title, status, apply_url, source, notes, application_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (application_id, job_id, company_name, job_title, status, apply_url, source, notes)
        )
        conn.commit()
        logger.info(f"Application saved successfully: {application_id}")
    except Exception as e:
        logger.error(f"Error saving application: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_applications() -> list:
    """Retrieves all application records ordered by application_date descending."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications ORDER BY application_date DESC")
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                "application_id": row["application_id"],
                "job_id": row["job_id"],
                "company_name": row["company_name"],
                "job_title": row["job_title"],
                "application_date": row["application_date"],
                "status": row["status"],
                "apply_url": row["apply_url"],
                "source": row["source"],
                "notes": row["notes"],
                "last_email_id": row["last_email_id"],
                "last_email_subject": row["last_email_subject"],
                "last_email_date": row["last_email_date"],
                "last_checked": row["last_checked"]
            })
        return results
    except Exception as e:
        logger.error(f"Error retrieving applications: {e}")
        raise e
    finally:
        conn.close()

def update_application_status(application_id: str, status: str) -> None:
    """Updates the status of an application in the database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE applications SET status = ? WHERE application_id = ?",
            (status, application_id)
        )
        conn.commit()
        logger.info(f"Updated status of application {application_id} to {status}")
    except Exception as e:
        logger.error(f"Error updating application status: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_application_by_id(application_id: str) -> dict:
    """Retrieves a specific application by its ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications WHERE application_id = ?", (application_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "application_id": row["application_id"],
            "job_id": row["job_id"],
            "company_name": row["company_name"],
            "job_title": row["job_title"],
            "application_date": row["application_date"],
            "status": row["status"],
            "apply_url": row["apply_url"],
            "source": row["source"],
            "notes": row["notes"],
            "last_email_id": row["last_email_id"],
            "last_email_subject": row["last_email_subject"],
            "last_email_date": row["last_email_date"],
            "last_checked": row["last_checked"]
        }
    except Exception as e:
        logger.error(f"Error retrieving application by ID: {e}")
        raise e
    finally:
        conn.close()

def save_resume_cache(resume_hash: str, parsed_profile: dict) -> None:
    """Caches a parsed resume profile in the SQLite database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO resume_cache (resume_hash, parsed_profile, created_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
            (resume_hash, json.dumps(parsed_profile))
        )
        conn.commit()
        logger.info(f"Resume cache saved successfully for hash: {resume_hash}")
    except Exception as e:
        logger.error(f"Error saving resume cache: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_resume_cache(resume_hash: str) -> dict:
    """Retrieves a cached parsed resume profile by its text hash."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT parsed_profile FROM resume_cache WHERE resume_hash = ?", (resume_hash,))
        row = cursor.fetchone()
        if not row:
            return None
        return json.loads(row["parsed_profile"])
    except Exception as e:
        logger.error(f"Error retrieving resume cache: {e}")
        raise e
    finally:
        conn.close()

def save_gmail_credentials(profile_id: str, creds_dict: dict) -> None:
    """Saves or updates Gmail credentials (OAuth tokens) for a profile."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO gmail_credentials (profile_id, token, refresh_token, token_uri, client_id, client_secret, scopes, expiry)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile_id,
                creds_dict.get("token", ""),
                creds_dict.get("refresh_token"),
                creds_dict.get("token_uri"),
                creds_dict.get("client_id"),
                creds_dict.get("client_secret"),
                creds_dict.get("scopes"),
                creds_dict.get("expiry")
            )
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Error saving Gmail credentials: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_gmail_credentials(profile_id: str) -> dict:
    """Retrieves stored Gmail credentials for a profile."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM gmail_credentials WHERE profile_id = ?", (profile_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return dict(row)
    except Exception as e:
        logger.error(f"Error retrieving Gmail credentials: {e}")
        raise e
    finally:
        conn.close()

def delete_gmail_credentials(profile_id: str) -> None:
    """Deletes stored Gmail credentials for a profile."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM gmail_credentials WHERE profile_id = ?", (profile_id,))
        conn.commit()
    except Exception as e:
        logger.error(f"Error deleting Gmail credentials: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def log_processed_email(email_id: str, sender: str, subject: str, body: str, received_date: str, classification: str, matched_application_id: str, confidence_score: float, classification_method: str) -> None:
    """Logs a processed recruiter email in the email_history table."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO email_history (email_id, sender, subject, body, received_date, classification, matched_application_id, confidence_score, classification_method)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (email_id, sender, subject, body, received_date, classification, matched_application_id, confidence_score, classification_method)
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Error logging processed email: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def has_email_been_processed(email_id: str) -> bool:
    """Checks if an email ID has already been logged in the email history."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM email_history WHERE email_id = ?", (email_id,))
        return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking email process state: {e}")
        raise e
    finally:
        conn.close()

def update_application_email_status(application_id: str, status: str, email_id: str, email_subject: str, email_date: str) -> None:
    """Updates the status and email details of a job application."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE applications
            SET status = ?, last_email_id = ?, last_email_subject = ?, last_email_date = ?, last_checked = CURRENT_TIMESTAMP
            WHERE application_id = ?
            """,
            (status, email_id, email_subject, email_date, application_id)
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Error updating application email status: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_email_history() -> list:
    """Retrieves all logged processed email records ordered by processed_at descending."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM email_history ORDER BY processed_at DESC")
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append(dict(row))
        return results
    except Exception as e:
        logger.error(f"Error retrieving email history: {e}")
        raise e
    finally:
        conn.close()

def get_email_monitor_stats() -> dict:
    """Aggregates stats for the email monitor dashboard."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM email_history")
        total_emails = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT matched_application_id) FROM email_history WHERE matched_application_id IS NOT NULL")
        apps_updated = cursor.fetchone()[0]
        
        # Get last checked timestamp across applications
        cursor.execute("SELECT MAX(last_checked) FROM applications")
        last_checked = cursor.fetchone()[0]
        
        return {
            "total_emails_processed": total_emails,
            "applications_updated": apps_updated,
            "last_checked": last_checked
        }
    except Exception as e:
        logger.error(f"Error retrieving monitor stats: {e}")
        raise e
    finally:
        conn.close()

