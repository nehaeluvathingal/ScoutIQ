import os
import sys
import logging
from google.adk import Agent
from google.adk.tools.mcp_tool import McpToolset
from mcp import StdioServerParameters
from tools.db_tools import save_user_profile

logger = logging.getLogger("resume_analyzer")

# Resolve absolute path to the resume MCP server script
SERVER_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "mcp_servers",
        "resume_server.py"
    )
)

# Connect to the Resume MCP Server
resume_toolset = McpToolset(
    connection_params=StdioServerParameters(
        command=sys.executable,
        args=[SERVER_PATH]
    )
)

resume_analyzer_agent = Agent(
    name="ResumeAnalyzerAgent",
    instruction=(
        "You are a professional resume analysis agent.\n"
        "Your task is to parse raw resume text, extract structured profile data, and save it in the database.\n"
        "Follow these steps:\n"
        "1. Call the `parse_resume_text` tool from the ResumeParser MCP server to parse the resume text.\n"
        "2. Once parsed, call the `save_user_profile` tool to persist the profile in the database. "
        "Use 'user_default' as the profile_id unless another ID is provided. Make sure to map all parsed fields "
        "(name, email, skills, projects, internships, certifications) correctly.\n"
        "3. Respond to the user confirming that the resume has been successfully parsed and saved, and return a summarized structured view of the user profile."
    ),
    model="gemini-2.5-flash",
    tools=[resume_toolset, save_user_profile]
)
