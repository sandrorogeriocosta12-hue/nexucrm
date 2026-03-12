import pytest
pytest.skip("legacy unit tests disabled", allow_module_level=True)
from datetime import datetime
from pydantic import ValidationError

from app.schemas.user import UserCreate, UserUpdate, UserInDB
from app.schemas.lead import LeadCreate, LeadUpdate, LeadInDB
from app.schemas.campaign import CampaignCreate, CampaignUpdate
from app.core.security import verify_password

class TestUserModels:
"""Testes para modelos de usuário"""

def test_user_create_valid(self):
"""Testa criação de usuário válido"""
user_data = {
"email": "test@example.com",
"password": "StrongPass123!",
"full_name": "Test User",
}

user = UserCreate(**user_data)

assert user.email == user_data["email"]
assert user.password == user_data["password"]
assert user.full_name == user_data["full_name"]
assert hasattr(user, "created_at")
assert hasattr(user, "updated_at")

def test_user_create_invalid_email(self):
"""Testa criação de usuário com email inválido"""
with pytest.raises(ValidationError):
UserCreate(
email="invalid-email",
password="StrongPass123!",
full_name="Test User"
)

def test_user_create_weak_password(self):
"""Testa criação de usuário com senha fraca"""
with pytest.raises(ValidationError):
UserCreate(
email="test@example.com",
password="weak",
full_name="Test User"
)

def test_user_update_partial(self):
"""Testa atualização parcial de usuário"""
update_data = {"full_name": "Updated Name"}
user_update = UserUpdate(**update_data)

assert user_update.full_name == "Updated Name"
assert user_update.email is None
assert user_update.password is None

class TestLeadModels:
"""Testes para modelos de lead"""

def test_lead_create_valid(self):
"""Testa criação de lead válido"""
lead_data = {
"email": "lead@example.com",
"full_name": "Lead Test",
"company": "Test Company",
"phone": "+5511999999999",
"source": "website",
"status": "new"
}

lead = LeadCreate(**lead_data)

assert lead.email == lead_data["email"]
assert lead.full_name == lead_data["full_name"]
assert lead.company == lead_data["company"]
assert lead.phone == lead_data["phone"]
assert lead.source == lead_data["source"]
assert lead.status == lead_data["status"]

def test_lead_create_without_optional(self):
"""Testa criação de lead sem campos opcionais"""
lead_data = {
"email": "lead@example.com",
"full_name": "Lead Test",
"status": "new"
}

lead = LeadCreate(**lead_data)

assert lead.email == lead_data["email"]
assert lead.full_name == lead_data["full_name"]
assert lead.company is None
assert lead.phone is None
assert lead.source == "manual"

def test_lead_update_status(self):
"""Testa atualização de status do lead"""
update_data = {"status": "contacted", "notes": "Client contacted"}
lead_update = LeadUpdate(**update_data)

assert lead_update.status == "contacted"
assert lead_update.notes == "Client contacted"
assert lead_update.email is None

class TestCampaignModels:
"""Testes para modelos de campanha"""

def test_campaign_create_valid(self):
"""Testa criação de campanha válida"""
campaign_data = {
"name": "Q1 Marketing Campaign",
"description": "Campaign for Q1 2024",
"campaign_type": "email",
"status": "draft",
"start_date": "2024-01-01",
"end_date": "2024-03-31",
"budget": 10000.00
}

campaign = CampaignCreate(**campaign_data)

assert campaign.name == campaign_data["name"]
assert campaign.description == campaign_data["description"]
assert campaign.campaign_type == campaign_data["campaign_type"]
assert campaign.status == campaign_data["status"]
assert campaign.budget == campaign_data["budget"]

def test_campaign_create_invalid_dates(self):
"""Testa criação com datas inválidas"""
with pytest.raises(ValidationError):
CampaignCreate(
name="Test Campaign",
campaign_type="email",
status="draft",
start_date="2024-03-31",
end_date="2024-01-01" # End before start
)

class TestSecurity:
"""Testes para funções de segurança"""

def test_password_hashing_and_verification(self):
"""Testa hash e verificação de senha"""
from app.core.security import get_password_hash

plain_password = "TestPass123!"
hashed_password = get_password_hash(plain_password)

# Verifica que a senha hash não é igual à original
assert hashed_password != plain_password

# Verifica que a senha pode ser verificada
assert verify_password(plain_password, hashed_password)

# Verifica que senha errada não passa
assert not verify_password("WrongPass", hashed_password)