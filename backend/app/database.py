"""
Mnemosyne — Database Layer
Manages CockroachDB connection pool and provides the schema for all memory types.
"""

import psycopg2
import psycopg2.pool
import psycopg2.extras
import logging
from contextlib import contextmanager
from app.config import settings

logger = logging.getLogger(__name__)

# Connection pool (singleton)
_pool = None


def get_pool():
    """Get or create the connection pool."""
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=settings.cockroachdb_url,
        )
        logger.info("CockroachDB connection pool initialized")
    return _pool


@contextmanager
def get_connection():
    """Get a connection from the pool. Auto-returns on exit."""
    pool = get_pool()
    conn = pool.getconn()
    conn.autocommit = True
    try:
        yield conn
    finally:
        pool.putconn(conn)


@contextmanager
def get_cursor():
    """Get a cursor with DictCursor. Auto-closes on exit."""
    with get_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield cur
        finally:
            cur.close()


@contextmanager
def transaction_cursor():
    """
    Get a cursor for an explicit transaction block.
    Commits on success, rollbacks on exception.
    """
    pool = get_pool()
    conn = pool.getconn()
    conn.autocommit = False
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    finally:
        pool.putconn(conn)


# ────────────────────────────────────────────────────────────
# Schema — all tables for the 4 memory types + consolidation
# ────────────────────────────────────────────────────────────

SCHEMA_SQL = """
-- Episodic Memory: conversation history
CREATE TABLE IF NOT EXISTS episodic_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL DEFAULT 'default',
    role TEXT NOT NULL,           -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    embedding VECTOR(1024),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    INDEX idx_episodic_session (session_id, created_at),
    INDEX idx_episodic_user (user_id, created_at)
);

-- Semantic Memory: knowledge base / RAG documents
CREATE TABLE IF NOT EXISTS semantic_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL DEFAULT 'default',
    content TEXT NOT NULL,
    source TEXT DEFAULT '',        -- where this knowledge came from
    category TEXT DEFAULT '',      -- topic/category tag
    embedding VECTOR(1024) NOT NULL,
    importance FLOAT DEFAULT 0.5,  -- 0.0–1.0 importance score
    access_count INT DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_accessed_at TIMESTAMPTZ DEFAULT now(),
    
    INDEX idx_semantic_user (user_id),
    INDEX idx_semantic_category (user_id, category)
);

-- Procedural Memory: learned patterns and preferences
CREATE TABLE IF NOT EXISTS procedural_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL DEFAULT 'default',
    pattern_type TEXT NOT NULL,    -- 'preference', 'correction', 'workflow', 'style'
    pattern TEXT NOT NULL,         -- the learned pattern/rule
    embedding VECTOR(1024),
    confidence FLOAT DEFAULT 0.5, -- 0.0–1.0 how confident we are
    times_applied INT DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_applied_at TIMESTAMPTZ DEFAULT now(),
    
    INDEX idx_procedural_user (user_id),
    INDEX idx_procedural_type (user_id, pattern_type)
);

-- Working Memory: active context for current session
CREATE TABLE IF NOT EXISTS working_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL DEFAULT 'default',
    key TEXT NOT NULL,             -- context key (e.g. 'current_topic', 'user_intent')
    value TEXT NOT NULL,
    priority FLOAT DEFAULT 0.5,   -- higher = stays longer
    ttl_seconds INT DEFAULT 3600, -- auto-expire after this
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ,
    
    UNIQUE (session_id, key),
    INDEX idx_working_session (session_id)
);

-- Memory Consolidation Log: tracks what was consolidated and when
CREATE TABLE IF NOT EXISTS consolidation_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type TEXT NOT NULL,     -- 'episodic', 'working'
    source_id UUID,
    target_type TEXT NOT NULL,     -- 'semantic', 'procedural'
    target_id UUID,
    consolidation_type TEXT NOT NULL, -- 'promote', 'merge', 'decay', 'forget'
    reason TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Vector indexes for similarity search
CREATE VECTOR INDEX IF NOT EXISTS idx_episodic_embedding ON episodic_memories (embedding) WHERE embedding IS NOT NULL;

CREATE VECTOR INDEX IF NOT EXISTS idx_semantic_embedding ON semantic_memories (embedding);

CREATE VECTOR INDEX IF NOT EXISTS idx_procedural_embedding ON procedural_memories (embedding) WHERE embedding IS NOT NULL;
"""


def initialize_schema():
    """Create all tables and indexes."""
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            # Execute each statement separately (CockroachDB doesn't support multi-statement in all cases)
            for statement in SCHEMA_SQL.split(";"):
                statement = statement.strip()
                if statement:
                    try:
                        cur.execute(statement + ";")
                    except psycopg2.errors.DuplicateObject:
                        pass  # Index already exists
                    except Exception as e:
                        logger.warning(f"Schema statement warning: {e}")
            logger.info("Database schema initialized successfully")
        finally:
            cur.close()


def drop_all_tables():
    """Drop all Mnemosyne tables (for testing only)."""
    tables = [
        "consolidation_log",
        "working_memory",
        "procedural_memories",
        "semantic_memories",
        "episodic_memories",
    ]
    with get_cursor() as cur:
        for table in tables:
            cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
    logger.info("All tables dropped")
