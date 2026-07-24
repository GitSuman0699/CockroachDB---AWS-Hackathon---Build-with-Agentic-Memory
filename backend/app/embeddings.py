"""
Mnemosyne — Embedding Service
Wraps Amazon Bedrock Titan Embeddings V2 for vector generation.
"""

import json
import logging
import boto3
from app.config import settings

logger = logging.getLogger(__name__)

# Singleton client
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
        logger.info(f"Bedrock client initialized (region: {settings.aws_region})")
    return _bedrock_client


def embed_text(text: str, dimensions: int = 1024) -> list[float]:
    """
    Generate an embedding vector for the given text using Titan Embeddings V2.
    
    Args:
        text: The text to embed (max ~8k tokens)
        dimensions: Vector dimensions (default 1024)
    
    Returns:
        List of floats representing the embedding vector
    """
    client = _get_client()
    
    body = json.dumps({
        "inputText": text[:8000],  # Titan V2 max input
        "dimensions": dimensions,
    })
    
    response = client.invoke_model(
        modelId=settings.bedrock_embedding_model_id,
        body=body,
        contentType="application/json",
        accept="application/json",
    )
    
    result = json.loads(response["body"].read())
    return result["embedding"]


def embed_batch(texts: list[str], dimensions: int = 1024) -> list[list[float]]:
    """
    Generate embeddings for a batch of texts.
    Note: Titan V2 doesn't support native batching, so we call sequentially.
    
    Args:
        texts: List of texts to embed
        dimensions: Vector dimensions
    
    Returns:
        List of embedding vectors
    """
    return [embed_text(text, dimensions) for text in texts]


def format_vector(embedding: list[float]) -> str:
    """Format an embedding as a CockroachDB VECTOR literal string."""
    return "[" + ",".join(str(x) for x in embedding) + "]"
