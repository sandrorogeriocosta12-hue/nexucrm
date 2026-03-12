import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.services.user_service import UserService
from app.services.lead_service import LeadService
from app.services.campaign_service import CampaignService
from app.schemas.user import UserCreate
from app.schemas.lead import LeadCreate
from app.schemas.campaign import CampaignCreate
from app.core.exceptions import (
NotFoundException,
DuplicateEntryException,
BusinessRuleException
)

class TestUserService:
"""Testes para UserService"""

@pytest_asyncio.fixture
async def mock_db(self):
"""Mock para sessão do banco de dados"""
mock_session = AsyncMock()
mock_session.execute = AsyncMock()
mock_session.commit = AsyncMock()
mock_session.rollback = AsyncMock()

# Mock para query
mock_query = MagicMock()
mock_query.filter = MagicMock(return_value=mock_query)
mock_query.offset = MagicMock(return_value=mock_query)
mock_query.limit = MagicMock(return_value=mock_query)
mock_query.all = AsyncMock(return_value=[])
mock_query.first = AsyncMock(return_value=None)

mock_session.exec.return_value = mock_query
return mock_session

@pytest_asyncio.fixture
async def user_service(self, mock_db):
"""Fixture para UserService"""
return UserService(mock_db)

async def test_create_user_success(self, user_service, sample_user_data):
"""Testa criação bem-sucedida de usuário"""
user_create = UserCreate(**sample_user_data)

# Mock para resultado da criação
mock_result = MagicMock()
mock_result.scalar_one = MagicMock(return_value=MagicMock(
id=1,
email=sample_user_data["email"],
full_name=sample_user_data["full_name"],
is_active=True,
created_at=datetime.utcnow()
))

user_service.db.exec.return_value = mock_result

result = await user_service.create(user_create)

assert result.email == sample_user_data["email"]
assert result.full_name == sample_user_data["full_name"]
assert result.is_active is True
assert hasattr(result, "id")

# Verifica que commit foi chamado
user_service.db.commit.assert_called_once()

async def test_create_user_duplicate_email(self, user_service, sample_user_data):
"""Testa criação de usuário com email duplicado"""
user_create = UserCreate(**sample_user_data)

# Mock para verificar se usuário já existe
mock_existing_user = MagicMock()
mock_existing_user.scalar_one_or_none.return_value = MagicMock(
email=sample_user_data["email"]
)

user_service.db.exec.return_value = mock_existing_user

with pytest.raises(DuplicateEntryException):
await user_service.create(user_create)

async def test_get_user_by_id_found(self, user_service):
"""Testa busca de usuário por ID encontrado"""
user_id = 1
mock_user = MagicMock(
id=user_id,
email="test@example.com",
full_name="Test User",
is_active=True
)

mock_result = MagicMock()
mock_result.scalar_one_or_none.return_value = mock_user
user_service.db.exec.return_value = mock_result

result = await user_service.get_by_id(user_id)

assert result.id == user_id
assert result.email == "test@example.com"

async def test_get_user_by_id_not_found(self, user_service):
"""Testa busca de usuário por ID não encontrado"""
user_id = 999

mock_result = MagicMock()
mock_result.scalar_one_or_none.return_value = None
user_service.db.exec.return_value = mock_result

with pytest.raises(NotFoundException):
await user_service.get_by_id(user_id)

async def test_authenticate_user_success(self, user_service):
"""Testa autenticação bem-sucedida"""
email = "test@example.com"
password = "TestPass123!"

mock_user = MagicMock()
mock_user.hashed_password = "$2b$12$..." # Mock hash
mock_user.is_active = True

mock_result = MagicMock()
mock_result.scalar_one_or_none.return_value = mock_user
user_service.db.exec.return_value = mock_result

with patch("app.core.security.verify_password", return_value=True):
result = await user_service.authenticate(email, password)

assert result == mock_user

async def test_authenticate_user_wrong_password(self, user_service):
"""Testa autenticação com senha errada"""
email = "test@example.com"
password = "WrongPass"

mock_user = MagicMock()
mock_user.hashed_password = "$2b$12$..."
mock_user.is_active = True

mock_result = MagicMock()
mock_result.scalar_one_or_none.return_value = mock_user
user_service.db.exec.return_value = mock_result

with patch("app.core.security.verify_password", return_value=False):
result = await user_service.authenticate(email, password)

assert result is None

class TestLeadService:
"""Testes para LeadService"""

@pytest_asyncio.fixture
async def lead_service(self, mock_db):
"""Fixture para LeadService"""
return LeadService(mock_db)

async def test_create_lead_success(self, lead_service, sample_lead_data):
"""Testa criação bem-sucedida de lead"""
lead_create = LeadCreate(**sample_lead_data)

mock_result = MagicMock()
mock_result.scalar_one.return_value = MagicMock(
id=1,
email=sample_lead_data["email"],
full_name=sample_lead_data["full_name"],
status="new",
created_at=datetime.utcnow()
)

lead_service.db.exec.return_value = mock_result

result = await lead_service.create(lead_create)

assert result.email == sample_lead_data["email"]
assert result.full_name == sample_lead_data["full_name"]
assert result.status == "new"
lead_service.db.commit.assert_called_once()

async def test_update_lead_status(self, lead_service):
"""Testa atualização de status do lead"""
lead_id = 1
update_data = {"status": "contacted", "notes": "Called client"}

mock_lead = MagicMock()
mock_lead.id = lead_id
mock_lead.status = "new"

mock_result = MagicMock()
mock_result.scalar_one_or_none.return_value = mock_lead
lead_service.db.exec.return_value = mock_result

result = await lead_service.update(lead_id, update_data)

assert result.status == "contacted"
lead_service.db.commit.assert_called_once()

async def test_get_leads_by_status(self, lead_service):
"""Testa busca de leads por status"""
status = "contacted"

mock_leads = [
MagicMock(id=1, email="lead1@example.com", status=status),
MagicMock(id=2, email="lead2@example.com", status=status),
]

mock_result = MagicMock()
mock_result.scalars.return_value.all.return_value = mock_leads
lead_service.db.exec.return_value = mock_result

result = await lead_service.get_by_status(status)

assert len(result) == 2
assert all(lead.status == status for lead in result)

class TestCampaignService:
"""Testes para CampaignService"""

@pytest_asyncio.fixture
async def campaign_service(self, mock_db):
"""Fixture para CampaignService"""
return CampaignService(mock_db)

async def test_create_campaign_with_budget(self):
"""Testa criação de campanha com orçamento"""
mock_db = AsyncMock()
service = CampaignService(mock_db)

campaign_data = {
"name": "Test Campaign",
"description": "Test Description",
"campaign_type": "email",
"status": "draft",
"budget": 5000.00
}

campaign_create = CampaignCreate(**campaign_data)

mock_result = MagicMock()
mock_result.scalar_one.return_value = MagicMock(
id=1,
name=campaign_data["name"],
budget=campaign_data["budget"],
status="draft"
)

service.db.exec.return_value = mock_result

result = await service.create(campaign_create)

assert result.name == campaign_data["name"]
assert result.budget == campaign_data["budget"]
service.db.commit.assert_called_once()

async def test_start_campaign_success(self):
"""Testa início de campanha bem-sucedido"""
mock_db = AsyncMock()
service = CampaignService(mock_db)
campaign_id = 1

mock_campaign = MagicMock()
mock_campaign.id = campaign_id
mock_campaign.status = "draft"
mock_campaign.start_date = None

mock_result = MagicMock()
mock_result.scalar_one_or_none.return_value = mock_campaign
service.db.exec.return_value = mock_result

result = await service.start_campaign(campaign_id)

assert result.status == "active"
assert result.start_date is not None
service.db.commit.assert_called_once()

async def test_start_campaign_already_active(self):
"""Testa início de campanha já ativa"""
mock_db = AsyncMock()
service = CampaignService(mock_db)
campaign_id = 1

mock_campaign = MagicMock()
mock_campaign.id = campaign_id
mock_campaign.status = "active"

mock_result = MagicMock()
mock_result.scalar_one_or_none.return_value = mock_campaign
service.db.exec.return_value = mock_result

with pytest.raises(BusinessRuleException):
await service.start_campaign(campaign_id)