"""
Phase 1 — Step 2: Vector Operations Test
Creates a table with a VECTOR column, inserts test data,
and runs a similarity search to confirm distributed vector indexing works.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import psycopg2
from app.config import settings


def test_vector_operations():
    """Create a VECTOR table, insert data, and run similarity search."""
    print("=" * 60)
    print("P1.2 — CockroachDB Vector Operations Test")
    print("=" * 60)

    conn = psycopg2.connect(settings.cockroachdb_url)
    conn.autocommit = True
    cur = conn.cursor()

    try:
        # Step 1: Drop test table if it exists
        print("\n🗑️  Cleaning up any previous test table...")
        cur.execute("DROP TABLE IF EXISTS p1_vector_test;")

        # Step 2: Create table with VECTOR column and vector index
        print("📦 Creating table with VECTOR(3) column...")
        cur.execute("""
            CREATE TABLE p1_vector_test (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                content TEXT NOT NULL,
                embedding VECTOR(3) NOT NULL,
                created_at TIMESTAMPTZ DEFAULT now()
            );
        """)
        print("✅ Table created successfully")

        # Step 3: Create vector index
        print("📊 Creating vector index...")
        cur.execute("""
            CREATE VECTOR INDEX ON p1_vector_test (embedding);
        """)
        print("✅ Vector index created successfully")

        # Step 4: Insert test vectors
        print("\n📝 Inserting test vectors...")
        test_data = [
            ("cat", "[1.0, 0.0, 0.0]"),
            ("dog", "[0.9, 0.1, 0.0]"),
            ("car", "[0.0, 1.0, 0.0]"),
            ("truck", "[0.0, 0.9, 0.1]"),
            ("flower", "[0.0, 0.0, 1.0]"),
        ]

        for content, embedding in test_data:
            cur.execute(
                "INSERT INTO p1_vector_test (content, embedding) VALUES (%s, %s);",
                (content, embedding)
            )
            print(f"   Inserted: {content} → {embedding}")

        # Step 5: Verify data
        cur.execute("SELECT count(*) FROM p1_vector_test;")
        count = cur.fetchone()[0]
        print(f"\n✅ {count} rows inserted")

        # Step 6: Run similarity search (cosine distance)
        print("\n🔍 Running similarity search...")
        print("   Query: 'What is similar to [0.95, 0.05, 0.0]?' (should match cat, dog)")
        query_vector = "[0.95, 0.05, 0.0]"

        cur.execute("""
            SELECT content, embedding, embedding <=> %s::VECTOR(3) AS cosine_distance
            FROM p1_vector_test
            ORDER BY embedding <=> %s::VECTOR(3)
            LIMIT 3;
        """, (query_vector, query_vector))

        results = cur.fetchall()
        print("\n   Results (closest first):")
        for content, embedding, distance in results:
            print(f"   • {content:10s} | distance: {distance:.4f} | embedding: {embedding}")

        # Step 7: Run another similarity search (L2 distance)
        print("\n🔍 Running L2 distance search...")
        print("   Query: 'What is similar to [0.0, 0.95, 0.05]?' (should match car, truck)")
        query_vector2 = "[0.0, 0.95, 0.05]"

        cur.execute("""
            SELECT content, embedding <-> %s::VECTOR(3) AS l2_distance
            FROM p1_vector_test
            ORDER BY embedding <-> %s::VECTOR(3)
            LIMIT 3;
        """, (query_vector2, query_vector2))

        results2 = cur.fetchall()
        print("\n   Results (closest first):")
        for content, distance in results2:
            print(f"   • {content:10s} | L2 distance: {distance:.4f}")

        # Cleanup
        print("\n🗑️  Cleaning up test table...")
        cur.execute("DROP TABLE IF EXISTS p1_vector_test;")

        print(f"\n{'=' * 60}")
        print("✅ P1.2 PASSED — Vector insert + similarity search works")
        print(f"{'=' * 60}")
        return True

    except Exception as e:
        print(f"\n❌ Vector operations failed: {e}")
        import traceback
        traceback.print_exc()

        # Attempt cleanup
        try:
            cur.execute("DROP TABLE IF EXISTS p1_vector_test;")
        except Exception:
            pass

        return False

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    success = test_vector_operations()
    sys.exit(0 if success else 1)
