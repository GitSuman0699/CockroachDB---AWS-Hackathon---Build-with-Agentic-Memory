"""
Phase 1 — Step 1: CockroachDB Connection Test
Confirms we can connect to CockroachDB Serverless and run a basic query.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import psycopg2
from app.config import settings


def test_connection():
    """Connect to CockroachDB and verify with a simple query."""
    print("=" * 60)
    print("P1.1 — CockroachDB Connection Test")
    print("=" * 60)

    if not settings.cockroachdb_url:
        print("❌ COCKROACHDB_URL not set in .env")
        print("   Get your connection string from:")
        print("   CockroachDB Cloud Console → Connect → Connection string")
        return False

    print(f"\n📡 Connecting to CockroachDB...")
    print(f"   URL: {settings.cockroachdb_url[:50]}...")

    try:
        conn = psycopg2.connect(settings.cockroachdb_url)
        conn.autocommit = True
        cur = conn.cursor()

        # Test 1: Basic query
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"\n✅ Connected successfully!")
        print(f"   Version: {version}")

        # Test 2: Check current user
        cur.execute("SELECT current_user;")
        current_user = cur.fetchone()[0]
        print(f"   User: {current_user}")

        # Test 3: Check current database
        cur.execute("SELECT current_database();")
        db_name = cur.fetchone()[0]
        print(f"   Database: {db_name}")

        # Test 4: Check if vector extension/support is available
        try:
            cur.execute("SELECT '[1.0, 2.0, 3.0]'::VECTOR(3);")
            vector_result = cur.fetchone()[0]
            print(f"\n✅ VECTOR type is supported!")
            print(f"   Test vector: {vector_result}")
        except Exception as e:
            print(f"\n⚠️  VECTOR type test failed: {e}")
            print("   This may require enabling: SET CLUSTER SETTING feature.vector_index.enabled = true;")

        cur.close()
        conn.close()
        print(f"\n{'=' * 60}")
        print("✅ P1.1 PASSED — CockroachDB connection works")
        print(f"{'=' * 60}")
        return True

    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Check your COCKROACHDB_URL in .env")
        print("  2. Ensure your IP is in the allowed list (CockroachDB Cloud Console → Networking)")
        print("  3. Verify the cluster is running")
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
