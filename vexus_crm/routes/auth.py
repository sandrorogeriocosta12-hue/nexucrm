"""
Basic authentication router for Vexus CRM.
Provides simple in-memory user store with JWT tokens.
"""

import time
from typing import Dict, Optional

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr

from app.core.auth import (
    ALGORITHM,
    SECRET_KEY,
    Token,
    TokenData,
    create_email_verification_token,
    create_password_reset_token,
    create_tokens,
    get_password_hash,
    verify_email_token,
    verify_password,
    verify_password_reset_token,
    verify_token,
)

# encryption helpers
try:
    from vexus_crm.utils.crypto import encrypt, decrypt
except ImportError:
    # fallback stubs if crypto module unavailable
    def encrypt(s: str) -> str:
        return s
    def decrypt(s: str) -> str:
        return s

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# using SQLAlchemy models for persistence
from typing import Generator

from sqlalchemy.orm import Session

from vexus_crm.database import get_db
from vexus_crm.models import User as UserModel


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    company: Optional[str] = None


class LoginRequest(BaseModel):
    username: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: bool = True

    class Config:
        orm_mode = True


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> UserModel:
    try:
        data = verify_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    email = data.email
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


@router.post("/register", response_model=UserOut, status_code=201)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # check existing
    existing = db.query(UserModel).filter(UserModel.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = get_password_hash(user.password)
    db_user = UserModel(
        email=user.email,
        password_hash=hashed,
        name=user.full_name,
        role="user",
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=Token)
async def login(form_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    tokens = create_tokens(
        user_id=user.id,
        email=user.email,
        name=user.name or "",
        role=user.role or "user",
    )
    # convert to dict for JSON serialization
    token_data = tokens.model_dump() if hasattr(tokens, 'model_dump') else tokens.dict()
    # Return tokens and set as HttpOnly secure cookies
    response = JSONResponse(token_data)
    response.set_cookie(
        "access_token",
        token_data["access_token"],
        httponly=True,
        secure=False,  # Set True in production with HTTPS
        samesite="lax",
        max_age=3600,  # 1 hour
    )
    response.set_cookie(
        "refresh_token",
        token_data["refresh_token"],
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=86400,  # 24 hours
    )
    return response


@router.get("/me", response_model=UserOut)
async def me(current: UserModel = Depends(get_current_user)):
    # return user data
    return UserOut(
        id=current.id,
        email=current.email,
        name=current.name,
        role=current.role,
        is_active=current.is_active,
    )


@router.post("/refresh", response_model=Token)
async def refresh(req: RefreshRequest, db: Session = Depends(get_db)):
    try:
        data = verify_token(req.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    from jose import jwt

    payload = jwt.decode(req.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token is not a refresh token")
    email = data.email
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    tokens = create_tokens(
        user_id=user.id,
        email=user.email,
        name=user.name or "",
        role=user.role or "user",
    )
    token_data = tokens.model_dump() if hasattr(tokens, 'model_dump') else tokens.dict()
    # Set new tokens as cookies
    response = JSONResponse(token_data)
    # use serialized dict to set cookie values
    response.set_cookie("access_token", token_data["access_token"], httponly=True, secure=False, samesite="lax", max_age=3600)
    response.set_cookie("refresh_token", token_data["refresh_token"], httponly=True, secure=False, samesite="lax", max_age=86400)
    return response


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class VerifyEmailRequest(BaseModel):
    token: str


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # check user exists
    user = db.query(UserModel).filter(UserModel.email == req.email).first()
    if not user:
        # do not reveal existence
        return {
            "ok": True,
            "message": "If that email exists, a reset link has been sent.",
        }
    token = create_password_reset_token(req.email)
    # in real app send email; here we return token for tests
    return {"ok": True, "reset_token": token}


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    email = verify_password_reset_token(req.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    user.password_hash = get_password_hash(req.new_password)
    db.commit()
    return {"ok": True, "message": "Password updated"}


@router.post("/verify-email")
async def verify_email(req: VerifyEmailRequest, db: Session = Depends(get_db)):
    email = verify_email_token(req.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    user.is_verified = True
    db.commit()
    return {"ok": True}


@router.post("/resend-verification")
async def resend_verification(req: ForgotPasswordRequest):
    # generate new token
    token = create_email_verification_token(req.email)
    return {"ok": True, "token": token}


@router.post("/logout")
async def logout(response: Response):
    # clear cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"ok": True}

@router.get("/users/profile")
async def profile(current: UserModel = Depends(get_current_user)):
    # return Pydantic model with selected fields
    return {
        "id": current.id,
        "email": current.email,
        "full_name": current.name,
        "company": current.company if hasattr(current, "company") else None,
        "role": current.role,
        "is_active": current.is_active,
        "is_verified": getattr(current, "is_verified", None),
    }


class UserSettings(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    company: Optional[str] = None
    # Communication integrations
    whatsapp_api_key: Optional[str] = None
    whatsapp_phone_id: Optional[str] = None
    webhook_url: Optional[str] = None
    # AI agent settings
    ai_provider: Optional[str] = None
    ai_api_key: Optional[str] = None
    ai_model: Optional[str] = None
    ai_system_prompt: Optional[str] = None
    ai_enabled: Optional[bool] = None


@router.put("/users/settings", response_model=UserOut)
async def update_settings(
    settings: UserSettings,
    current: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update profile information. Only provided fields are changed."""
    # avoid changing to an email already taken
    if settings.email and settings.email != current.email:
        existing = db.query(UserModel).filter(UserModel.email == settings.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        current.email = settings.email
    if settings.name is not None:
        current.name = settings.name
    if settings.role is not None:
        current.role = settings.role
    if settings.company is not None:
        setattr(current, "company", settings.company)
    # Persist user settings JSON in Config table under a per-user key
    user_key = f"user:{current.id}:settings"
    # convert to dict, keep only provided fields
    settings_json = settings.dict(exclude_unset=True)
    # **ENCRYPT sensitive values before storing**
    for k in list(settings_json.keys()):
        if k.endswith("api_key") or k in ("webhook_url", "email_smtp_password"):
            if settings_json[k]:
                settings_json[k] = encrypt(settings_json[k])
    # import Config model here to avoid circular import at top if needed
    from vexus_crm.models import Config as ConfigModel

    cfg = db.query(ConfigModel).filter(ConfigModel.key == user_key).first()
    if cfg:
        # merge with existing stored settings so we don't erase earlier values
        existing = cfg.value or {}
        if isinstance(existing, dict):
            # produce new dict object to ensure ORM marks it as changed
            merged = {**existing, **settings_json}
            cfg.value = merged
        else:
            cfg.value = settings_json
    else:
        cfg = ConfigModel(
            key=user_key,
            value=settings_json,
            description=f"Settings for user {current.id}",
        )
        db.add(cfg)
    db.commit()
    db.refresh(current)
    return current


@router.get("/users/settings")
async def get_user_settings(
    current: UserModel = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Return stored settings for the current user, if any. Decrypt sensitive values."""
    from vexus_crm.models import Config as ConfigModel

    user_key = f"user:{current.id}:settings"
    cfg = db.query(ConfigModel).filter(ConfigModel.key == user_key).first()
    if not cfg:
        return {
            "name": current.name,
            "email": current.email,
            "role": current.role,
            "company": getattr(current, "company", None),
        }
    # **DECRYPT sensitive fields before returning**
    val = cfg.value or {}
    for k in list(val.keys()):
        if k.endswith("api_key") or k in ("webhook_url", "email_smtp_password"):
            if val.get(k):
                try:
                    val[k] = decrypt(val[k])
                except Exception:
                    pass  # if decryption fails, return as-is for now
    return val
    val = cfg.value or {}
    for k in list(val.keys()):
        if k.endswith("api_key") or k == "webhook_url":
            if val.get(k):
                val[k] = decrypt(val[k])
    return val


@router.post("/users/test-whatsapp-webhook")
async def test_whatsapp_webhook(
    payload: Dict[str, str], current: UserModel = Depends(get_current_user)
):
    """Server-side helper that POSTs a sample message to a provided webhook URL.

    The client can call this to work around CORS/policy restrictions when
    testing an external WhatsApp webhook.  The payload should include a
    `url` key containing the webhook endpoint to hit.
    """
    url = payload.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="Missing url")
    if not HAS_HTTPX:
        raise HTTPException(status_code=500, detail="httpx não instalado. Webhook test não disponível.")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                url,
                json={
                    "from": "whatsapp:+5511999999999",
                    "to": "whatsapp:+5511888888888",
                    "message": "Webhook test — Vexus App",
                    "timestamp": int(time.time()),
                },
            )
        return {"status_code": response.status_code, "body": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
