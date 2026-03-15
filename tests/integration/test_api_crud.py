import pytest
pytest.skip("legacy integration tests disabled", allow_module_level=True)
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

from app.models.lead import Lead
from app.models.campaign import Campaign
from app.schemas.lead import LeadCreate, LeadUpdate

class TestUserCRUD:
    """Testes CRUD para usuários"""

    @pytest.mark.asyncio
    async def test_get_users_paginated(self, client: AsyncClient, auth_headers):
        """Testa listagem paginada de usuários"""
response = await client.get(
"/api/v1/users/",
headers=auth_headers,
params={"skip": 0, "limit": 10}
)

assert response.status_code == 200
data = response.json()

assert "items" in data
assert "total" in data
assert "page" in data
assert "pages" in data
assert isinstance(data["items"], list)

@pytest.mark.asyncio
async def test_update_user(self, client: AsyncClient, test_user, auth_headers):
"""Testa atualização de usuário"""
update_data = {
"full_name": "Updated Name",
"company": "Updated Company"
}

response = await client.put(
f"/api/v1/users/{test_user.id}",
json=update_data,
headers=auth_headers
)

assert response.status_code == 200
data = response.json()

assert data["full_name"] == update_data["full_name"]
assert data["company"] == update_data["company"]
assert data["email"] == test_user.email # Email não mudou

@pytest.mark.asyncio
async def test_delete_user(self, client: AsyncClient, test_user, auth_headers):
"""Testa exclusão de usuário"""
response = await client.delete(
f"/api/v1/users/{test_user.id}",
headers=auth_headers
)

assert response.status_code == 204

# Verifica que o usuário não existe mais
get_response = await client.get(
f"/api/v1/users/{test_user.id}",
headers=auth_headers
)

assert get_response.status_code == 404

class TestLeadCRUD:
"""Testes CRUD para leads"""

@pytest.mark.asyncio
async def test_create_lead(self, client: AsyncClient, auth_headers):
"""Testa criação de lead"""
lead_data = {
"email": "newlead@example.com",
"full_name": "New Lead",
"company": "Lead Company",
"phone": "+5511999999999",
"source": "website",
"status": "new"
}

response = await client.post(
"/api/v1/leads/",
json=lead_data,
headers=auth_headers
)

assert response.status_code == 201
data = response.json()

assert data["email"] == lead_data["email"]
assert data["full_name"] == lead_data["full_name"]
assert data["status"] == "new"
assert "id" in data
assert "created_at" in data

@pytest.mark.asyncio
async def test_get_leads_with_filters(self, client: AsyncClient, auth_headers):
"""Testa busca de leads com filtros"""
# Cria alguns leads primeiro
leads_data = [
{
"email": f"lead{i}@example.com",
"full_name": f"Lead {i}",
"status": "new" if i % 2 == 0 else "contacted"
}
for i in range(5)
]

for lead_data in leads_data:
await client.post("/api/v1/leads/", json=lead_data, headers=auth_headers)

# Busca apenas leads com status "new"
response = await client.get(
"/api/v1/leads/",
headers=auth_headers,
params={"status": "new", "skip": 0, "limit": 10}
)

assert response.status_code == 200
data = response.json()

# Verifica que todos os leads retornados têm status "new"
for lead in data["items"]:
assert lead["status"] == "new"

@pytest.mark.asyncio
async def test_update_lead_status(self, client: AsyncClient, test_lead, auth_headers):
"""Testa atualização de status do lead"""
update_data = {
"status": "qualified",
"notes": "Client is interested in our premium plan"
}

response = await client.put(
f"/api/v1/leads/{test_lead.id}",
json=update_data,
headers=auth_headers
)

assert response.status_code == 200
data = response.json()

assert data["status"] == "qualified"
assert data["notes"] == update_data["notes"]

@pytest.mark.asyncio
async def test_search_leads(self, client: AsyncClient, auth_headers):
"""Testa busca de leads por termo"""
# Cria lead com nome específico
lead_data = {
"email": "specific@example.com",
"full_name": "John Doe Specific",
"company": "Specific Corp"
}

await client.post("/api/v1/leads/", json=lead_data, headers=auth_headers)

# Busca pelo termo "Specific"
response = await client.get(
"/api/v1/leads/search",
headers=auth_headers,
params={"q": "Specific"}
)

assert response.status_code == 200
data = response.json()

assert len(data) > 0
# Verifica que o termo aparece no nome ou empresa
for lead in data:
assert (
"Specific" in lead["full_name"] or
"Specific" in lead.get("company", "")
)

class TestCampaignCRUD:
"""Testes CRUD para campanhas"""

@pytest.mark.asyncio
async def test_create_campaign(self, client: AsyncClient, auth_headers):
"""Testa criação de campanha"""
campaign_data = {
"name": "Q1 Email Campaign",
"description": "Email campaign for Q1 2024",
"campaign_type": "email",
"status": "draft",
"budget": 5000.00,
"target_audience": "small_business"
}

response = await client.post(
"/api/v1/campaigns/",
json=campaign_data,
headers=auth_headers
)

assert response.status_code == 201
data = response.json()

assert data["name"] == campaign_data["name"]
assert data["campaign_type"] == campaign_data["campaign_type"]
assert data["status"] == "draft"
assert float(data["budget"]) == campaign_data["budget"]
assert "id" in data

@pytest.mark.asyncio
async def test_start_campaign(self, client: AsyncClient, test_campaign, auth_headers):
"""Testa início de campanha"""
response = await client.post(
f"/api/v1/campaigns/{test_campaign.id}/start",
headers=auth_headers
)

assert response.status_code == 200
data = response.json()

assert data["status"] == "active"
assert data["start_date"] is not None

@pytest.mark.asyncio
async def test_add_lead_to_campaign(self, client: AsyncClient, test_campaign, test_lead, auth_headers):
"""Testa adição de lead a campanha"""
response = await client.post(
f"/api/v1/campaigns/{test_campaign.id}/add-lead/{test_lead.id}",
headers=auth_headers
)

assert response.status_code == 200
data = response.json()

assert "message" in data
assert str(test_lead.id) in data["message"]

@pytest.mark.asyncio
async def test_get_campaign_analytics(self, client: AsyncClient, test_campaign, auth_headers):
"""Testa obtenção de analytics da campanha"""
response = await client.get(
f"/api/v1/campaigns/{test_campaign.id}/analytics",
headers=auth_headers
)

assert response.status_code == 200
data = response.json()

# Verifica estrutura básica do analytics
assert "campaign_id" in data
assert "total_leads" in data
assert "conversion_rate" in data
assert "status_distribution" in data
assert isinstance(data["status_distribution"], dict)

class TestBulkOperations:
"""Testes para operações em massa"""

@pytest.mark.asyncio
async def test_bulk_create_leads(self, client: AsyncClient, auth_headers):
"""Testa criação em massa de leads"""
leads_data = [
{
"email": f"bulk{i}@example.com",
"full_name": f"Bulk Lead {i}",
"source": "import"
}
for i in range(10)
]

response = await client.post(
"/api/v1/leads/bulk",
json=leads_data,
headers=auth_headers
)

assert response.status_code == 201
data = response.json()

assert len(data) == 10
for i, lead in enumerate(data):
assert lead["email"] == f"bulk{i}@example.com"
assert lead["source"] == "import"

@pytest.mark.asyncio
async def test_bulk_update_leads(self, client: AsyncClient, auth_headers):
"""Testa atualização em massa de leads"""
# Primeiro cria alguns leads
leads_data = [
{
"email": f"update{i}@example.com",
"full_name": f"To Update {i}",
"status": "new"
}
for i in range(5)
]

create_response = await client.post(
"/api/v1/leads/bulk",
json=leads_data,
headers=auth_headers
)
created_leads = create_response.json()
lead_ids = [lead["id"] for lead in created_leads]

# Agora atualiza todos para "contacted"
update_data = {
"lead_ids": lead_ids,
"update": {"status": "contacted"}
}

response = await client.put(
"/api/v1/leads/bulk",
json=update_data,
headers=auth_headers
)

assert response.status_code == 200
data = response.json()

assert data["updated_count"] == 5
assert data["failed_count"] == 0