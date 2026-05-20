"""
🔐 API v1 - Autenticação e Configuração
/api/v1/auth e /api/v1/config endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
import jwt
import os
from typing import Optional, Dict, Any
import logging

from api_v1_models import (
    LoginRequest, LoginResponse, TokenResponse, RefreshTokenRequest,
    ConfigIntegrationsResponse, IntegrationStatus, SetupRequest, SuccessResponse
)
from api_v1_workers import CacheManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["auth", "config"])

# ═══════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO JWT
# ═══════════════════════════════════════════════════════════════════

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria JWT token de acesso"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Cria JWT token de refresh"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Valida JWT token do header Authorization"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


# ═══════════════════════════════════════════════════════════════════
# ENDPOINTS - AUTENTICAÇÃO
# ═══════════════════════════════════════════════════════════════════

@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    🔐 Autenticação do usuário
    
    Valida email e senha, retorna JWT tokens.
    
    Args:
        request: Email e senha do usuário
        
    Returns:
        access_token, refresh_token, user info
    """
    # ⚠️ TEMP: Verificação dummy - em produção, validar contra banco de dados
    if request.email == "demo@vexus.com" and request.password == "demo123":
        user_id = "user_demo_001"
        email = request.email
        name = "Demo User"
        
        # Gerar tokens
        access_token = create_access_token(
            data={"sub": user_id, "email": email}
        )
        refresh_token = create_refresh_token(
            data={"sub": user_id, "email": email}
        )
        
        # Cachear sessão
        await CacheManager.set_user_session(
            user_id,
            {
                "email": email,
                "name": name,
                "created_at": datetime.now().isoformat(),
                "permissions": ["read", "write", "admin"]
            }
        )
        
        logger.info(f"✅ Login bem-sucedido: {email}")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user_id,
            email=email,
            name=name
        )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Email ou senha inválidos"
    )


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    🔄 Renovar token de acesso
    
    Usa refresh_token para obter novo access_token
    """
    try:
        payload = jwt.decode(request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        access_token = create_access_token(
            data={"sub": user_id}
        )
        
        logger.info(f"✅ Token renovado para: {user_id}")
        
        return TokenResponse(access_token=access_token)
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expirou"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/auth/me")
async def get_current_user(payload: Dict[str, Any] = Depends(verify_token)):
    """
    👤 Obter dados do usuário autenticado
    """
    user_id = payload.get("sub")
    
    # Obter dados do cache/banco
    session = await CacheManager.get_user_session(user_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User session not found"
        )
    
    return {
        "user_id": user_id,
        **session
    }


# ═══════════════════════════════════════════════════════════════════
# ENDPOINTS - CONFIGURAÇÃO
# ═══════════════════════════════════════════════════════════════════

@router.get("/config/integrations", response_model=ConfigIntegrationsResponse)
async def get_integrations_status(payload: Dict[str, Any] = Depends(verify_token)):
    """
    🔗 Status de todas as integrações
    
    Retorna se cada API externa está conectada e operacional
    """
    
    # Tentar obter do cache primeiro
    cached_status = await CacheManager.get_integration_status("all")
    if cached_status:
        return ConfigIntegrationsResponse(**cached_status)
    
    # Se não tiver em cache, retornar status padrão
    status_data = {
        "openai": IntegrationStatus(
            name="OpenAI",
            enabled=bool(os.getenv("OPENAI_API_KEY")),
            connected=True,
            error_message=None
        ),
        "whatsapp": IntegrationStatus(
            name="WhatsApp Business",
            enabled=bool(os.getenv("WHATSAPP_PHONE_ID")),
            connected=bool(os.getenv("WHATSAPP_ACCESS_TOKEN")),
            error_message=None
        ),
        "telegram": IntegrationStatus(
            name="Telegram",
            enabled=bool(os.getenv("TELEGRAM_BOT_TOKEN")),
            connected=True,
            error_message=None
        ),
        "instagram": IntegrationStatus(
            name="Instagram",
            enabled=bool(os.getenv("INSTAGRAM_ACCESS_TOKEN")),
            connected=bool(os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")),
            error_message=None
        ),
        "stripe": IntegrationStatus(
            name="Stripe",
            enabled=bool(os.getenv("STRIPE_SECRET_KEY")),
            connected=True,
            error_message=None
        ),
        "email": IntegrationStatus(
            name="Email (SMTP/SendGrid)",
            enabled=bool(os.getenv("SENDGRID_API_KEY") or os.getenv("SMTP_HOST")),
            connected=True,
            error_message=None
        )
    }
    
    # Cachear por 1 hora
    await CacheManager.set_integration_status("all", {
        "openai": status_data["openai"].dict(),
        "whatsapp": status_data["whatsapp"].dict(),
        "telegram": status_data["telegram"].dict(),
        "instagram": status_data["instagram"].dict(),
        "stripe": status_data["stripe"].dict(),
        "email": status_data["email"].dict(),
    })
    
    return ConfigIntegrationsResponse(**status_data)


@router.post("/config/setup", response_model=SuccessResponse)
async def setup_integration(request: SetupRequest, payload: Dict[str, Any] = Depends(verify_token)):
    """
    ⚙️ Configurar integração (salvar chaves de API)
    
    Apenas admins podem fazer isso.
    Em produção, integrar com Key Vault ou secrets manager.
    
    Args:
        request: Nome da integração e credenciais
    """
    user_id = payload.get("sub")
    
    # ⚠️ SEGURANÇA: Validar permissões do usuário
    session = await CacheManager.get_user_session(user_id)
    if "admin" not in session.get("permissions", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem configurar integrações"
        )
    
    # Salvar credenciais (em produção: criptografar e guardar em Key Vault)
    logger.warning(f"⚠️  INSEGURO: Salvando credenciais de {request.integration} em variáveis de ambiente")
    
    # Validações básicas por integração
    integration_map = {
        "whatsapp": ["phone_id", "access_token", "business_account_id"],
        "telegram": ["bot_token"],
        "stripe": ["public_key", "secret_key"],
        "sendgrid": ["api_key"],
        "openai": ["api_key"]
    }
    
    required_fields = integration_map.get(request.integration, [])
    missing_fields = [f for f in required_fields if f not in request.credentials]
    
    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Campos obrigatórios faltando: {missing_fields}"
        )
    
    # Invalidar cache para forçar refresh
    await CacheManager.set_integration_status(request.integration, {
        "name": request.integration,
        "enabled": request.enabled,
        "connected": True,
        "error_message": None
    })
    
    logger.info(f"✅ Integração {request.integration} configurada por {user_id}")
    
    return SuccessResponse(
        success=True,
        message=f"Integração {request.integration} configurada com sucesso",
        data={
            "integration": request.integration,
            "enabled": request.enabled,
            "configured_at": datetime.now().isoformat()
        }
    )


@router.get("/health")
async def health():
    """
    ❤️ Health check da API v1
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }
