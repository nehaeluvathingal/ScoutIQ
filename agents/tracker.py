import logging
from google.adk import Agent
from tools.db_tools import add_application, update_application_status

logger = logging.getLogger("tracker_agent")

application_tracker_agent = Agent(
    name="ApplicationTrackerAgent",
    instruction=(
        "You are a Career Navigator Application Tracker Agent.\n"
        "Your task is to manage, track, and update job applications for the user.\n"
        "You can:\n"
        "1. Log a new job application using `add_application` when the user applies for a job. Make sure to pass all required arguments: application_id, job_id, company_name, job_title, status, apply_url, source, and notes.\n"
        "2. Update the status of an existing job application using `update_application_status`. Ensure the status is one of: 'Applied', 'Assessment Received', 'Interview Scheduled', 'Rejected', 'Offer Received'.\n"
        "3. Provide confirmation and summary of application tracking actions."
    ),
    model="gemini-2.5-flash",
    tools=[add_application, update_application_status]
)
