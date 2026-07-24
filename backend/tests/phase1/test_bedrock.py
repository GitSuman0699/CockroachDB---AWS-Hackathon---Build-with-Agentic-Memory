"""
Phase 1 — Step 3: Amazon Bedrock Test
Confirms both embedding generation (Titan) and chat completion (Claude) work.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import boto3
from botocore.exceptions import ClientError
from app.config import settings


def test_bedrock_embedding():
    """Generate an embedding using Amazon Titan Embeddings V2."""
    print("\n📐 Testing Titan Embeddings V2...")

    client = boto3.client(
        "bedrock-runtime",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
    )

    payload = {
        "inputText": "CockroachDB is a distributed SQL database.",
        "dimensions": 1024,
        "normalize": True,
    }

    try:
        response = client.invoke_model(
            body=json.dumps(payload),
            modelId=settings.bedrock_embedding_model_id,
            accept="application/json",
            contentType="application/json",
        )

        response_body = json.loads(response["body"].read())
        embedding = response_body["embedding"]

        print(f"   ✅ Embedding generated successfully!")
        print(f"   Dimensions: {len(embedding)}")
        print(f"   First 5 values: {embedding[:5]}")
        print(f"   Model: {settings.bedrock_embedding_model_id}")

        return embedding

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_msg = e.response["Error"]["Message"]
        print(f"   ❌ Bedrock embedding failed: [{error_code}] {error_msg}")
        if error_code == "AccessDeniedException":
            print("   → You need to request model access in the Bedrock console")
            print(f"   → Region: {settings.aws_region}")
        return None


def test_bedrock_chat():
    """Run a chat completion using Claude via the Converse API."""
    print("\n💬 Testing Claude via Converse API...")

    client = boto3.client(
        "bedrock-runtime",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
    )

    messages = [
        {
            "role": "user",
            "content": [{"text": "In exactly one sentence, explain what CockroachDB is."}],
        }
    ]

    try:
        response = client.converse(
            modelId=settings.bedrock_chat_model_id,
            messages=messages,
            inferenceConfig={"maxTokens": 200, "temperature": 0.3},
        )

        response_text = response["output"]["message"]["content"][0]["text"]
        usage = response.get("usage", {})

        print(f"   ✅ Chat completion successful!")
        print(f"   Response: {response_text}")
        print(f"   Input tokens: {usage.get('inputTokens', 'N/A')}")
        print(f"   Output tokens: {usage.get('outputTokens', 'N/A')}")
        print(f"   Model: {settings.bedrock_chat_model_id}")

        return response_text

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_msg = e.response["Error"]["Message"]
        print(f"   ❌ Bedrock chat failed: [{error_code}] {error_msg}")
        if error_code == "AccessDeniedException":
            print("   → You need to request model access in the Bedrock console")
            print(f"   → Region: {settings.aws_region}")
        return None


def test_bedrock():
    """Run both Bedrock tests."""
    print("=" * 60)
    print("P1.3 — Amazon Bedrock Test (Embeddings + Chat)")
    print("=" * 60)

    embedding = test_bedrock_embedding()
    chat_response = test_bedrock_chat()

    print(f"\n{'=' * 60}")
    if embedding and chat_response:
        print("✅ P1.3 PASSED — Both Bedrock calls work")
    else:
        if not embedding:
            print("❌ Embedding test failed")
        if not chat_response:
            print("❌ Chat completion test failed")
        print("❌ P1.3 FAILED")
    print(f"{'=' * 60}")

    return bool(embedding and chat_response)


if __name__ == "__main__":
    success = test_bedrock()
    sys.exit(0 if success else 1)
