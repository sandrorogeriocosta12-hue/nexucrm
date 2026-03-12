"""
Authentication and JWT token management.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Configuration
SECRET_KEY = "vexus-secret-key-change-in-production"  # Change in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = None
    scopes: list[str] = []


class User(BaseModel):
    id: str
    email: str
    name: str
    role: str = "user"  # admin, manager, user
    is_active: bool = True


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token (longer expiry)."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if email is None:
            raise JWTError("Invalid token")
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(scopes=token_scopes, email=email, user_id=user_id)
    except JWTError:
        raise JWTError("Invalid token")
    return token_data


def create_tokens(user_id: int, email: str, name: str, role: str = "user") -> Token:
    """Create both access and refresh tokens."""
    access_data = {
        "sub": email,
        "user_id": user_id,
        "name": name,
        "role": role,
        "type": "access",
    }
    refresh_data = {"sub": email, "user_id": user_id, "type": "refresh"}

    access_token = create_access_token(access_data)
    refresh_token = create_refresh_token(refresh_data)

    return Token(access_token=access_token, refresh_token=refresh_token)


def create_email_verification_token(email: str) -> str:
    """Create JWT token for email verification (24 hour expiry)."""
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode = {"sub": email, "type": "email_verification", "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_email_token(token: str) -> Optional[str]:
    """Verify email verification token and return email."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "email_verification":
            return None
        return payload.get("sub")
    except JWTError:
        return None


def create_password_reset_token(email: str) -> str:
    """Create JWT token for password reset (1 hour expiry)."""
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    to_encode = {"sub": email, "type": "password_reset", "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify password reset token and return email."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "password_reset":
            return None
        return payload.get("sub")
    except JWTError:
        return None


def create_invite_token(
    email: str, company_id: str, role: str = "member", expires_in_days: int = 7
) -> str:
    """Create JWT token for team invites (7 day expiry)."""
    expire = datetime.utcnow() + timedelta(days=expires_in_days)
    to_encode = {
        "sub": email,
        "company_id": company_id,
        "role": role,
        "type": "invite",
        "exp": expire,
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_invite_token(token: str) -> Optional[dict]:
    """Verify invite token and return decoded data."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "invite":
            return None
        return {
            "email": payload.get("sub"),
            "company_id": payload.get("company_id"),
            "role": payload.get("role", "member"),
        }
    except JWTError:
        return None
