"""
Mnemosyne — LLM Service
Wraps Amazon Bedrock Claude for chat completions.
"""

import json
import logging
import boto3
from app.config import settings

logger = logging.getLogger(__name__)

_bedrock_client = None


def _get_client():
    """Get or create the Bedrock Runtime client."""
    global _bedrock_client
    if _bedrock_client is None:
        kwargs = {"region_name": settings.aws_region}
        if settings.aws_access_key_id:
            kwargs["aws_access_key_id"] = settings.aws_access_key_id
            kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
        _bedrock_client = boto3.client("bedrock-runtime", **kwargs)
    return _bedrock_client


def chat(
    messages: list[dict],
    system_prompt: str = "",
    max_tokens: int = 1024,
    temperature: float = 0.7,
) -> str:
    """
    Send a chat completion request to Claude via Bedrock Converse API.
    
    Args:
        messages: List of {"role": "user"|"assistant", "content": "..."}
        system_prompt: Optional system prompt
        max_tokens: Maximum response tokens
        temperature: Sampling temperature (0.0-1.0)
    
    Returns:
        The assistant's response text
    """
    client = _get_client()
    
    # Build Converse API messages
    converse_messages = []
    for msg in messages:
        converse_messages.append({
            "role": msg["role"],
            "content": [{"text": msg["content"]}],
        })
    
    kwargs = {
        "modelId": settings.bedrock_chat_model_id,
        "messages": converse_messages,
        "inferenceConfig": {
            "maxTokens": max_tokens,
            "temperature": temperature,
        },
    }
    
    if system_prompt:
        kwargs["system"] = [{"text": system_prompt}]
    
    response = client.converse(**kwargs)
    
    # Extract response text
    output = response["output"]["message"]["content"][0]["text"]
    
    # Log usage
    usage = response.get("usage", {})
    logger.debug(
        f"LLM call: {usage.get('inputTokens', '?')} in, "
        f"{usage.get('outputTokens', '?')} out"
    )
    
    return output


def chat_with_context(
    query: str,
    context_chunks: list[str],
    system_prompt: str = "",
    conversation_history: list[dict] = None,
) -> str:
    """
    RAG-style chat: inject retrieved context into the prompt, then ask Claude.
    
    Args:
        query: The user's current question
        context_chunks: Retrieved memory/document chunks for context
        system_prompt: Optional system prompt
        conversation_history: Previous messages in the conversation
    
    Returns:
        Claude's response
    """
    # Build context block
    context_text = "\n\n---\n\n".join(context_chunks) if context_chunks else "No relevant context found."
    
    augmented_query = (
        f"## Retrieved Context\n{context_text}\n\n"
        f"## User Question\n{query}"
    )
    
    messages = []
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": augmented_query})
    
    return chat(messages, system_prompt=system_prompt)
