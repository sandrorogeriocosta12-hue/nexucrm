"""
Configuração centralizada para múltiplos ambientes
Desenvolvimento, Staging e Produção
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuração da aplicação"""
    
    # ========================================================================
    # 🌍 AMBIENTE
    # ========================================================================
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"
    
    # ========================================================================
    # 🚀 SERVIDOR
    # ========================================================================
    APP_NAME: str = "Nexus CRM"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # ========================================================================
    # 🔐 SEGURANÇA
    # ========================================================================
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "jwt-secret-key-change")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # ========================================================================
    # 💾 BANCO DE DADOS
    # ========================================================================
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/nexuscrm"
    )
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "20"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
    DATABASE_POOL_RECYCLE: int = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))
    SQLALCHEMY_ECHO: bool = DEBUG
    
    # ========================================================================
    # 🔄 REDIS (Cache e Sessions)
    # ========================================================================
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))
    
    # ========================================================================
    # 📧 EMAIL
    # ========================================================================
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@nexuscrm.tech")
    FROM_NAME: str = os.getenv("FROM_NAME", "Nexus CRM")
    
    # ========================================================================
    # 🔒 CORS
    # ========================================================================
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://nexuscrm.tech",
        "https://www.nexuscrm.tech",
        "https://app.nexuscrm.tech",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # ========================================================================
    # 📊 MONITORAMENTO
    # ========================================================================
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", None)
    SENTRY_ENVIRONMENT: str = ENVIRONMENT
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1 if ENVIRONMENT == "production" else 1.0
    
    # ========================================================================
    # ⏱️ RATE LIMITING
    # ========================================================================
    RATE_LIMIT_ENABLED: bool = ENVIRONMENT == "production"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "1000"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "3600"))
    
    # ========================================================================
    # 🔐 SEGURANÇA AVANÇADA
    # ========================================================================
    # Headers de segurança
    SECURE_HSTS_SECONDS: int = 31536000 if ENVIRONMENT == "production" else 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS: bool = True
    SECURE_HSTS_PRELOAD: bool = False
    SECURE_SSL_REDIRECT: bool = ENVIRONMENT == "production"
    
    # Content Security Policy
    CSP_DEFAULT_SRC: str = "'self'"
    CSP_SCRIPT_SRC: str = "'self' 'unsafe-inline' 'unsafe-eval'"
    CSP_STYLE_SRC: str = "'self' 'unsafe-inline'"
    CSP_IMG_SRC: str = "'self' data: https:"
    
    # ========================================================================
    # 📁 UPLOAD
    # ========================================================================
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB
    UPLOAD_DIR: str = "uploads"
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "doc", "docx", "xls", "xlsx", "png", "jpg", "jpeg"]
    
    # ========================================================================
    # 🎯 FEATURE FLAGS
    # ========================================================================
    ENABLE_2FA: bool = os.getenv("ENABLE_2FA", "true").lower() == "true"
    ENABLE_EMAIL_VERIFICATION: bool = os.getenv("ENABLE_EMAIL_VERIFICATION", "true").lower() == "true"
    ENABLE_API_DOCS: bool = ENVIRONMENT != "production"
    ENABLE_ANALYTICS: bool = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
    
    # ========================================================================
    # 🔗 URLs EXTERNAS
    # ========================================================================
    APP_URL: str = os.getenv("APP_URL", "http://localhost:3000")
    API_URL: str = os.getenv("API_URL", "http://localhost:8000")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # ========================================================================
    # 📝 LOGGING
    # ========================================================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO" if ENVIRONMENT == "production" else "DEBUG")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE", None)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Retorna instância singleton de configurações"""
    return Settings()


# Funções auxiliares para configuração por ambiente
def is_development() -> bool:
    """Verifica se está em desenvolvimento"""
    return get_settings().ENVIRONMENT == "development"


def is_staging() -> bool:
    """Verifica se está em staging"""
    return get_settings().ENVIRONMENT == "staging"


def is_production() -> bool:
    """Verifica se está em produção"""
    return get_settings().ENVIRONMENT == "production"
