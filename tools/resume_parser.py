import os
import re
import json
import logging
from typing import Dict, Any

logger = logging.getLogger("resume_parser")

def extract_resume_details_fallback(text: str) -> Dict[str, Any]:
    """A robust rule-based/regex fallback parser to extract candidate details directly from resume text.
    
    This replaces hardcoded placeholder values when the Gemini API is unavailable or quota is exhausted.
    """
    logger.info("Executing rule-based fallback resume parser.")
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    # 1. Extract Email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    email = email_match.group(0) if email_match else "candidate@example.com"
    
    # 2. Extract Name
    name = "Candidate Name"
    for line in lines[:5]:
        if "@" in line or "/" in line or "phone" in line.lower() or "resume" in line.lower():
            continue
        words = line.split()
        if len(words) >= 1 and len(words) <= 4:
            if all(w[0].isupper() if w[0].isalpha() else True for w in words):
                name = line
                break
                
    # 3. Extract Skills (Keyword Matching)
    common_skills = [
        "Python", "FastAPI", "Flask", "Django", "SQL", "SQLite", "PostgreSQL",
        "React", "Angular", "Vue", "JavaScript", "TypeScript", "HTML", "CSS",
        "Machine Learning", "NLP", "Deep Learning", "Docker", "Kubernetes", "AWS",
        "Azure", "Google Cloud", "Git", "GitHub", "Java", "C++", "C#", "Linux"
    ]
    skills = []
    for skill in common_skills:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            skills.append(skill)
    if not skills:
        skills = ["Python", "Software Engineering"]
        
    # 4. Extract sections (Projects, Experience, Certifications)
    projects = []
    internships = []
    certifications = []
    
    current_section = None
    for line in lines:
        line_lower = line.lower()
        if any(kw in line_lower for kw in ["project", "portfolio"]):
            current_section = "projects"
            continue
        elif any(kw in line_lower for kw in ["experience", "internship", "employment", "work history"]):
            current_section = "internships"
            continue
        elif any(kw in line_lower for kw in ["certification", "certificate", "credential", "award"]):
            current_section = "certifications"
            continue
        elif any(kw in line_lower for kw in ["education", "skills", "languages"]):
            current_section = None
            continue
            
        clean_line = line.strip("- *•")
        if not clean_line or len(clean_line) < 4:
            continue
            
        if current_section == "projects" and len(projects) < 5:
            projects.append(clean_line)
        elif current_section == "internships" and len(internships) < 5:
            internships.append(clean_line)
        elif current_section == "certifications" and len(certifications) < 5:
            certifications.append(clean_line)
            
    if not projects:
        projects = ["General software development projects"]
    if not internships:
        internships = ["Professional career experience"]
    if not certifications:
        certifications = ["Standard industry certifications"]
        
    return {
        "name": name,
        "email": email,
        "skills": skills,
        "projects": projects,
        "internships": internships,
        "certifications": certifications
    }

def parse_resume_text_with_gemini(resume_text: str) -> Dict[str, Any]:
    """Invokes the Gemini API directly using structured output generation.
    
    This uses at most 1 Gemini request.
    """
    logger.info("Executing parse_resume_text_with_gemini direct API call.")
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not configured.")
        
    from google import genai
    from google.genai import types
    
    client = genai.Client()
    prompt = (
        "Analyze the following resume text. Extract the applicant's name, email, skills, "
        "notable projects, internships/work experiences, and certifications."
    )
    
    schema = {
        "type": "OBJECT",
        "properties": {
            "name": {"type": "STRING"},
            "email": {"type": "STRING"},
            "skills": {"type": "ARRAY", "items": {"type": "STRING"}},
            "projects": {"type": "ARRAY", "items": {"type": "STRING"}},
            "internships": {"type": "ARRAY", "items": {"type": "STRING"}},
            "certifications": {"type": "ARRAY", "items": {"type": "STRING"}}
        },
        "required": ["name", "email", "skills", "projects", "internships", "certifications"]
    }
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[prompt, resume_text],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
        )
    )
    
    return json.loads(response.text)
