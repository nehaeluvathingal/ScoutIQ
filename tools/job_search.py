import logging
from typing import List, Dict, Any

logger = logging.getLogger("job_search")

MOCK_JOBS = [
    {
        "id": "job_001",
        "title": "Software Engineer (FastAPI & Python)",
        "company": "SecureTech Solutions",
        "location": "Seattle",
        "salary": 130000.0,
        "work_mode": "Remote",
        "description": "Develop and maintain robust APIs using Python and FastAPI. Familiarity with SQL and cloud deployments is a plus.",
        "skills_required": ["Python", "FastAPI", "SQL"]
    },
    {
        "id": "job_002",
        "title": "Data Scientist",
        "company": "InsightCorp",
        "location": "Austin",
        "salary": 140000.0,
        "work_mode": "Hybrid",
        "description": "Build and optimize machine learning models for predictive analytics. Python experience is required.",
        "skills_required": ["Python", "Machine Learning"]
    },
    {
        "id": "job_003",
        "title": "Cloud Architect",
        "company": "CloudWorks",
        "location": "Boston",
        "salary": 160000.0,
        "work_mode": "Onsite",
        "description": "Design and architect secure cloud infrastructures. Expert knowledge of AWS and Kubernetes is essential.",
        "skills_required": ["AWS", "Kubernetes"]
    },
    {
        "id": "job_004",
        "title": "Full Stack Developer",
        "company": "WebCraft",
        "location": "Denver",
        "salary": 105000.0,
        "work_mode": "Remote",
        "description": "Develop front-end layouts using React and backend systems with Python.",
        "skills_required": ["React", "Python", "JavaScript"]
    },
    {
        "id": "job_005",
        "title": "Database Engineer",
        "company": "DataHub",
        "location": "Atlanta",
        "salary": 115000.0,
        "work_mode": "Onsite",
        "description": "Administer and optimize high-throughput relational databases. Strong SQL skills required.",
        "skills_required": ["SQL", "PostgreSQL"]
    },
    {
        "id": "job_006",
        "title": "Python Scripting Specialist",
        "company": "Shadowy Finance Group",
        "location": "Unknown Location",
        "salary": 70000.0,
        "work_mode": "Remote",
        "description": "Need developer to build fast script to scrap data. Paying in Crypto. Mismatching domains okay.",
        "skills_required": ["Python", "Web Scraping"]
    },
    {
        "id": "job_007",
        "title": "QA Automation Engineer",
        "company": "QualityFirst",
        "location": "Dallas",
        "salary": 95000.0,
        "work_mode": "Hybrid",
        "description": "Write automated test scripts for APIs and web UIs using Python and Selenium.",
        "skills_required": ["Python", "Selenium"]
    },
    {
        "id": "job_008",
        "title": "React Frontend Developer",
        "company": "AppMakers",
        "location": "Miami",
        "salary": 110000.0,
        "work_mode": "Remote",
        "description": "Build modern interfaces with React, TypeScript, and TailwindCSS.",
        "skills_required": ["React", "TypeScript", "CSS"]
    },
    {
        "id": "job_009",
        "title": "DevOps Engineer",
        "company": "DeployBot",
        "location": "Chicago",
        "salary": 145000.0,
        "work_mode": "Hybrid",
        "description": "Orchestrate release pipelines, build Docker files, and coordinate Kubernetes deployments.",
        "skills_required": ["Docker", "Kubernetes", "Git"]
    },
    {
        "id": "job_010",
        "title": "ML Operations Engineer",
        "company": "Intelligence Labs",
        "location": "Los Angeles",
        "salary": 155000.0,
        "work_mode": "Onsite",
        "description": "Deploy and maintain machine learning models in production containers.",
        "skills_required": ["Python", "Machine Learning", "Docker"]
    },
    {
        "id": "job_011",
        "title": "Senior Backend Engineer (Python & FastAPI)",
        "company": "TechVanguard India",
        "location": "Bangalore",
        "salary": 120000.0,
        "work_mode": "Remote",
        "description": "Develop scalable web services and APIs using Python, FastAPI, and PostgreSQL. Position is fully remote with team hubs in Bangalore.",
        "skills_required": ["Python", "FastAPI", "SQL"]
    },
    {
        "id": "job_012",
        "title": "Machine Learning Scientist",
        "company": "AI Innovations",
        "location": "Bangalore",
        "salary": 140000.0,
        "work_mode": "Hybrid",
        "description": "Work on state-of-the-art LLM fine-tuning and retrieval-augmented generation. Hybrid model based out of Bangalore.",
        "skills_required": ["Python", "Machine Learning"]
    },
    {
        "id": "job_013",
        "title": "React Developer",
        "company": "PixelPerfect Studios",
        "location": "Bangalore",
        "salary": 95000.0,
        "work_mode": "Onsite",
        "description": "Build high-performance web frontends. Located onsite at our electronic city campus in Bangalore.",
        "skills_required": ["React", "JavaScript", "CSS"]
    }
]

def search_jobs(skills: List[str]) -> List[Dict[str, Any]]:
    """Simulates searching an external job board.
    
    Filters mock jobs that share at least one skill keyword with the user's skills.
    If no matching skills, returns all jobs.
    """
    logger.info(f"Searching jobs with skills: {skills}")
    matched = []
    user_skills_lower = [s.lower() for s in skills]
    
    for job in MOCK_JOBS:
        overlap = [req for req in job["skills_required"] if req.lower() in user_skills_lower]
        if overlap:
            matched.append(job)
            
    if not matched:
        return MOCK_JOBS
        
    return matched

def get_job_by_id(job_id: str) -> Dict[str, Any]:
    """Retrieves a mock job by its ID. Returns None if not found."""
    for job in MOCK_JOBS:
        if job["id"] == job_id:
            return job
    return None
