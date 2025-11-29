import os

"""
Configuration for AstraFlow - Environment Variables Based Configuration
"""

# DashVector Configuration
DASHVECTOR_API_KEY = os.getenv("DASHVECTOR_API_KEY", "")
DASHVECTOR_ENDPOINT = os.getenv("DASHVECTOR_ENDPOINT", "")

# DashScope Configuration
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

# OpenRouter API Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# Default model
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "anthropic/claude-sonnet-4.5")

# PostgreSQL Configuration
POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", ""),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "database": os.getenv("POSTGRES_DATABASE", ""),
    "user": os.getenv("POSTGRES_USER", ""),
    "password": os.getenv("POSTGRES_PASSWORD", "")
}

# OSS Configuration
OSS_CONFIG = {
    "access_key_id": os.getenv("OSS_ACCESS_KEY_ID", ""),
    "access_key_secret": os.getenv("OSS_ACCESS_KEY_SECRET", ""),
    "endpoint": os.getenv("OSS_ENDPOINT", ""),
    "region": os.getenv("OSS_REGION", ""),
    "bucket_name": os.getenv("OSS_BUCKET_NAME", "")
}


