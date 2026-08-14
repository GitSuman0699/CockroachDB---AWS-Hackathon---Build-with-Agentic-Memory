"""
Mnemosyne — Semantic Memory
Knowledge base with vector search (RAG).
Like human semantic memory: "facts and knowledge I've learned."
"""

import json
import logging
import uuid
from app.database import get_cursor
from app.embeddings import embed_text, format_vector

logger = logging.getLogger(__name__)


def store_knowledge(
    content: str,
    user_id: str = "default",
    source: str = "",
    category: str = "",
    importance: float = 0.5,
    metadata: dict = None,
    _cur=None,
) -> str:
    """
    Store a piece of knowledge in semantic memory.
    
    Args:
        content: The knowledge text
        user_id: User identifier
        source: Where this knowledge came from
        category: Topic/category tag
        importance: 0.0-1.0 importance score
        metadata: Optional metadata
    
    Returns:
        UUID of stored knowledge
    """
    knowledge_id = str(uuid.uuid4())
    embedding = embed_text(content)
    embedding_vec = format_vector(embedding)
    
    query = """INSERT INTO semantic_memories
               (id, user_id, content, source, category, embedding, importance, metadata)
               VALUES (%s, %s, %s, %s, %s, %s::VECTOR(1024), %s, %s)"""
    args = (knowledge_id, user_id, content, source, category,
            embedding_vec, importance, json.dumps(metadata or {}))
    
    if _cur:
        _cur.execute(query, args)
    else:
        with get_cursor() as cur:
            cur.execute(query, args)
    
    logger.debug(f"Stored semantic memory: {content[:50]}...")
    return knowledge_id


def search(
    query: str,
    user_id: str = "default",
    limit: int = 5,
    category: str = None,
    min_importance: float = 0.0,
) -> list[dict]:
    """
    Search semantic memories by vector similarity.
    
    Args:
        query: Search query text
        user_id: User identifier
        limit: Max results
        category: Optional category filter
        min_importance: Minimum importance threshold
    
    Returns:
        List of matching knowledge items with distance scores
    """
    query_embedding = embed_text(query)
    query_vec = format_vector(query_embedding)
    
    with get_cursor() as cur:
        if category:
            cur.execute(
                """SELECT id, content, source, category, importance, 
                          access_count, metadata, created_at,
                          embedding <=> %s::VECTOR(1024) AS distance
                   FROM semantic_memories
                   WHERE user_id = %s AND category = %s AND importance >= %s
                   ORDER BY distance ASC
                   LIMIT %s""",
                (query_vec, user_id, category, min_importance, limit)
            )
        else:
            cur.execute(
                """SELECT id, content, source, category, importance,
                          access_count, metadata, created_at,
                          embedding <=> %s::VECTOR(1024) AS distance
                   FROM semantic_memories
                   WHERE user_id = %s AND importance >= %s
                   ORDER BY distance ASC
                   LIMIT %s""",
                (query_vec, user_id, min_importance, limit)
            )
        rows = cur.fetchall()
    
    # Update access counts for retrieved memories
    if rows:
        ids = [str(row["id"]) for row in rows]
        with get_cursor() as cur:
            cur.execute(
                """UPDATE semantic_memories 
                   SET access_count = access_count + 1,
                       last_accessed_at = now()
                   WHERE id = ANY(%s::UUID[])""",
                (ids,)
            )
    
    return [
        {
            "id": str(row["id"]),
            "content": row["content"],
            "source": row["source"],
            "category": row["category"],
            "importance": float(row["importance"]),
            "access_count": row["access_count"],
            "distance": float(row["distance"]),
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        }
        for row in rows
    ]


def update_importance(memory_id: str, new_importance: float):
    """Update the importance score of a semantic memory."""
    with get_cursor() as cur:
        cur.execute(
            """UPDATE semantic_memories 
               SET importance = %s 
               WHERE id = %s""",
            (new_importance, memory_id)
        )


def store_batch(
    items: list[dict],
    user_id: str = "default",
) -> list[str]:
    """
    Store multiple knowledge items.
    Each item should have: content, source (optional), category (optional)
    
    Returns:
        List of UUIDs
    """
    ids = []
    for item in items:
        mid = store_knowledge(
            content=item["content"],
            user_id=user_id,
            source=item.get("source", ""),
            category=item.get("category", ""),
            importance=item.get("importance", 0.5),
            metadata=item.get("metadata"),
        )
        ids.append(mid)
    return ids


def get_by_id(memory_id: str) -> dict | None:
    """Get a specific semantic memory by ID."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT id, content, source, category, importance,
                      access_count, metadata, created_at
               FROM semantic_memories WHERE id = %s""",
            (memory_id,)
        )
        row = cur.fetchone()
    
    if not row:
        return None
    
    return {
        "id": str(row["id"]),
        "content": row["content"],
        "source": row["source"],
        "category": row["category"],
        "importance": float(row["importance"]),
        "access_count": row["access_count"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
    }
