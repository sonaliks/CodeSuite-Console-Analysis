"""Configuration for the CodeSuite Diagnostics Demo backend."""

import os

# Bedrock configuration
BEDROCK_MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0"
)
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")

# Server configuration
API_HOST = os.environ.get("API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("API_PORT", "8000"))
