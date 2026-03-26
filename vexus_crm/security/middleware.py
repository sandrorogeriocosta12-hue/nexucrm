"""
🔒 MIDDLEWARE DE SEGURANÇA AVANÇADA
Headers de proteção, rate limiting, CORS seguro
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
from typing import Optional
from vexus_crm.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SecurityHeaders:
    """Middleware para headers de segurança"""
    
    @staticmethod
    async def add_security_headers(request: Request, call_next):
        """Adiciona headers de segurança à resposta"""
        response = await call_next(request)
        
        # HSTS (HTTP Strict Transport Security)
        if settings.SECURE_HSTS_SECONDS > 0:
            hsts_value = f"max-age={settings.SECURE_HSTS_SECONDS}"
            if settings.SECURE_HSTS_INCLUDE_SUBDOMAINS:
                hsts_value += "; includeSubDomains"
            if settings.SECURE_HSTS_PRELOAD:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value
        
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-XSS-Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content-Security-Policy
        if settings.ENVIRONMENT == "production":
            csp = (
                f"default-src {settings.CSP_DEFAULT_SRC}; "
                f"script-src {settings.CSP_SCRIPT_SRC}; "
                f"style-src {settings.CSP_STYLE_SRC}; "
                f"img-src {settings.CSP_IMG_SRC}; "
                "form-action 'self'; "
                "frame-ancestors 'none';"
            )
            response.headers["Content-Security-Policy"] = csp
        
        # Permissions-Policy (Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )
        
        return response


class RateLimitConfig:
    """Configuração de rate limiting"""
    
    @staticmethod
    def setup_limiter() -> Limiter:
        """Configura limiter com Redis"""
        try:
            limiter = Limiter(
                key_func=get_remote_address,
                storage_uri=settings.REDIS_URL if settings.RATE_LIMIT_ENABLED else None,
                default_limits=[f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_PERIOD}s"]
            )
            logger.info("✅ Rate Limiter configurado com Redis")
            return limiter
        except Exception as e:
            logger.warning(f"⚠️ Erro ao configurar rate limiter: {e}")
            # Fallback para in-memory
            limiter = Limiter(
                key_func=get_remote_address,
                default_limits=[f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_PERIOD}s"]
            )
            return limiter


class CORSConfig:
    """Configuração de CORS segura"""
    
    @staticmethod
    def setup_cors(app: FastAPI):
        """Configura CORS com comportamiento seguro"""
        
        # Em produção, usar apenas domínios específicos
        if settings.ENVIRONMENT == "production":
            allowed_origins = [
                "https://nexuscrm.tech",
                "https://www.nexuscrm.tech",
                "https://app.nexuscrm.tech",
            ]
        else:
            allowed_origins = settings.CORS_ORIGINS
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
            allow_methods=settings.CORS_ALLOW_METHODS,
            allow_headers=settings.CORS_ALLOW_HEADERS,
            max_age=86400,  # 24 horas
        )
        
        logger.info(f"✅ CORS configurado para: {allowed_origins}")


class TrustedHostsConfig:
    """Configuração de hosts confiáveis"""
    
    @staticmethod
    def setup_trusted_hosts(app: FastAPI):
        """Adiciona middleware de hosts confiáveis"""
        
        allowed_hosts = [
            "localhost",
            "127.0.0.1",
            "nexuscrm.tech",
            "www.nexuscrm.tech",
            "api.nexuscrm.tech",
            "app.nexuscrm.tech",
        ]
        
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=allowed_hosts
        )
        
        logger.info(f"✅ Trusted hosts configurado: {allowed_hosts}")


def setup_security_middleware(app: FastAPI):
    """Configura todos os middlewares de segurança"""
    
    # 1. Hosts confiáveis (primeiro)
    TrustedHostsConfig.setup_trusted_hosts(app)
    
    # 2. CORS
    CORSConfig.setup_cors(app)
    
    # 3. Headers de segurança
    app.add_middleware(SecurityHeaders.__class__)
    
    logger.info("✅ Todos os middlewares de segurança configurados")


# Limiter global
limiter = RateLimitConfig.setup_limiter()


__all__ = [
    "SecurityHeaders",
    "RateLimitConfig", 
    "CORSConfig",
    "TrustedHostsConfig",
    "setup_security_middleware",
    "limiter"
]
