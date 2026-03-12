"""
Testes para endpoints estendidos de autenticação
- verify-email
- resend-verification
- forgot-password
- reset-password
"""

import pytest

pytest.skip("legacy auth extended tests disabled", allow_module_level=True)
from unittest.mock import patch, AsyncMock
from app.core.auth import (
    create_email_verification_token,
    verify_email_token,
    create_password_reset_token,
    verify_password_reset_token,
    get_password_hash,
    verify_password,
)


class TestEmailVerification:
    """Testes para verificação de email"""

    def test_create_email_verification_token(self):
        """Deve criar um token válido de verificação de email"""
        email = "test@example.com"
        token = create_email_verification_token(email)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_email_token_valid(self):
        """Deve verificar um token válido e retornar o email"""
        email = "test@example.com"
        token = create_email_verification_token(email)
        verified_email = verify_email_token(token)
        assert verified_email == email

    def test_verify_email_token_invalid(self):
        """Deve retornar None para um token inválido"""
        invalid_token = "invalid.token.here"
        result = verify_email_token(invalid_token)
        assert result is None

    def test_verify_email_token_expired(self):
        """Deve retornar None para um token expirado"""
        from datetime import datetime, timedelta
        from jose import jwt
        from app.core.auth import SECRET_KEY, ALGORITHM

        # Criar token com expiração no passado
        expire = datetime.utcnow() - timedelta(hours=1)
        to_encode = {
            "sub": "test@example.com",
            "type": "email_verification",
            "exp": expire,
        }
        expired_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        result = verify_email_token(expired_token)
        assert result is None


class TestPasswordReset:
    """Testes para redefinição de senha"""

    def test_create_password_reset_token(self):
        """Deve criar um token válido de reset"""
        email = "test@example.com"
        token = create_password_reset_token(email)
        assert token is not None
        assert isinstance(token, str)

    def test_verify_password_reset_token_valid(self):
        """Deve verificar um token de reset válido"""
        email = "test@example.com"
        token = create_password_reset_token(email)
        verified_email = verify_password_reset_token(token)
        assert verified_email == email

    def test_verify_password_reset_token_invalid(self):
        """Deve retornar None para token inválido"""
        invalid_token = "invalid.token.here"
        result = verify_password_reset_token(invalid_token)
        assert result is None


class TestPasswordHashing:
    """Testes para hashing de senha"""

    def test_get_password_hash(self):
        """Deve gerar hash válido para uma senha"""
        password = "my_secure_password_123"
        hashed = get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Deve validar uma senha correta contra seu hash"""
        password = "my_secure_password_123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Deve rejeitar uma senha incorreta"""
        password = "my_secure_password_123"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        assert verify_password(wrong_password, hashed) is False
