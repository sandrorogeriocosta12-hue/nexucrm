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
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    class Config:
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cache de configurações"""
    return Settings()
