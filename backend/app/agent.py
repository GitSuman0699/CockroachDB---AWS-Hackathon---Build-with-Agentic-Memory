"""
Mnemosyne — Agent Orchestration Loop
The core agent that retrieves context from memory, augments the prompt,
generates a response, and stores the interaction.
"""

import logging
import uuid
from typing import Dict, Any, List
from app.llm import chat_with_context
from app.memory import episodic, semantic, procedural, working, consolidation

logger = logging.getLogger(__name__)


class MnemosyneAgent:
    def __init__(self, user_id: str = "default", session_id: str = None):
        self.user_id = user_id
        self.session_id = session_id or str(uuid.uuid4())
        logger.info(f"Initialized agent for user {self.user_id}, session {self.session_id[:8]}")

    def chat(self, user_query: str) -> str:
        """
        Full agent loop: Retrieve -> Augment -> Generate -> Store
        """
        # 1. Update Working Memory
        working.update_context_from_message(self.session_id, "user", user_query)
        
        # 2. Store user message in Episodic Memory
        episodic.store_message(
            session_id=self.session_id,
            role="user",
            content=user_query,
            user_id=self.user_id
        )

        # 3. Retrieve Context (The "R" in RAG)
        context_chunks = []

        # A. Working Memory (Active Context)
        active_context = working.get_context_for_prompt(self.session_id)
        if active_context:
            context_chunks.append(active_context)

        # B. Procedural Memory (Learned Preferences)
        patterns = procedural.search_patterns(
            query=user_query, 
            user_id=self.user_id, 
            limit=3
        )
        if patterns:
            pattern_text = "## User Preferences & Patterns\n" + "\n".join(
                f"- {p['pattern']} (confidence: {p['confidence']:.2f})" 
                for p in patterns
            )
            context_chunks.append(pattern_text)

        # C. Semantic Memory (Knowledge Base)
        knowledge = semantic.search(
            query=user_query, 
            user_id=self.user_id, 
            limit=3
        )
        if knowledge:
            knowledge_text = "## Knowledge Base\n" + "\n".join(
                f"- {k['content']} (source: {k['source']})" 
                for k in knowledge
            )
            context_chunks.append(knowledge_text)

        # D. Episodic Memory (Past similar conversations, excluding current session)
        past_convos = episodic.search_similar_conversations(
            query=user_query,
            user_id=self.user_id,
            limit=2,
            session_id=self.session_id
        )
        if past_convos:
            convo_text = "## Similar Past Conversations\n" + "\n".join(
                f"- {c['role']}: {c['content']}" 
                for c in past_convos
            )
            context_chunks.append(convo_text)

        # 4. Augment & Generate (The "A" & "G" in RAG)
        # Get recent history for conversational flow
        history = episodic.get_session_history(self.session_id, limit=10, user_id=self.user_id)
        
        # Convert history format for Bedrock
        formatted_history = []
        for msg in history:
            # Skip the very last user message we just added, as it goes into the query
            if msg["id"] != history[-1]["id"]:
                formatted_history.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        system_prompt = """You are Mnemosyne, an advanced AI assistant with a sophisticated, multi-layered memory system. You remember facts about the user, their preferences, and past conversations.

RESPONSE STYLE — follow these rules strictly:
- Be warm, concise, and conversational. Write like a smart colleague, not an encyclopedia.
- Use short paragraphs (2–3 sentences max). Never write walls of text.
- Use **bold** sparingly to highlight key terms or names. Do NOT bold entire sentences.
- Use bullet points or numbered lists when listing 3+ items. Keep each bullet to one line.
- Use headers (##) only when the response has 3+ distinct sections. For short replies, skip headers entirely.
- Never use tables unless the user explicitly asks for structured data.
- Never start your response with "# Title" — just start talking naturally.
- Use code blocks (```) only for actual code. Use inline `code` for technical terms.
- Keep your tone helpful but not overly enthusiastic. No excessive emojis or exclamation marks.
- When recalling memories, weave them naturally into conversation. Say "I remember you mentioned..." not "## Knowledge Base: ...".
- If you have nothing stored about a user, say so honestly and warmly — invite them to share.

Use the provided context (active working memory, learned preferences, semantic knowledge, and past conversations) to personalize your response. If a preference or pattern is provided, adhere to it."""

        logger.info("Generating response with augmented context...")
        response = chat_with_context(
            query=user_query,
            context_chunks=context_chunks,
            system_prompt=system_prompt,
            conversation_history=formatted_history
        )

        # 5. Store assistant response
        episodic.store_message(
            session_id=self.session_id,
            role="assistant",
            content=response,
            user_id=self.user_id
        )
        
        working.update_context_from_message(self.session_id, "assistant", response)

        return response

    def finish_session(self) -> dict:
        """Run memory consolidation when a session is complete."""
        logger.info(f"Finishing session {self.session_id[:8]} and running consolidation...")
        results = consolidation.consolidate_session(self.session_id, self.user_id)
        return results
