"""
Mnemosyne — Procedural Memory
Learned patterns, preferences, and behavioral rules.
Like human procedural memory: "how I've learned to do things."
"""

import json
import logging
import uuid
from app.database import get_cursor
from app.embeddings import embed_text, format_vector

logger = logging.getLogger(__name__)


def store_pattern(
    pattern: str,
    pattern_type: str = "preference",
    user_id: str = "default",
    confidence: float = 0.5,
    metadata: dict = None,
) -> str:
    """
    Store a learned pattern or preference.
    
    Args:
        pattern: The pattern text (e.g., "User prefers concise answers")
        pattern_type: 'preference', 'correction', 'workflow', 'style'
        user_id: User identifier
        confidence: 0.0-1.0 confidence score
        metadata: Optional metadata
    
    Returns:
        UUID of stored pattern
    """
    pattern_id = str(uuid.uuid4())
    embedding = embed_text(pattern)
    embedding_vec = format_vector(embedding)
    
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO procedural_memories
               (id, user_id, pattern_type, pattern, embedding, confidence, metadata)
               VALUES (%s, %s, %s, %s, %s::VECTOR(1024), %s, %s)""",
            (pattern_id, user_id, pattern_type, pattern,
             embedding_vec, confidence, json.dumps(metadata or {}))
        )
    
    logger.debug(f"Stored procedural memory ({pattern_type}): {pattern[:50]}...")
    return pattern_id


def search_patterns(
    query: str,
    user_id: str = "default",
    pattern_type: str = None,
    limit: int = 5,
    min_confidence: float = 0.0,
) -> list[dict]:
    """
    Search for relevant patterns by similarity to the current context.
    
    Args:
        query: Current context/query to match against
        user_id: User identifier
        pattern_type: Optional filter by type
        limit: Max results
        min_confidence: Minimum confidence threshold
    
    Returns:
        List of matching patterns with distance scores
    """
    query_embedding = embed_text(query)
    query_vec = format_vector(query_embedding)
    
    with get_cursor() as cur:
        if pattern_type:
            cur.execute(
                """SELECT id, pattern_type, pattern, confidence, 
                          times_applied, metadata, created_at,
                          embedding <=> %s::VECTOR(1024) AS distance
                   FROM procedural_memories
                   WHERE user_id = %s AND pattern_type = %s AND confidence >= %s
                   ORDER BY distance ASC
                   LIMIT %s""",
                (query_vec, user_id, pattern_type, min_confidence, limit)
            )
        else:
            cur.execute(
                """SELECT id, pattern_type, pattern, confidence,
                          times_applied, metadata, created_at,
                          embedding <=> %s::VECTOR(1024) AS distance
                   FROM procedural_memories
                   WHERE user_id = %s AND confidence >= %s
                   ORDER BY distance ASC
                   LIMIT %s""",
                (query_vec, user_id, min_confidence, limit)
            )
        rows = cur.fetchall()
    
    # Update application counts
    if rows:
        ids = [str(row["id"]) for row in rows]
        with get_cursor() as cur:
            cur.execute(
                """UPDATE procedural_memories 
                   SET times_applied = times_applied + 1,
                       last_applied_at = now()
                   WHERE id = ANY(%s::UUID[])""",
                (ids,)
            )
    
    return [
        {
            "id": str(row["id"]),
            "pattern_type": row["pattern_type"],
            "pattern": row["pattern"],
            "confidence": float(row["confidence"]),
            "times_applied": row["times_applied"],
            "distance": float(row["distance"]),
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        }
        for row in rows
    ]


def update_confidence(pattern_id: str, new_confidence: float):
    """Update the confidence score of a pattern."""
    with get_cursor() as cur:
        cur.execute(
            "UPDATE procedural_memories SET confidence = %s WHERE id = %s",
            (new_confidence, pattern_id)
        )


def reinforce_pattern(pattern_id: str, boost: float = 0.1):
    """
    Reinforce a pattern — increase confidence when it's validated.
    Caps at 1.0.
    """
    with get_cursor() as cur:
        cur.execute(
            """UPDATE procedural_memories 
               SET confidence = LEAST(confidence + %s, 1.0),
                   times_applied = times_applied + 1,
                   last_applied_at = now()
               WHERE id = %s""",
            (boost, pattern_id)
        )


def get_all_patterns(
    user_id: str = "default",
    pattern_type: str = None,
) -> list[dict]:
    """Get all patterns, optionally filtered by type."""
    with get_cursor() as cur:
        if pattern_type:
            cur.execute(
                """SELECT id, pattern_type, pattern, confidence, 
                          times_applied, created_at
                   FROM procedural_memories
                   WHERE user_id = %s AND pattern_type = %s
                   ORDER BY confidence DESC, times_applied DESC""",
                (user_id, pattern_type)
            )
        else:
            cur.execute(
                """SELECT id, pattern_type, pattern, confidence,
                          times_applied, created_at
                   FROM procedural_memories
                   WHERE user_id = %s
                   ORDER BY confidence DESC, times_applied DESC""",
                (user_id,)
            )
        rows = cur.fetchall()
    
    return [
        {
            "id": str(row["id"]),
            "pattern_type": row["pattern_type"],
            "pattern": row["pattern"],
            "confidence": float(row["confidence"]),
            "times_applied": row["times_applied"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        }
        for row in rows
    ]
