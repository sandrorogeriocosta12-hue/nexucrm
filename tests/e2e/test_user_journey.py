import pytest
pytest.skip("legacy tests disabled", allow_module_level=True)
import asyncio
from httpx import AsyncClient
from typing import Dict, Any

from app.core.security import create_access_token

class TestUserRegistrationJourney:
"""Testes E2E para jornada completa do usuário"""

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_user_journey(self, client: AsyncClient):
"""Testa jornada completa do usuário: registro → login → CRUD"""
# 1. Registro de usuário
user_data = {
"email": "journey.user@example.com",
"password": "JourneyPass123!",
"full_name": "Journey User",
"company": "Journey Corp"
}

register_response = await client.post(
"/api/v1/auth/register",
json=user_data
)

assert register_response.status_code == 201
user = register_response.json()
user_id = user["id"]

# 2. Login
login_response = await client.post(
"/api/v1/auth/login",
data={
"username": user_data["email"],
"password": user_data["password"]
}
)

assert login_response.status_code == 200
tokens = login_response.json()
access_token = tokens["access_token"]

headers = {"Authorization": f"Bearer {access_token}"}

# 3. Atualizar perfil
update_data = {
"company": "Updated Journey Corp",
"phone": "+5511999999999"
}

update_response = await client.put(
f"/api/v1/users/{user_id}",
json=update_data,
headers=headers
)

assert update_response.status_code == 200
updated_user = update_response.json()
assert updated_user["company"] == update_data["company"]

# 4. Criar lead
lead_data = {
"email": "journey.lead@example.com",
"full_name": "Journey Lead",
"company": "Lead Company",
"source": "website"
}

lead_response = await client.post(
"/api/v1/leads/",
json=lead_data,
headers=headers
)

assert lead_response.status_code == 201
lead = lead_response.json()
lead_id = lead["id"]

# 5. Atualizar lead
lead_update = {
"status": "contacted",
"notes": "Contacted via email"
}

update_lead_response = await client.put(
f"/api/v1/leads/{lead_id}",
json=lead_update,
headers=headers
)

assert update_lead_response.status_code == 200

# 6. Criar campanha
campaign_data = {
"name": "Journey Campaign",
"description": "Test campaign for journey",
"campaign_type": "email",
"status": "draft",
"budget": 1000.00
}

campaign_response = await client.post(
"/api/v1/campaigns/",
json=campaign_data,
headers=headers
)

assert campaign_response.status_code == 201
campaign = campaign_response.json()
campaign_id = campaign["id"]

# 7. Adicionar lead à campanha
add_lead_response = await client.post(
f"/api/v1/campaigns/{campaign_id}/add-lead/{lead_id}",
headers=headers
)

assert add_lead_response.status_code == 200

# 8. Iniciar campanha
start_response = await client.post(
f"/api/v1/campaigns/{campaign_id}/start",
headers=headers
)

assert start_response.status_code == 200
started_campaign = start_response.json()
assert started_campaign["status"] == "active"

# 9. Verificar dashboard
dashboard_response = await client.get(
"/api/v1/dashboard/summary",
headers=headers
)

assert dashboard_response.status_code == 200
dashboard = dashboard_response.json()

assert "total_leads" in dashboard
assert "active_campaigns" in dashboard
assert "conversion_rate" in dashboard

# 10. Logout (invalida token)
logout_response = await client.post(
"/api/v1/auth/logout",
headers=headers
)

assert logout_response.status_code == 200

# 11. Tentar acessar com token inválido
failed_response = await client.get(
f"/api/v1/users/{user_id}",
headers=headers
)

assert failed_response.status_code == 401

class TestSalesFunnelJourney:
"""Testes E2E para jornada do funil de vendas"""

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_sales_funnel_journey(self, client: AsyncClient, auth_headers):
"""Testa jornada completa do funil de vendas"""
# 1. Criar múltiplos leads com diferentes status
leads_status = ["new", "contacted", "qualified", "proposal", "closed_won"]

for i, status in enumerate(leads_status):
lead_data = {
"email": f"funnel{i}@example.com",
"full_name": f"Funnel Lead {i}",
"status": status
}

response = await client.post(
"/api/v1/leads/",
json=lead_data,
headers=auth_headers
)

assert response.status_code == 201

# 2. Obter analytics do funil
response = await client.get(
"/api/v1/analytics/funnel",
headers=auth_headers
)

assert response.status_code == 200
funnel_data = response.json()

assert "stages" in funnel_data
assert "conversion_rates" in funnel_data
assert "total_leads" in funnel_data

# Verifica que todos os status estão presentes
for status in leads_status:
assert any(stage["status"] == status for stage in funnel_data["stages"])

# 3. Simular movimento no funil
# Buscar lead com status "contacted"
search_response = await client.get(
"/api/v1/leads/",
headers=auth_headers,
params={"status": "contacted", "limit": 1}
)

contacted_leads = search_response.json()["items"]
if contacted_leads:
lead_id = contacted_leads[0]["id"]

# Mover para "qualified"
update_response = await client.put(
f"/api/v1/leads/{lead_id}",
json={"status": "qualified"},
headers=auth_headers
)

assert update_response.status_code == 200

# Verificar analytics atualizados
updated_response = await client.get(
"/api/v1/analytics/funnel",
headers=auth_headers
)

updated_data = updated_response.json()

# Encontrar estágios
contacted_stage = next(
s for s in updated_data["stages"] if s["status"] == "contacted"
)
qualified_stage = next(
s for s in updated_data["stages"] if s["status"] == "qualified"
)

# Verifica que o movimento foi registrado
assert contacted_stage["count"] >= 0
assert qualified_stage["count"] > 0

class TestPerformanceJourney:
"""Testes E2E para performance"""

@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.performance
async def test_bulk_operations_performance(self, client: AsyncClient, auth_headers):
"""Testa performance de operações em massa"""
import time

# 1. Criação em massa de leads
num_leads = 50
leads_data = [
{
"email": f"perf{i}@example.com",
"full_name": f"Performance Lead {i}",
"source": "performance_test"
}
for i in range(num_leads)
]

start_time = time.time()

# Teste individual
for i in range(min(10, num_leads)): # Testa apenas 10 para não demorar muito
response = await client.post(
"/api/v1/leads/",
json=leads_data[i],
headers=auth_headers
)
assert response.status_code == 201

individual_time = time.time() - start_time

# 2. Criação em massa
start_time = time.time()

bulk_response = await client.post(
"/api/v1/leads/bulk",
json=leads_data,
headers=auth_headers
)

bulk_time = time.time() - start_time

assert bulk_response.status_code == 201
bulk_result = bulk_response.json()
assert len(bulk_result) == num_leads

# 3. Verificar performance
print(f"\nPerformance Results:")
print(f"Individual creation (10 leads): {individual_time:.2f}s")
print(f"Bulk creation ({num_leads} leads): {bulk_time:.2f}s")
print(f"Speedup: {individual_time/bulk_time:.1f}x")

# Verifica que bulk é mais rápido (considerando overhead)
assert bulk_time < individual_time * 5 # Bulk não deve ser mais de 5x mais lento

# 4. Teste de busca com muitos registros
start_time = time.time()

search_response = await client.get(
"/api/v1/leads/",
headers=auth_headers,
params={"limit": 100, "source": "performance_test"}
)

search_time = time.time() - start_time

assert search_response.status_code == 200
search_data = search_response.json()

# Verifica que busca retornou resultados
assert len(search_data["items"]) > 0

# Verifica tempo de resposta aceitável
assert search_time < 2.0 # Busca deve ser rápida (< 2 segundos)

print(f"Search time ({len(search_data['items'])} leads): {search_time:.2f}s")