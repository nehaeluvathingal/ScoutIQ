import os
import re
import logging
import json
from typing import Dict, Any, List, Tuple
from tools.db_tools import (
    get_applications,
    has_email_been_processed,
    log_processed_email,
    update_application_email_status
)

logger = logging.getLogger("email_monitor")

# Mock recruiter emails dataset
MOCK_EMAILS = [
    {
        "id": "mock_email_001",
        "sender": "hr@securetech.com",
        "subject": "Interview Invitation: Software Engineer",
        "body": "Hello Alice, thank you for applying to SecureTech Solutions. We would like to invite you to a technical interview next week. Please select a time slot on our portal.",
        "received_date": "2026-07-01 10:00:00"
    },
    {
        "id": "mock_email_002",
        "sender": "careers@insightcorp.com",
        "subject": "Update on your application",
        "body": "Dear Candidate, thank you for taking the time to apply and interview with InsightCorp. Unfortunately, we have decided to move forward with other candidates whose profiles align more closely with our requirements.",
        "received_date": "2026-07-01 11:30:00"
    },
    {
        "id": "mock_email_003",
        "sender": "recruiter@techvanguard.com",
        "subject": "Offer Details: TechVanguard India",
        "body": "Hi Alice, we are thrilled to offer you the role of Frontend Developer at TechVanguard India! Please find the offer letter details and contract attached.",
        "received_date": "2026-07-01 14:15:00"
    },
    {
        "id": "mock_email_004",
        "sender": "assessments@datahub.com",
        "subject": "HackerRank test invitation - DataHub",
        "body": "Dear Applicant, please complete this online coding assessment link within 48 hours for the Database Engineer opening at DataHub.",
        "received_date": "2026-07-01 15:00:00"
    }
]

def classify_email_rule_based(subject: str, body: str) -> Tuple[str, float]:
    """Runs a fast deterministic keyword/regex match on subject and body.
    
    Returns (classification, confidence_score) or (None, 0.0) if inconclusive.
    """
    text = (subject + " " + body).lower()
    
    # Check for ignore rules first (newsletters, spam keywords, generic marketing)
    ignore_keywords = [
        "newsletter", "unsubscribe", "weekly digest", "promotions", "marketing",
        "special offer", "verify your account", "reset password", "security alert"
    ]
    if any(k in text for k in ignore_keywords):
        return "Ignore", 1.0
        
    # Rejection checks
    rejection_keywords = [
        "not moving forward", "thank you for your interest", "other candidates",
        "regret to inform", "unable to offer you", "not selecting you",
        "decision was difficult", "wish you best of luck"
    ]
    if any(k in text for k in rejection_keywords):
        return "Rejected", 1.0
        
    # Offer checks
    offer_keywords = [
        "offer letter", "official offer", "congratulations! we are pleased",
        "pleased to offer you", "contract details", "employment agreement"
    ]
    if any(k in text for k in offer_keywords):
        return "Offer Received", 1.0
        
    # Interview checks
    interview_keywords = [
        "interview invitation", "schedule an interview", "schedule chat",
        "phone screen", "hiring manager interview", "panel interview",
        "select a time", "calendly.com", "zoom link for interview"
    ]
    if any(k in text for k in interview_keywords):
        return "Interview Scheduled", 1.0
        
    # Assessment checks
    assessment_keywords = [
        "assessment invitation", "coding test", "technical assessment",
        "hackerrank", "codility", "test link", "online test", "pre-employment test"
    ]
    if any(k in text for k in assessment_keywords):
        return "Assessment Received", 1.0
        
    # Application received/confirmation checks
    received_keywords = [
        "application received", "thank you for applying", "received your application",
        "application confirmation", "successfully submitted"
    ]
    if any(k in text for k in received_keywords):
        return "Applied", 1.0
        
    return None, 0.0

def classify_email_with_gemini(subject: str, body: str) -> Tuple[str, float]:
    """Uses Gemini API to classify the email text when rule-based passes are inconclusive."""
    from google import genai
    from google.genai import types
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not configured, falling back to default classification.")
        return "Ignore", 0.5
        
    client = genai.Client()
    prompt = f"""
    Analyze the following email. Classify it into one of the following categories:
    - "Applied" (for application receipts/confirmations)
    - "Assessment Received" (for online tests, hackerrank links, etc.)
    - "Interview Scheduled" (for scheduling chats, invitations, video screens)
    - "Offer Received" (for offer letters, employment agreements)
    - "Rejected" (for rejection emails, thank you but no thank you)
    - "Ignore" (for spam, newsletters, automated warnings, promotions, unrelated updates)
    
    Email Subject: {subject}
    Email Body:
    {body}
    
    Return a valid JSON object with the fields:
    - "classification": The category string exactly as listed above.
    - "confidence_score": A float between 0.0 and 1.0.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        data = json.loads(response.text)
        classification = data.get("classification", "Ignore")
        confidence = float(data.get("confidence_score", 0.8))
        return classification, confidence
    except Exception as e:
        logger.error(f"Gemini email classification error: {e}")
        return "Ignore", 0.5

def match_email_to_application(sender: str, subject: str, body: str, apps: List[Dict[str, Any]]) -> str:
    """Matches the email to one of the user's active tracked applications.
    
    Returns the matched application_id or None.
    """
    text = (sender + " " + subject + " " + body).lower()
    best_match_app_id = None
    best_match_len = 0
    
    for app in apps:
        company_name = app.get("company_name", "").strip()
        if not company_name:
            continue
            
        company_cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', company_name).lower()
        suffixes = ["inc", "co", "corp", "corporation", "ltd", "limited", "solutions", "technologies", "group", "india", "us", "uk"]
        words = [w for w in company_cleaned.split() if w not in suffixes]
        
        match_found = False
        if company_cleaned in text:
            match_found = True
            match_len = len(company_cleaned)
        else:
            for word in words:
                if len(word) >= 3 and word in text:
                    match_found = True
                    match_len = len(word)
                    break
                    
        if match_found:
            if match_len > best_match_len:
                best_match_len = match_len
                best_match_app_id = app["application_id"]
                
    return best_match_app_id

def run_email_monitor_sync(creds: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Runs the email monitoring sync loop.
    
    If creds is provided (Live Gmail Mode), connects using Gmail API.
    Otherwise (Mock Mode), loads from MOCK_EMAILS.
    """
    emails_to_process = []
    
    # 1. Fetch emails depending on mode
    if creds:
        logger.info("Running sync in Live Gmail Mode using Gmail API.")
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            
            google_creds = Credentials(
                token=creds.get("token"),
                refresh_token=creds.get("refresh_token"),
                token_uri=creds.get("token_uri"),
                client_id=creds.get("client_id"),
                client_secret=creds.get("client_secret"),
                scopes=creds.get("scopes", "").split(",") if isinstance(creds.get("scopes"), str) else creds.get("scopes")
            )
            
            service = build('gmail', 'v1', credentials=google_creds)
            # Fetch recent threads/messages (limit to last 20 messages for simplicity and performance)
            results = service.users().messages().list(userId='me', maxResults=20).execute()
            messages = results.get('messages', [])
            
            for msg in messages:
                msg_id = msg['id']
                if has_email_been_processed(msg_id):
                    continue
                    
                msg_data = service.users().messages().get(userId='me', id=msg_id).execute()
                headers = msg_data.get('payload', {}).get('headers', [])
                
                subject = ""
                sender = ""
                for h in headers:
                    if h['name'].lower() == 'subject':
                        subject = h['value']
                    elif h['name'].lower() == 'from':
                        sender = h['value']
                        
                body = msg_data.get('snippet', '')
                received_date = msg_data.get('internalDate', '') # timestamp
                
                emails_to_process.append({
                    "id": msg_id,
                    "sender": sender,
                    "subject": subject,
                    "body": body,
                    "received_date": received_date
                })
        except Exception as e:
            logger.error(f"Failed to query Live Gmail API: {e}. Falling back to empty run.")
            return []
    else:
        logger.info("Running sync in Mock Mode (default).")
        # In Mock Mode, process all MOCK_EMAILS that haven't been processed yet
        for me in MOCK_EMAILS:
            if not has_email_been_processed(me["id"]):
                emails_to_process.append(me)
                
    # 2. Match and classify each fetched email
    apps = get_applications()
    results_logged = []
    
    for email in emails_to_process:
        subject = email["subject"]
        body = email["body"]
        sender = email["sender"]
        email_id = email["id"]
        received_date = email["received_date"]
        
        # Classify: Rule-based first
        classification, confidence = classify_email_rule_based(subject, body)
        method = "Rule-Based"
        
        if not classification:
            # Fallback to Gemini
            classification, confidence = classify_email_with_gemini(subject, body)
            method = "Gemini"
            
        # Match email to application
        matched_app_id = match_email_to_application(sender, subject, body, apps)
        
        # Log email processing in audit trail
        log_processed_email(
            email_id=email_id,
            sender=sender,
            subject=subject,
            body=body,
            received_date=str(received_date),
            classification=classification,
            matched_application_id=matched_app_id,
            confidence_score=confidence,
            classification_method=method
        )
        
        # If matched to a tracked application and classification is NOT Ignore, update application status
        if matched_app_id and classification != "Ignore":
            update_application_email_status(
                application_id=matched_app_id,
                status=classification,
                email_id=email_id,
                email_subject=subject,
                email_date=str(received_date)
            )
            
            # Find matching company name for UI notification
            matched_company = ""
            for app in apps:
                if app["application_id"] == matched_app_id:
                    matched_company = app.get("company_name", "")
                    break
                    
            results_logged.append({
                "email_id": email_id,
                "sender": sender,
                "subject": subject,
                "classification": classification,
                "matched_application_id": matched_app_id,
                "matched_company": matched_company,
                "confidence_score": confidence,
                "classification_method": method,
                "status_updated": True
            })
        else:
            results_logged.append({
                "email_id": email_id,
                "sender": sender,
                "subject": subject,
                "classification": classification,
                "matched_application_id": matched_app_id,
                "matched_company": "",
                "confidence_score": confidence,
                "classification_method": method,
                "status_updated": False
            })
            
    # 3. Retroactively match previously unmatched emails to newly created applications
    try:
        from tools.db_tools import get_email_history
        unmatched_emails = [m for m in get_email_history() if not m.get("matched_application_id")]
        for u_email in unmatched_emails:
            matched_app_id = match_email_to_application(
                u_email.get("sender", ""),
                u_email.get("subject", ""),
                u_email.get("body", ""),
                apps
            )
            if matched_app_id:
                # Update email history with matched application ID
                log_processed_email(
                    email_id=u_email["email_id"],
                    sender=u_email["sender"],
                    subject=u_email["subject"],
                    body=u_email["body"],
                    received_date=u_email["received_date"],
                    classification=u_email["classification"],
                    matched_application_id=matched_app_id,
                    confidence_score=u_email["confidence_score"],
                    classification_method=u_email["classification_method"]
                )
                # Update application status
                update_application_email_status(
                    application_id=matched_app_id,
                    status=u_email["classification"],
                    email_id=u_email["email_id"],
                    email_subject=u_email["subject"],
                    email_date=u_email["received_date"]
                )
                # Add to results_logged so it triggers UI notifications and matches
                results_logged.append({
                    "email_id": u_email["email_id"],
                    "sender": u_email["sender"],
                    "subject": u_email["subject"],
                    "classification": u_email["classification"],
                    "matched_application_id": matched_app_id,
                    "matched_company": next((a["company_name"] for a in apps if a["application_id"] == matched_app_id), ""),
                    "confidence_score": u_email["confidence_score"],
                    "classification_method": u_email["classification_method"],
                    "status_updated": True
                })
    except Exception as e:
        logger.error(f"Error retroactively matching unmatched emails: {e}")
            
    return results_logged
