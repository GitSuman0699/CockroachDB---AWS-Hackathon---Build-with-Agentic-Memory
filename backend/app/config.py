"""
Mnemosyne — Configuration
Loads environment variables and provides typed settings.
"""

import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # CockroachDB
    cockroachdb_url: str = ""

    # AWS
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # Bedrock Models
    bedrock_chat_model_id: str = "us.anthropic.claude-sonnet-4-20250514"
    bedrock_embedding_model_id: str = "amazon.titan-embed-text-v2:0"

    # S3
    s3_bucket_name: str = "mnemosyne-documents"

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
