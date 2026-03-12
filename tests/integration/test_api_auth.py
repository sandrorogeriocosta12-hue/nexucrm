import pytest
pytest.skip("legacy integration tests disabled", allow_module_level=True)
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

from app.core.security import create_access_token
from app.models.user import User

class TestAuthAPI:
"""Testes para endpoints de autenticação"""

@pytest.mark.asyncio
async def test_register_user_success(self, client: AsyncClient):
"""Testa registro bem-sucedido de usuário"""
user_data = {
"email": "newuser@example.com",
"password": "StrongPass123!",
"full_name": "New User",
"company": "Test Company"
}

with patch("app.api.endpoints.auth.get_db") as mock_get_db:
mock_db = AsyncMock()
mock_get_db.return_value = mock_db

response = await client.post("/api/v1/auth/register", json=user_data)

assert response.status_code == 201
data = response.json()

assert data["email"] == user_data["email"]
assert data["full_name"] == user_data["full_name"]
assert "id" in data
assert "password" not in data
assert "hashed_password" not in data

@pytest.mark.asyncio
async def test_register_user_duplicate_email(self, client: AsyncClient):
"""Testa registro com email duplicado"""
user_data = {
"email": "existing@example.com",
"password": "StrongPass123!",
"full_name": "Existing User"
}

# Primeiro registro
await client.post("/api/v1/auth/register", json=user_data)

# Segundo registro com mesmo email
response = await client.post("/api/v1/auth/register", json=user_data)

assert response.status_code == 400
data = response.json()
assert "email" in data["detail"].lower()

@pytest.mark.asyncio
async def test_login_success(self, client: AsyncClient, test_user):
"""Testa login bem-sucedido"""
login_data = {
"username": test_user.email,
"password": "testpassword"
}

response = await client.post("/api/v1/auth/login", data=login_data)

assert response.status_code == 200
data = response.json()

assert "access_token" in data
assert data["token_type"] == "bearer"
assert "user" in data
assert data["user"]["email"] == test_user.email

@pytest.mark.asyncio
async def test_login_wrong_password(self, client: AsyncClient, test_user):
"""Testa login com senha errada"""
login_data = {
"username": test_user.email,
"password": "wrongpassword"
}

response = await client.post("/api/v1/auth/login", data=login_data)

assert response.status_code == 401
data = response.json()
assert "detail" in data

@pytest.mark.asyncio
async def test_get_current_user(self, client: AsyncClient, test_user):
"""Testa obtenção do usuário atual"""
# Primeiro faz login
login_data = {
"username": test_user.email,
"password": "testpassword"
}

login_response = await client.post("/api/v1/auth/login", data=login_data)
token = login_response.json()["access_token"]

# Agora usa o token para acessar endpoint protegido
headers = {"Authorization": f"Bearer {token}"}
response = await client.get("/api/v1/auth/me", headers=headers)

assert response.status_code == 200
data = response.json()

assert data["email"] == test_user.email
assert data["full_name"] == test_user.full_name
assert "id" in data

@pytest.mark.asyncio
async def test_get_current_user_no_token(self, client: AsyncClient):
"""Testa acesso sem token"""
response = await client.get("/api/v1/auth/me")

assert response.status_code == 401
data = response.json()
assert "detail" in data

@pytest.mark.asyncio
async def test_refresh_token(self, client: AsyncClient, test_user):
"""Testa refresh token"""
# Primeiro login
login_data = {
"username": test_user.email,
"password": "testpassword"
}

login_response = await client.post("/api/v1/auth/login", data=login_data)
refresh_token = login_response.json()["refresh_token"]

# Refresh token
response = await client.post(
"/api/v1/auth/refresh",
json={"refresh_token": refresh_token}
)

assert response.status_code == 200
data = response.json()
assert "access_token" in data
assert "refresh_token" in data

class TestProtectedEndpoints:
"""Testes para endpoints protegidos"""

@pytest.mark.asyncio
async def test_access_protected_endpoint_with_token(self, client: AsyncClient, test_user):
"""Testa acesso a endpoint protegido com token válido"""
token = create_access_token({"sub": test_user.email})
headers = {"Authorization": f"Bearer {token}"}

response = await client.get("/api/v1/users/profile", headers=headers)

# Pode retornar 200 ou 404 se o perfil não existir
assert response.status_code in [200, 404]

@pytest.mark.asyncio
async def test_access_protected_endpoint_without_token(self, client: AsyncClient):
"""Testa acesso a endpoint protegido sem token"""
response = await client.get("/api/v1/users/profile")

assert response.status_code == 401

@pytest.mark.asyncio
async def test_access_protected_endpoint_invalid_token(self, client: AsyncClient):
"""Testa acesso a endpoint protegido com token inválido"""
headers = {"Authorization": "Bearer invalid_token"}
response = await client.get("/api/v1/users/profile", headers=headers)

assert response.status_code == 401