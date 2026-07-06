import os
import sys
import uvicorn
from database.connection import init_db

def load_dotenv():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip("'\"")

def run_server():
    """Starts the FastAPI development server."""
    print("Loading Environment Variables...")
    load_dotenv()
    print("Initializing Database...")
    init_db()
    print("Starting ScoutIQ API Server on http://127.0.0.1:8000")
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        print("Initializing database schema...")
        init_db()
        print("Database initialized successfully.")
    else:
        run_server()
