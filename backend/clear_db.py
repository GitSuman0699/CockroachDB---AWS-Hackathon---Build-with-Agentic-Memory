"""
Utility script to clean all CockroachDB memory tables for a clean test/demo state.
"""
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.database import get_cursor

def clear_database():
    tables = [
        "consolidation_log",
        "working_memory",
        "procedural_memories",
        "semantic_memories",
        "episodic_memories",
    ]
    with get_cursor() as cur:
        for table in tables:
            cur.execute(f"DELETE FROM {table};")
    print("[SUCCESS] CockroachDB memory tables cleared successfully. Database is 100% clean and ready for demo!")

if __name__ == "__main__":
    clear_database()
