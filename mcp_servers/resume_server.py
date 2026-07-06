import os
import json
import logging
from fastmcp import FastMCP
from tools.resume_parser import parse_resume_text_with_gemini, extract_resume_details_fallback

def load_dotenv():
    # .env is located at parent directory of mcp_servers
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

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("resume_mcp_server")

# Initialize FastMCP Server
mcp = FastMCP("ResumeParser")

@mcp.tool()
def parse_resume_text(resume_text: str) -> str:
    """Parses a resume's raw text and extracts structured information including name, email, skills, projects, internships, and certifications.
    
    Args:
        resume_text: The plain text of the resume.
    
    Returns:
        A JSON string containing the extracted structured fields.
    """
    logger.info("parse_resume_text called on server.")
    try:
        parsed = parse_resume_text_with_gemini(resume_text)
        return json.dumps(parsed)
    except Exception as e:
        logger.error(f"Error calling Gemini API for resume parsing: {e}. Falling back to rule-based parsing.")
        fallback_result = extract_resume_details_fallback(resume_text)
        return json.dumps(fallback_result)

if __name__ == "__main__":
    mcp.run()
