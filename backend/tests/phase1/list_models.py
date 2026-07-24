"""Quick script to list available Claude models in your Bedrock region."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import boto3
from app.config import settings

client = boto3.client(
    "bedrock",
    region_name=settings.aws_region,
    aws_access_key_id=settings.aws_access_key_id or None,
    aws_secret_access_key=settings.aws_secret_access_key or None,
)

print(f"Region: {settings.aws_region}")
print(f"Listing Claude models...\n")

response = client.list_foundation_models(byProvider="Anthropic")
for m in response["modelSummaries"]:
    mid = m["modelId"]
    if "claude" in mid.lower():
        print(f"  {mid}")

print(f"\nListing Titan Embedding models...\n")
response2 = client.list_foundation_models(byProvider="Amazon")
for m in response2["modelSummaries"]:
    mid = m["modelId"]
    if "embed" in mid.lower():
        print(f"  {mid}")
