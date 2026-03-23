"""
Arquivo de configuração centralizado para Vexus CRM
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # Aplicação
    APP_NAME: str = "Vexus CRM Agêntico"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"
    
    # Banco de dados
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://vexus:password@localhost/vexus_crm"
    )
    DATABASE_ECHO: bool = DEBUG
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4-turbo"
    OPENAI_TEMPERATURE: float = 0.3
    OPENAI_MAX_TOKENS: int = 1000
    
    # WhatsApp
    WHATSAPP_BUSINESS_API_KEY: str = os.getenv("WHATSAPP_BUSINESS_API_KEY", "")
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_API_VERSION: str = "v17.0"
    
    # Twilio (SMS)
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    
    # SendGrid (Email)
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    SENDGRID_FROM_EMAIL: str = os.getenv("SENDGRID_FROM_EMAIL", "noreply@vexus.com.br")
    
    # Meta (Instagram/Facebook)
    META_ACCESS_TOKEN: str = os.getenv("META_ACCESS_TOKEN", "")
    META_BUSINESS_ACCOUNT_ID: str = os.getenv("META_BUSINESS_ACCOUNT_ID", "")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # Security - Enhanced
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

    # File Upload Security
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", str(10 * 1024 * 1024)))  # 10MB
    ALLOWED_EXTENSIONS: list = [".pdf", ".doc", ".docx", ".txt", ".png", ".jpg", ".jpeg", ".gif"]

    # CORS - Production Ready
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    CORS_ALLOW_HEADERS: list = ["*"]
    CORS_MAX_AGE: int = 86400  # 24 hours

    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "1"))
    RELOAD: bool = ENVIRONMENT == "development"

    # Database - Production Settings
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    DATABASE_POOL_RECYCLE: int = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))  # 1 hour

    # Cache Settings
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes

    # Monitoring & Metrics
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    METRICS_PORT: int = int(os.getenv("METRICS_PORT", "9090"))
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")

    # Backup Settings
    BACKUP_ENABLED: bool = os.getenv("BACKUP_ENABLED", "false").lower() == "true"
    BACKUP_INTERVAL_HOURS: int = int(os.getenv("BACKUP_INTERVAL_HOURS", "24"))
    BACKUP_RETENTION_DAYS: int = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))

    # Feature Flags
    ENABLE_WHATSAPP: bool = os.getenv("ENABLE_WHATSAPP", "true").lower() == "true"
    ENABLE_EMAIL: bool = os.getenv("ENABLE_EMAIL", "true").lower() == "true"
    ENABLE_ANALYTICS: bool = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
    ENABLE_AI_AGENTS: bool = os.getenv("ENABLE_AI_AGENTS", "true").lower() == "true"

    class Config:
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cache de configurações"""
    return Settings()
