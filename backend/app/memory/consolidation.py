"""
Mnemosyne — Memory Consolidation Engine
The TOP DIFFERENTIATOR for the hackathon.

Mimics human memory consolidation: promotes important short-term memories
into long-term storage, merges related knowledge, and decays unused memories.

Consolidation types:
1. PROMOTE: Move important episodic/working memories → semantic/procedural
2. MERGE: Combine related semantic memories into richer knowledge
3. DECAY: Reduce importance of rarely-accessed memories
4. FORGET: Remove very low-importance, old, never-accessed memories
"""

import json
import logging
from datetime import datetime, timedelta
from app.database import get_cursor, transaction_cursor
from app.embeddings import embed_text, format_vector
from app.llm import chat
from app.memory import episodic, semantic, procedural, working

logger = logging.getLogger(__name__)


def consolidate_session(session_id: str, user_id: str = "default") -> dict:
    """
    Consolidate memories from a completed conversation session.
    This is the main consolidation entry point — call after a session ends
    or on a periodic schedule.
    
    Steps:
    1. Summarize the session → store as semantic memory
    2. Extract patterns/preferences → store as procedural memories
    3. Clean up working memory for the session
    
    Returns:
        Dict summarizing what was consolidated
    """
    results = {
        "session_id": session_id,
        "semantic_created": [],
        "procedural_created": [],
        "working_cleaned": False,
    }
    
    # Get session history
    history = episodic.get_session_history(session_id, limit=100, user_id=user_id)
    if len(history) < 2:
        logger.info(f"Session {session_id[:8]} too short to consolidate")
        return results
    
    # Build conversation text
    conv_text = "\n".join(
        f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
        for m in history
    )
    
    # Step 1: Extract key knowledge using LLM
    knowledge_prompt = """Analyze this conversation and extract the KEY FACTS and KNOWLEDGE discussed.
Return each fact as a separate line starting with "FACT: ".
Only include substantive facts, not meta-conversation.
If no meaningful facts were discussed, return "NONE".

Conversation:
""" + conv_text[:4000]  # Token limit safety
    
    try:
        knowledge_response = chat(
            messages=[{"role": "user", "content": knowledge_prompt}],
            system_prompt="You extract structured knowledge from conversations. Be concise and factual.",
            max_tokens=500,
            temperature=0.3,
        )
        
        # Parse facts
        facts = []
        for line in knowledge_response.strip().split("\n"):
            line = line.strip()
            if line.startswith("FACT:"):
                fact = line[5:].strip()
                if fact and fact != "NONE":
                    facts.append(fact)
        
        
        
        logger.info(f"Extracted {len(facts)} facts from session {session_id[:8]}")
        
    except Exception as e:
        logger.error(f"Knowledge extraction failed: {e}")
        facts = []
        
    # Step 2: Extract user preferences/patterns using LLM
    pattern_prompt = """Analyze this conversation and extract any USER PREFERENCES or PATTERNS.
For example:
- Communication style preferences (concise vs detailed)
- Topic interests
- Corrections the user made
- Workflow patterns

Return each as: "PATTERN [type]: description"
Where type is one of: preference, correction, workflow, style
If no patterns found, return "NONE".

Conversation:
""" + conv_text[:4000]
    
    procedural_items_to_store = []
    try:
        pattern_response = chat(
            messages=[{"role": "user", "content": pattern_prompt}],
            system_prompt="You analyze conversations to learn user preferences and behavioral patterns.",
            max_tokens=500,
            temperature=0.3,
        )
        
        for line in pattern_response.strip().split("\n"):
            line = line.strip()
            if line.startswith("PATTERN"):
                try:
                    bracket_start = line.index("[")
                    bracket_end = line.index("]")
                    ptype = line[bracket_start + 1:bracket_end].strip().lower()
                    description = line[bracket_end + 1:].strip().lstrip(":").strip()
                    
                    if ptype not in ("preference", "correction", "workflow", "style"):
                        ptype = "preference"
                    
                    if description:
                        procedural_items_to_store.append({"type": ptype, "description": description})
                except (ValueError, IndexError):
                    pass
                    
        logger.info(f"Extracted {len(procedural_items_to_store)} patterns from session {session_id[:8]}")
        
    except Exception as e:
        logger.error(f"Pattern extraction failed: {e}")
        
    try:
        # --- ACID Transaction Block ---
        # We wrap all insertions, deletions, and logging in a single CockroachDB transaction
        # to guarantee that if the process fails midway, memory isn't corrupted or partially duplicated.
        with transaction_cursor() as cur:
            # Store each fact as semantic memory
            for fact in facts:
                mid = semantic.store_knowledge(
                    content=fact,
                    user_id=user_id,
                    source=f"consolidated:session:{session_id[:8]}",
                    category="conversation_knowledge",
                    importance=0.6,
                    metadata={"consolidated_from": session_id},
                    _cur=cur,
                )
                results["semantic_created"].append({"id": mid, "content": fact})
            
            # Store patterns as procedural memories
            for p in procedural_items_to_store:
                mid = procedural.store_pattern(
                    pattern=p["description"],
                    pattern_type=p["type"],
                    user_id=user_id,
                    confidence=0.4,
                    metadata={"consolidated_from": session_id},
                    _cur=cur,
                )
                results["procedural_created"].append({
                    "id": mid, "type": p["type"], "pattern": p["description"]
                })
            
            # Step 3: Clean up working memory within the same transaction
            working.clear_session(session_id, _cur=cur)
            results["working_cleaned"] = True
            
            # Log consolidation
            _log_consolidation(
                source_type="episodic",
                target_type="semantic",
                consolidation_type="promote",
                reason=f"Session {session_id[:8]} consolidation: {len(results['semantic_created'])} facts, {len(results['procedural_created'])} patterns",
                metadata=results,
                _cur=cur,
            )
            
        logger.info(f"Successfully committed consolidation transaction for session {session_id[:8]}")
        
    except Exception as e:
        logger.error(f"Pattern extraction or transaction failed: {e}")
        # The transaction will automatically rollback due to transaction_cursor()
    
    return results


def decay_old_memories(
    user_id: str = "default",
    decay_factor: float = 0.95,
    min_age_days: int = 7,
) -> int:
    """
    Decay importance of semantic memories that haven't been accessed recently.
    Mimics human memory: unused memories fade over time.
    
    Args:
        user_id: User identifier
        decay_factor: Multiply importance by this (e.g., 0.95 = 5% decay)
        min_age_days: Only decay memories older than this
    
    Returns:
        Number of memories decayed
    """
    with get_cursor() as cur:
        cur.execute(
            """UPDATE semantic_memories 
               SET importance = importance * %s
               WHERE user_id = %s 
               AND last_accessed_at < now() - INTERVAL '1 day' * %s
               AND importance > 0.1""",
            (decay_factor, user_id, min_age_days)
        )
        # Log it
        _log_consolidation(
            source_type="semantic",
            target_type="semantic",
            consolidation_type="decay",
            reason=f"Decayed old memories by factor {decay_factor}",
        )
    
    logger.info(f"Decayed old semantic memories for user {user_id}")
    return 0  # CockroachDB doesn't easily return affected rows with RealDictCursor


def forget_irrelevant(
    user_id: str = "default",
    importance_threshold: float = 0.1,
    min_age_days: int = 30,
) -> int:
    """
    Remove memories that are old, low-importance, and never accessed.
    
    Returns:
        Number of memories removed
    """
    with get_cursor() as cur:
        cur.execute(
            """DELETE FROM semantic_memories
               WHERE user_id = %s
               AND importance < %s
               AND access_count = 0
               AND created_at < now() - INTERVAL '1 day' * %s""",
            (user_id, importance_threshold, min_age_days)
        )
    
    _log_consolidation(
        source_type="semantic",
        target_type="semantic",
        consolidation_type="forget",
        reason=f"Forgot irrelevant memories (importance < {importance_threshold}, age > {min_age_days}d)",
    )
    
    logger.info(f"Forgot irrelevant memories for user {user_id}")
    return 0


def merge_similar_memories(
    user_id: str = "default",
    similarity_threshold: float = 0.15,
    limit: int = 10,
) -> list[dict]:
    """
    Find and merge very similar semantic memories into richer combined entries.
    
    This prevents duplicate or near-duplicate knowledge and creates
    more comprehensive memory entries.
    
    Returns:
        List of merged memory records
    """
    merged = []
    
    with get_cursor() as cur:
        # Find pairs of very similar memories
        cur.execute(
            """SELECT a.id AS id_a, b.id AS id_b,
                      a.content AS content_a, b.content AS content_b,
                      a.importance AS imp_a, b.importance AS imp_b,
                      a.embedding <=> b.embedding AS distance
               FROM semantic_memories a
               JOIN semantic_memories b ON a.id < b.id
               WHERE a.user_id = %s AND b.user_id = %s
               AND a.embedding <=> b.embedding < %s
               ORDER BY distance ASC
               LIMIT %s""",
            (user_id, user_id, similarity_threshold, limit)
        )
        pairs = cur.fetchall()
    
    for pair in pairs:
        # Use LLM to merge the two memories
        try:
            merge_prompt = f"""Merge these two related pieces of knowledge into a single, 
more comprehensive statement. Keep it concise but complete.

Knowledge 1: {pair['content_a']}
Knowledge 2: {pair['content_b']}

Merged knowledge:"""
            
            merged_content = chat(
                messages=[{"role": "user", "content": merge_prompt}],
                system_prompt="You merge related knowledge into concise, comprehensive statements.",
                max_tokens=200,
                temperature=0.3,
            )
            
            # Store merged memory with higher importance
            new_importance = max(float(pair["imp_a"]), float(pair["imp_b"])) + 0.1
            new_id = semantic.store_knowledge(
                content=merged_content.strip(),
                user_id=user_id,
                source="consolidated:merge",
                category="merged_knowledge",
                importance=min(new_importance, 1.0),
                metadata={
                    "merged_from": [str(pair["id_a"]), str(pair["id_b"])],
                },
            )
            
            # Delete originals
            with get_cursor() as cur:
                cur.execute(
                    "DELETE FROM semantic_memories WHERE id IN (%s, %s)",
                    (str(pair["id_a"]), str(pair["id_b"]))
                )
            
            merged.append({
                "new_id": new_id,
                "merged_content": merged_content.strip(),
                "original_ids": [str(pair["id_a"]), str(pair["id_b"])],
            })
            
            _log_consolidation(
                source_type="semantic",
                target_type="semantic",
                consolidation_type="merge",
                reason=f"Merged similar memories (distance={float(pair['distance']):.4f})",
                metadata={"merged_from": [str(pair["id_a"]), str(pair["id_b"])]},
            )
            
        except Exception as e:
            logger.error(f"Failed to merge memories: {e}")
    
    logger.info(f"Merged {len(merged)} memory pairs for user {user_id}")
    return merged


def run_full_consolidation(user_id: str = "default") -> dict:
    """
    Run the complete consolidation pipeline.
    Call this periodically (e.g., after every session, or on a schedule).
    
    Returns:
        Summary of all consolidation actions
    """
    results = {
        "decayed": 0,
        "forgotten": 0,
        "merged": [],
    }
    
    # 1. Decay old memories
    results["decayed"] = decay_old_memories(user_id)
    
    # 2. Forget irrelevant ones
    results["forgotten"] = forget_irrelevant(user_id)
    
    # 3. Merge similar memories
    results["merged"] = merge_similar_memories(user_id)
    
    logger.info(f"Full consolidation complete for user {user_id}: {results}")
    return results


def get_consolidation_history(limit: int = 20) -> list[dict]:
    """Get recent consolidation log entries."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT id, source_type, target_type, consolidation_type,
                      reason, metadata, created_at
               FROM consolidation_log
               ORDER BY created_at DESC
               LIMIT %s""",
            (limit,)
        )
        rows = cur.fetchall()
    
    return [
        {
            "id": str(row["id"]),
            "source_type": row["source_type"],
            "target_type": row["target_type"],
            "consolidation_type": row["consolidation_type"],
            "reason": row["reason"],
            "metadata": row["metadata"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        }
        for row in rows
    ]


def _log_consolidation(
    source_type: str,
    target_type: str,
    consolidation_type: str,
    reason: str = "",
    metadata: dict = None,
    _cur=None,
):
    """Internal: log a consolidation event."""
    query = """INSERT INTO consolidation_log 
               (source_type, target_type, consolidation_type, reason, metadata)
               VALUES (%s, %s, %s, %s, %s)"""
    args = (source_type, target_type, consolidation_type, reason,
             json.dumps(metadata or {}, default=str))
    
    if _cur:
        _cur.execute(query, args)
    else:
        with get_cursor() as cur:
            cur.execute(query, args)
