import logging
from google.adk import Agent
from tools.db_tools import get_user_profile
from tools.job_search import search_jobs

logger = logging.getLogger("discovery_agent")

job_discovery_agent = Agent(
    name="JobDiscoveryAgent",
    instruction=(
        "You are a Career Navigator Job Discovery Agent.\n"
        "Your task is to find and rank job postings matching a user's skills.\n"
        "Follow these steps:\n"
        "1. Retrieve the user profile from the database using `get_user_profile` with profile_id='user_default'.\n"
        "2. Extract the user's skills list and pass it to the `search_jobs` tool to discover matching job postings.\n"
        "3. For each discovered job, analyze how well the job requirements match the user's skills. Calculate a 'match_score' between 0.0 and 1.0 (where 1.0 is a perfect match).\n"
        "4. Rank the jobs by match_score in descending order.\n"
        "5. Output a structured list of jobs. For each job, include: job_id, title, company, location, skills_required, match_score, and a short explanation of the score."
    ),
    model="gemini-2.5-flash",
    tools=[get_user_profile, search_jobs]
)
