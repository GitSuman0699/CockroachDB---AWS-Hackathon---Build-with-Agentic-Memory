"""
Mnemosyne — Episodic Memory
Stores conversation history with session management.
Like human episodic memory: "what happened in my conversations."
"""

import json
import logging
import uuid
from datetime import datetime
from app.database import get_cursor
from app.embeddings import embed_text, format_vector

logger = logging.getLogger(__name__)


def store_message(
    session_id: str,
    role: str,
    content: str,
    user_id: str = "default",
    metadata: dict = None,
    generate_embedding: bool = True,
) -> str:
    """
    Store a conversation message.
    
    Args:
        session_id: Conversation session identifier
        role: 'user', 'assistant', or 'system'
        content: Message text
        user_id: User identifier
        metadata: Optional metadata dict
        generate_embedding: Whether to embed the message (for search)
    
    Returns:
        The UUID of the stored message
    """
    msg_id = str(uuid.uuid4())
    embedding_val = None
    
    if generate_embedding and content.strip():
        try:
            embedding = embed_text(content)
            embedding_val = format_vector(embedding)
        except Exception as e:
            logger.warning(f"Failed to embed message: {e}")
    
    with get_cursor() as cur:
        if embedding_val:
            cur.execute(
                """INSERT INTO episodic_memories 
                   (id, session_id, user_id, role, content, embedding, metadata)
                   VALUES (%s, %s, %s, %s, %s, %s::VECTOR(1024), %s)""",
                (msg_id, session_id, user_id, role, content, embedding_val,
                 json.dumps(metadata or {}))
            )
        else:
            cur.execute(
                """INSERT INTO episodic_memories 
                   (id, session_id, user_id, role, content, metadata)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (msg_id, session_id, user_id, role, content,
                 json.dumps(metadata or {}))
            )
    
    logger.debug(f"Stored {role} message in session {session_id[:8]}...")
    return msg_id


def get_session_history(
    session_id: str,
    limit: int = 50,
    user_id: str = "default",
) -> list[dict]:
    """
    Get conversation history for a session, ordered by time.
    
    Returns:
        List of message dicts with role, content, created_at
    """
    with get_cursor() as cur:
        cur.execute(
            """SELECT id, role, content, metadata, created_at 
               FROM episodic_memories 
               WHERE session_id = %s AND user_id = %s
               ORDER BY created_at ASC
               LIMIT %s""",
            (session_id, user_id, limit)
        )
        rows = cur.fetchall()
    
    return [
        {
            "id": str(row["id"]),
            "role": row["role"],
            "content": row["content"],
            "metadata": row["metadata"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        }
        for row in rows
    ]


def search_similar_conversations(
    query: str,
    user_id: str = "default",
    limit: int = 5,
    session_id: str = None,
) -> list[dict]:
    """
    Search past conversations by semantic similarity.
    Optionally exclude current session.
    
    Returns:
        List of matching messages with distance score
    """
    query_embedding = embed_text(query)
    query_vec = format_vector(query_embedding)
    
    with get_cursor() as cur:
        if session_id:
            cur.execute(
                """SELECT id, session_id, role, content, metadata, created_at,
                          embedding <=> %s::VECTOR(1024) AS distance
                   FROM episodic_memories
                   WHERE user_id = %s AND session_id != %s AND embedding IS NOT NULL
                   ORDER BY distance ASC
                   LIMIT %s""",
                (query_vec, user_id, session_id, limit)
            )
        else:
            cur.execute(
                """SELECT id, session_id, role, content, metadata, created_at,
                          embedding <=> %s::VECTOR(1024) AS distance
                   FROM episodic_memories
                   WHERE user_id = %s AND embedding IS NOT NULL
                   ORDER BY distance ASC
                   LIMIT %s""",
                (query_vec, user_id, limit)
            )
        rows = cur.fetchall()
    
    return [
        {
            "id": str(row["id"]),
            "session_id": row["session_id"],
            "role": row["role"],
            "content": row["content"],
            "distance": float(row["distance"]),
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        }
        for row in rows
    ]


def list_sessions(user_id: str = "default", limit: int = 20) -> list[dict]:
    """List recent sessions with message counts."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT session_id, 
                      COUNT(*) as message_count,
                      MIN(created_at) as started_at,
                      MAX(created_at) as last_message_at
               FROM episodic_memories
               WHERE user_id = %s
               GROUP BY session_id
               ORDER BY MAX(created_at) DESC
               LIMIT %s""",
            (user_id, limit)
        )
        rows = cur.fetchall()
    
    return [
        {
            "session_id": row["session_id"],
            "message_count": row["message_count"],
            "started_at": row["started_at"].isoformat() if row["started_at"] else None,
            "last_message_at": row["last_message_at"].isoformat() if row["last_message_at"] else None,
        }
        for row in rows
    ]


def get_session_summary(session_id: str, user_id: str = "default") -> str:
    """Get a text summary of a session's messages (for consolidation)."""
    history = get_session_history(session_id, limit=100, user_id=user_id)
    if not history:
        return ""
    
    lines = []
    for msg in history:
        role_label = "User" if msg["role"] == "user" else "Assistant"
        lines.append(f"{role_label}: {msg['content'][:200]}")
    
    return "\n".join(lines)
