import os
import sqlite3
from typing import Generator

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "career_navigator.db")
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")

def get_db_connection() -> sqlite3.Connection:
    """Returns a connection to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Initializes the database schema if it doesn't already exist."""
    conn = get_db_connection()
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        
        # Apply migrations for applications table if columns don't exist
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(applications)")
        existing_cols = [row["name"] for row in cursor.fetchall()]
        
        new_cols = {
            "last_email_id": "TEXT",
            "last_email_subject": "TEXT",
            "last_email_date": "TIMESTAMP",
            "last_checked": "TIMESTAMP"
        }
        for col, col_type in new_cols.items():
            if col not in existing_cols:
                cursor.execute(f"ALTER TABLE applications ADD COLUMN {col} {col_type}")
                
        conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
