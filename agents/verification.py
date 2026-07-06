import logging
from google.adk import Agent
from tools.company_verifier import verify_company
from tools.db_tools import save_company_verification

logger = logging.getLogger("verification_agent")

company_verification_agent = Agent(
    name="CompanyVerificationAgent",
    instruction=(
        "You are a Company Verification Agent.\n"
        "Your task is to analyze the safety, legitimacy, and trust score of companies, and save the results in the database.\n"
        "Follow these steps:\n"
        "1. For any company name provided, check its trust signals by calling the `verify_company` tool.\n"
        "2. Save the verification result in the database using `save_company_verification`. Generate a unique company_id (e.g., 'company_' + name in lowercase/no spaces).\n"
        "3. Output a verification report summarizing the trust score, safety flags (if any), is_suspicious flag, and notes."
    ),
    model="gemini-2.5-flash",
    tools=[verify_company, save_company_verification]
)
