import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.database import SCHEMA_SQL, get_connection

def debug_schema():
    statements = SCHEMA_SQL.split(";")
    print(f"Total statements found: {len(statements)}")
    
    with get_connection() as conn:
        cur = conn.cursor()
        for i, statement in enumerate(statements):
            statement = statement.strip()
            print(f"Statement {i} length: {len(statement)}")
            if statement and not statement.startswith("--"):
                try:
                    print(f"Executing:\n{statement[:100]}...")
                    cur.execute(statement + ";")
                    print("  -> SUCCESS")
                except Exception as e:
                    print(f"  -> ERROR: {e}")

if __name__ == "__main__":
    debug_schema()
