"""
Phase 1 — Step 4: End-to-End Pipeline Test
Wires the full pipeline together:
  text → embed (Bedrock Titan) → store (CockroachDB) → semantic query → chat (Bedrock Claude) → print

This is the critical integration test that proves the entire memory pipeline works.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import uuid
import boto3
import psycopg2
from app.config import settings

# Embedding dimension must match Titan V2 config
EMBEDDING_DIM = 1024


def get_bedrock_client():
    """Create a Bedrock Runtime client."""
    return boto3.client(
        "bedrock-runtime",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
    )


def generate_embedding(client, text: str) -> list[float]:
    """Generate an embedding for the given text using Titan V2."""
    response = client.invoke_model(
        body=json.dumps({
            "inputText": text,
            "dimensions": EMBEDDING_DIM,
            "normalize": True,
        }),
        modelId=settings.bedrock_embedding_model_id,
        accept="application/json",
        contentType="application/json",
    )
    return json.loads(response["body"].read())["embedding"]


def chat_with_context(client, question: str, context: str) -> str:
    """Ask Claude a question with retrieved context (RAG pattern)."""
    prompt = f"""You are a helpful assistant. Answer the question based ONLY on the 
provided context. If the context doesn't contain enough information, say so.

Context:
{context}

Question: {question}

Answer:"""

    response = client.converse(
        modelId=settings.bedrock_chat_model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 300, "temperature": 0.3},
    )
    return response["output"]["message"]["content"][0]["text"]


def test_e2e_pipeline():
    """Run the full text → embed → store → query → chat → print pipeline."""
    print("=" * 60)
    print("P1.4 — End-to-End Pipeline Test")
    print("=" * 60)

    bedrock = get_bedrock_client()
    conn = psycopg2.connect(settings.cockroachdb_url)
    conn.autocommit = True
    cur = conn.cursor()

    try:
        # ── Step 1: Setup ──────────────────────────────────────────
        print("\n📦 Setting up test table...")
        cur.execute("DROP TABLE IF EXISTS p1_e2e_test;")
        cur.execute(f"""
            CREATE TABLE p1_e2e_test (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                content TEXT NOT NULL,
                embedding VECTOR({EMBEDDING_DIM}) NOT NULL,
                created_at TIMESTAMPTZ DEFAULT now()
            );
        """)
        cur.execute("CREATE VECTOR INDEX ON p1_e2e_test (embedding);")
        print("   ✅ Table + vector index created")

        # ── Step 2: Embed and store knowledge ──────────────────────
        knowledge_chunks = [
            "CockroachDB is a distributed SQL database that survives any failure. "
            "It provides serializable isolation, horizontal scaling, and low-latency reads.",

            "CockroachDB uses the Raft consensus protocol for replication. "
            "Data is automatically split into ranges and distributed across nodes.",

            "Amazon Bedrock is a fully managed service for foundation models. "
            "It supports models from Anthropic, Amazon, Meta, and others.",

            "Python is a programming language widely used in AI and machine learning. "
            "It has libraries like NumPy, pandas, and scikit-learn.",
        ]

        print(f"\n📝 Embedding and storing {len(knowledge_chunks)} knowledge chunks...")
        for i, chunk in enumerate(knowledge_chunks):
            embedding = generate_embedding(bedrock, chunk)
            embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"

            cur.execute(
                "INSERT INTO p1_e2e_test (content, embedding) VALUES (%s, %s::VECTOR);",
                (chunk, embedding_str)
            )
            print(f"   [{i+1}/{len(knowledge_chunks)}] Embedded + stored: {chunk[:60]}...")

        print("   ✅ All chunks embedded and stored")

        # ── Step 3: Semantic search ────────────────────────────────
        query = "How does CockroachDB handle data replication?"
        print(f"\n🔍 Semantic search for: '{query}'")

        query_embedding = generate_embedding(bedrock, query)
        query_embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

        cur.execute(f"""
            SELECT content, embedding <=> %s::VECTOR({EMBEDDING_DIM}) AS distance
            FROM p1_e2e_test
            ORDER BY embedding <=> %s::VECTOR({EMBEDDING_DIM})
            LIMIT 2;
        """, (query_embedding_str, query_embedding_str))

        results = cur.fetchall()
        print("\n   Top 2 results:")
        retrieved_context = ""
        for content, distance in results:
            print(f"   • [dist={distance:.4f}] {content[:80]}...")
            retrieved_context += content + "\n"

        # ── Step 4: RAG — Feed context to Claude ───────────────────
        print(f"\n💬 Asking Claude with retrieved context...")
        answer = chat_with_context(bedrock, query, retrieved_context)
        print(f"\n   Question: {query}")
        print(f"   Answer: {answer}")

        # ── Step 5: Verify the chain ───────────────────────────────
        print("\n📊 Pipeline summary:")
        print("   1. Text → Bedrock Titan V2 → 1024-dim embedding    ✅")
        print("   2. Embedding → CockroachDB VECTOR column            ✅")
        print("   3. Query → Embed → Cosine similarity search         ✅")
        print("   4. Retrieved context → Bedrock Claude → Answer      ✅")

        # Cleanup
        print("\n🗑️  Cleaning up...")
        cur.execute("DROP TABLE IF EXISTS p1_e2e_test;")

        print(f"\n{'=' * 60}")
        print("✅ P1.4 PASSED — Full RAG pipeline works end-to-end!")
        print(f"{'=' * 60}")
        return True

    except Exception as e:
        print(f"\n❌ E2E pipeline failed: {e}")
        import traceback
        traceback.print_exc()

        try:
            cur.execute("DROP TABLE IF EXISTS p1_e2e_test;")
        except Exception:
            pass

        return False

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    success = test_e2e_pipeline()
    sys.exit(0 if success else 1)
