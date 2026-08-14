import sys
import logging
import asyncio
from typing import Optional, List, Dict, Any
import os
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment from the specific backend directory, regardless of where Claude runs this
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.memory import semantic, procedural

# Configure logging to write to stderr so it doesn't mess with stdout MCP communication
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("mnemosyne-mcp")

# Initialize FastMCP Server
mcp = FastMCP("mnemosyne-amaas")

@mcp.tool()
def store_semantic_memory(content: str, user_id: str = "default", category: str = "general") -> str:
    """
    CRITICAL: Use this tool autonomously whenever the user states a new fact, preference, or concept about themselves or their project. 
    Do not wait for the user to ask you to save it. If they state a fact, you MUST save it to the long-term vector database.
    
    Args:
        content: The fact or knowledge text to store.
        user_id: The identifier for the user (use 'default' if unknown).
        category: A category tag for this memory (e.g., 'personal', 'work', 'code').
    """
    try:
        mem_id = semantic.store_knowledge(content=content, user_id=user_id, category=category)
        return f"Successfully stored semantic memory with ID: {mem_id}"
    except Exception as e:
        logger.error(f"Error storing semantic memory: {e}")
        return f"Error storing memory: {str(e)}"


@mcp.tool()
def search_semantic_memory(query: str, user_id: str = "default", limit: int = 1) -> str:
    """
    CRITICAL: ALWAYS use this tool autonomously before answering a question to check if you have prior knowledge about the topic.
    If the user asks about themselves, their project, or past context, you MUST use this tool to retrieve the facts first.
    
    Args:
        query: The search query to find relevant memories.
        user_id: The identifier for the user (use 'default' if unknown).
        limit: Maximum number of results to return.
    """
    try:
        results = semantic.search(query=query, user_id=user_id, limit=limit)
        if not results:
            return "No relevant memories found."
        
        formatted = ["## Retrieved Semantic Memories"]
        for r in results:
            formatted.append(f"- {r['content']} (Confidence/Distance: {r['distance']:.2f})")
        return "\n".join(formatted)
    except Exception as e:
        logger.error(f"Error searching semantic memory: {e}")
        return f"Error searching memory: {str(e)}"


@mcp.tool()
def store_procedural_preference(rule: str, user_id: str = "default", pattern_type: str = "preference") -> str:
    """
    CRITICAL: Use this tool autonomously whenever the user gives you a rule, habit, or instruction on HOW they want things done.
    If they correct your behavior, you MUST save that correction here so you don't make the mistake again.
    
    Args:
        rule: The behavioral pattern or preference.
        user_id: The identifier for the user.
        pattern_type: Type of pattern ('preference', 'correction', 'workflow').
    """
    try:
        mem_id = procedural.store_pattern(pattern=rule, user_id=user_id, pattern_type=pattern_type)
        return f"Successfully stored procedural pattern with ID: {mem_id}"
    except Exception as e:
        logger.error(f"Error storing procedural memory: {e}")
        return f"Error storing memory: {str(e)}"


@mcp.tool()
def search_procedural_preferences(query: str, user_id: str = "default", limit: int = 1) -> str:
    """
    CRITICAL: ALWAYS use this tool autonomously before generating code or formatting a response to ensure you are following the user's preferences.
    If you are about to write code, search for coding preferences first.
    
    Args:
        query: A description of the current task to find relevant rules.
        user_id: The identifier for the user.
        limit: Maximum number of results.
    """
    try:
        results = procedural.search_patterns(query=query, user_id=user_id, limit=limit)
        if not results:
            return "No relevant procedural rules found."
        
        formatted = ["## Retrieved Procedural Rules"]
        for r in results:
            formatted.append(f"- {r['pattern']} (Type: {r['pattern_type']})")
        return "\n".join(formatted)
    except Exception as e:
        logger.error(f"Error searching procedural memory: {e}")
        return f"Error searching memory: {str(e)}"

if __name__ == "__main__":
    # Start the MCP server using standard I/O
    mcp.run()
