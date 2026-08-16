---
name: cockroachdb-agent
description: Machine-executable CockroachDB Agent Skill for Distributed Vector Indexing, ACID Transaction Resilience, and Memory Schema Operations.
version: 1.0.0
---

# CockroachDB Agent Skill 🪳

This skill encodes machine-executable CockroachDB operational knowledge and architectural standards for AI agents (Antigravity IDE, Cursor, Claude Code, and LangChain).

## 1. Distributed Vector Indexing Specification
When creating or querying vector embeddings in CockroachDB:
- **Data Type:** `VECTOR(1024)` (matches Amazon Titan Embeddings V2).
- **Index Creation:**
  ```sql
  CREATE VECTOR INDEX IF NOT EXISTS idx_semantic_embedding ON semantic_memories (embedding);
  CREATE VECTOR INDEX IF NOT EXISTS idx_procedural_embedding ON procedural_memories (embedding) WHERE embedding IS NOT NULL;
  ```
- **Similarity Search Query:** Use native Cosine Distance `<=>`:
  ```sql
  SELECT id, content, category,
         embedding <=> %s::VECTOR(1024) AS distance
  FROM semantic_memories
  WHERE user_id = %s
  ORDER BY distance ASC
  LIMIT %s;
  ```

## 2. Distributed ACID Transaction Resilience (SQLSTATE 40001)
In CockroachDB's serializable isolation level, concurrent transactions that conflict will return `40001` (Serialization Failure).
Always wrap multi-table state mutations in an exponential backoff retry loop:

```python
import time
import psycopg2.errors

MAX_RETRIES = 3

for attempt in range(MAX_RETRIES):
    try:
        with transaction_cursor() as cur:
            # Multi-table atomic mutation
            cur.execute("INSERT INTO semantic_memories (...) VALUES (...);")
            cur.execute("UPDATE working_memory SET ...;")
            break  # Success
    except psycopg2.errors.SerializationFailure:
        if attempt == MAX_RETRIES - 1:
            raise
        time.sleep(0.05 * (2 ** attempt))  # Exponential backoff
```

## 3. CockroachDB Cloud Managed MCP & CLI Integration
- **Managed MCP Server:** Connect directly via `https://cockroachlabs.cloud/mcp`.
- **ccloud CLI Commands:**
  - `ccloud cluster list --output json`
  - `ccloud sql --cluster <cluster-name> --execute "<sql>"`
