"""
Mnemosyne — FastAPI Backend
Exposes the agent and memory engine to the frontend via REST API.
"""

import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from app.agent import MnemosyneAgent
from app.memory import working, semantic, procedural, episodic

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mnemosyne API")

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    # Next can choose a different local port when 3000 is already occupied.
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Models ---
class ChatRequest(BaseModel):
    user_id: str = "default"
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    session_id: str

class MemoryResponse(BaseModel):
    memories: List[dict]


# --- Routes ---

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "Mnemosyne"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest, background_tasks: BackgroundTasks):
    """Process a user message and return the agent's response."""
    try:
        agent = MnemosyneAgent(user_id=req.user_id, session_id=req.session_id)
        response_text = agent.chat(req.message)
        
        return ChatResponse(
            response=response_text,
            session_id=agent.session_id
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/session/consolidate")
async def consolidate_session(session_id: str, user_id: str = "default"):
    """Trigger memory consolidation for a completed session."""
    try:
        agent = MnemosyneAgent(user_id=user_id, session_id=session_id)
        results = agent.finish_session()
        return {"status": "success", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memory/working", response_model=dict)
async def get_working_memory(session_id: str):
    """Get active context for a session."""
    try:
        context = working.get_all_context(session_id)
        return {"session_id": session_id, "context": context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memory/semantic", response_model=MemoryResponse)
async def get_semantic_memory(user_id: str = "default", query: Optional[str] = None):
    """Get semantic knowledge (facts). Optionally search by query."""
    try:
        if query:
            results = semantic.search(query=query, user_id=user_id, limit=20)
        else:
            # If no query, just return recent items (we'll implement a basic fetch-all by searching for a blank space or using a direct query)
            # For simplicity in the hackathon, we'll just run a direct SQL query to get the latest
            from app.database import get_cursor
            with get_cursor() as cur:
                cur.execute(
                    "SELECT id, content, category, importance FROM semantic_memories WHERE user_id = %s ORDER BY created_at DESC LIMIT 20",
                    (user_id,)
                )
                results = [{"id": str(r["id"]), "content": r["content"], "category": r["category"], "importance": r["importance"]} for r in cur.fetchall()]
        return {"memories": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memory/procedural", response_model=MemoryResponse)
async def get_procedural_memory(user_id: str = "default"):
    """Get learned procedural rules/preferences."""
    try:
        patterns = procedural.get_all_patterns(user_id=user_id)
        return {"memories": patterns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memory/episodic", response_model=MemoryResponse)
async def get_episodic_memory(session_id: str, user_id: str = "default"):
    """Get conversation history."""
    try:
        history = episodic.get_session_history(session_id=session_id, user_id=user_id, limit=100)
        return {"memories": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
