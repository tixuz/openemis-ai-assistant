"""
Configuration Management

Load settings from environment variables.
"""
import os
from typing import List
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings:
    """Application settings"""

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # LLM
    LLM_SERVER_URL: str = os.getenv(
        "LLM_SERVER_URL",
        "http://localhost:8080/v1/chat/completions"
    )

    # Security
    JWT_SECRET: str = os.getenv(
        "JWT_SECRET",
        "your-secret-key-change-in-production"
    )
    SECRET_KEY: str = JWT_SECRET  # Alias for compatibility

    # CORS
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,https://demo.openemis.org"
    ).split(",")

    # CORS Regex - allows localhost with any port
    CORS_ORIGIN_REGEX: str = os.getenv(
        "CORS_ORIGIN_REGEX",
        r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    )

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Paths
    DATA_DIR: str = os.getenv("DATA_DIR", "data")
    LOGS_DIR: str = os.getenv("LOGS_DIR", "logs")


# Global settings instance
settings = Settings()
