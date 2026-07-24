"""
Mnemosyne — Working Memory
Active context management for current conversation.
Like human working memory: "what I'm currently thinking about."
"""

import json
import logging
from app.database import get_cursor

logger = logging.getLogger(__name__)


def set_context(
    session_id: str,
    key: str,
    value: str,
    user_id: str = "default",
    priority: float = 0.5,
    ttl_seconds: int = 3600,
):
    """
    Set a working memory context item. Upserts on (session_id, key).
    
    Args:
        session_id: Current session
        key: Context key (e.g., 'current_topic', 'user_intent', 'active_entities')
        value: Context value
        user_id: User identifier
        priority: 0.0-1.0 (higher = stays longer in context window)
        ttl_seconds: Auto-expire after this many seconds
    """
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO working_memory 
               (session_id, user_id, key, value, priority, ttl_seconds, 
                expires_at, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, 
                       now() + INTERVAL '1 second' * %s, now())
               ON CONFLICT (session_id, key) DO UPDATE SET
                   value = EXCLUDED.value,
                   priority = EXCLUDED.priority,
                   ttl_seconds = EXCLUDED.ttl_seconds,
                   expires_at = now() + INTERVAL '1 second' * EXCLUDED.ttl_seconds,
                   created_at = now()""",
            (session_id, user_id, key, value, priority, ttl_seconds, ttl_seconds)
        )
    
    logger.debug(f"Working memory set: {key} = {value[:50]}...")


def get_context(session_id: str, key: str) -> str | None:
    """Get a specific context value. Returns None if expired or missing."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT value FROM working_memory 
               WHERE session_id = %s AND key = %s
               AND (expires_at IS NULL OR expires_at > now())""",
            (session_id, key)
        )
        row = cur.fetchone()
    
    return row["value"] if row else None


def get_all_context(session_id: str) -> dict:
    """
    Get all active (non-expired) context for a session.
    
    Returns:
        Dict of key -> value pairs, ordered by priority (highest first)
    """
    with get_cursor() as cur:
        cur.execute(
            """SELECT key, value, priority, created_at
               FROM working_memory 
               WHERE session_id = %s
               AND (expires_at IS NULL OR expires_at > now())
               ORDER BY priority DESC, created_at DESC""",
            (session_id,)
        )
        rows = cur.fetchall()
    
    return {row["key"]: row["value"] for row in rows}


def get_context_for_prompt(session_id: str) -> str:
    """
    Build a formatted context string for injection into the LLM prompt.
    
    Returns:
        A formatted string of all active context items
    """
    context = get_all_context(session_id)
    if not context:
        return ""
    
    lines = ["## Active Context"]
    for key, value in context.items():
        lines.append(f"- **{key}**: {value}")
    
    return "\n".join(lines)


def remove_context(session_id: str, key: str):
    """Remove a specific context item."""
    with get_cursor() as cur:
        cur.execute(
            "DELETE FROM working_memory WHERE session_id = %s AND key = %s",
            (session_id, key)
        )


def clear_session(session_id: str):
    """Clear all working memory for a session."""
    with get_cursor() as cur:
        cur.execute(
            "DELETE FROM working_memory WHERE session_id = %s",
            (session_id,)
        )
    logger.debug(f"Cleared working memory for session {session_id[:8]}...")


def cleanup_expired():
    """Remove all expired working memory entries across all sessions."""
    with get_cursor() as cur:
        cur.execute(
            """DELETE FROM working_memory 
               WHERE expires_at IS NOT NULL AND expires_at <= now()"""
        )
        # Can't get rowcount from RealDictCursor easily, so just log
    logger.debug("Cleaned up expired working memory entries")


def update_context_from_message(session_id: str, role: str, content: str):
    """
    Automatically extract and update context from a message.
    This is a simple heuristic — could be enhanced with LLM extraction.
    """
    # Track message count
    count_str = get_context(session_id, "message_count")
    count = int(count_str) if count_str else 0
    set_context(session_id, "message_count", str(count + 1), priority=0.1)
    
    if role == "user":
        # Store the latest user query
        set_context(
            session_id, "last_user_query", content[:500],
            priority=0.9, ttl_seconds=7200
        )
        
        # Simple topic detection: store first few words as topic hint
        words = content.split()[:10]
        topic_hint = " ".join(words)
        set_context(
            session_id, "current_topic", topic_hint,
            priority=0.7, ttl_seconds=3600
        )
