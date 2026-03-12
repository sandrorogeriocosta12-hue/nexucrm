"""
Security configuration settings
"""

import os
from typing import Optional


class SecurityConfig:
    """Security configuration class"""

    # Basic security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default-secret-key-change-in-production")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Rate limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = int(
        os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60")
    )
    RATE_LIMIT_REQUESTS_PER_HOUR: int = int(
        os.getenv("RATE_LIMIT_REQUESTS_PER_HOUR", "1000")
    )
    RATE_LIMIT_REQUESTS_PER_DAY: int = int(
        os.getenv("RATE_LIMIT_REQUESTS_PER_DAY", "10000")
    )

    # Secrets management
    SECRETS_MANAGER_TYPE: str = os.getenv("SECRETS_MANAGER_TYPE", "local")
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    LOG_RETENTION_DAYS: int = int(os.getenv("LOG_RETENTION_DAYS", "30"))

    # Security headers
    CSP_POLICY: str = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    HSTS_MAX_AGE: int = 31536000  # 1 year
    X_FRAME_OPTIONS: str = "DENY"

    # Validation settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: list = [".jpg", ".png", ".pdf", ".txt"]


# Global config instance
security_config = SecurityConfig()
