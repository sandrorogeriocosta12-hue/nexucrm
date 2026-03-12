import pytest
pytest.skip("legacy performance tests disabled", allow_module_level=True)
import asyncio
from typing import List
from datetime import datetime

import pytest_asyncio
from httpx import AsyncClient, Limits, Timeout

from app.core.config import settings

class TestLoadPerformance:
"""Testes de performance sob carga"""

@pytest_asyncio.fixture
async def load_client(self):
"""Cliente HTTP com configurações para testes de carga"""
timeout = Timeout(30.0)
limits = Limits(max_connections=100, max_keepalive_connections=20)

async with AsyncClient(
timeout=timeout,
limits=limits,
base_url="http://localhost:8000"
) as client:
yield client

@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_user_registration(self, load_client):
"""Testa registro concorrente de usuários"""
num_users = 50
tasks = []

async def register_user(user_id: int):
user_data = {
"email": f"loaduser{user_id}@example.com",
"password": f"LoadPass{user_id}!",
"full_name": f"Load User {user_id}"
}

try:
response = await load_client.post(
"/api/v1/auth/register",
json=user_data
)
return response.status_code == 201
except Exception as e:
print(f"Error registering user {user_id}: {e}")
return False

# Executa registros concorrentes
start_time = datetime.now()

for i in range(num_users):
task = asyncio.create_task(register_user(i))
tasks.append(task)

results = await asyncio.gather(*tasks, return_exceptions=True)

end_time = datetime.now()
duration = (end_time - start_time).total_seconds()

# Analisa resultados
successful = sum(1 for r in results if r is True)
failed = sum(1 for r in results if isinstance(r, Exception) or r is False)

print(f"\nConcurrent Registration Results:")
print(f"Total requests: {num_users}")
print(f"Successful: {successful}")
print(f"Failed: {failed}")
print(f"Duration: {duration:.2f}s")
print(f"Requests per second: {num_users/duration:.2f}")

assert successful > num_users * 0.9 # 90% de sucesso
assert duration < 30 # Menos de 30 segundos

@pytest.mark.performance
@pytest.mark.asyncio
async def test_high_concurrency_lead_creation(self, load_client, auth_headers):
"""Testa criação de leads com alta concorrência"""
num_leads = 100
batch_size = 10
all_successful = True

async def create_leads_batch(batch_id: int, num_in_batch: int):
batch_success = True
for i in range(num_in_batch):
lead_id = batch_id * batch_size + i
lead_data = {
"email": f"loadlead{lead_id}@example.com",
"full_name": f"Load Lead {lead_id}",
"source": "load_test"
}

try:
response = await load_client.post(
"/api/v1/leads/",
json=lead_data,
headers=auth_headers
)
if response.status_code != 201:
batch_success = False
print(f"Batch {batch_id}, Lead {i}: Failed with status {response.status_code}")
except Exception as e:
batch_success = False
print(f"Batch {batch_id}, Lead {i}: Error {e}")

return batch_success

# Executa em batches concorrentes
start_time = datetime.now()

num_batches = (num_leads + batch_size - 1) // batch_size
tasks = []

for batch_id in range(num_batches):
num_in_batch = min(batch_size, num_leads - batch_id * batch_size)
task = asyncio.create_task(create_leads_batch(batch_id, num_in_batch))
tasks.append(task)

batch_results = await asyncio.gather(*tasks)

end_time = datetime.now()
duration = (end_time - start_time).total_seconds()

successful_batches = sum(1 for r in batch_results if r is True)

print(f"\nHigh Concurrency Lead Creation:")
print(f"Total leads: {num_leads}")
print(f"Batch size: {batch_size}")
print(f"Successful batches: {successful_batches}/{num_batches}")
print(f"Duration: {duration:.2f}s")
print(f"Leads per second: {num_leads/duration:.2f}")

assert successful_batches == num_batches # Todos os batches devem ter sucesso
assert duration < 60 # Menos de 60 segundos

@pytest.mark.performance
@pytest.mark.asyncio
async def test_database_query_performance(self, load_client, auth_headers):
"""Testa performance de queries do banco de dados"""
import time

# Primeiro, cria dados de teste
num_test_leads = 1000

print(f"\nCreating {num_test_leads} test leads...")
leads_data = [
{
"email": f"perfquery{i}@example.com",
"full_name": f"Perf Query Lead {i}",
"status": "new" if i % 3 == 0 else "contacted" if i % 3 == 1 else "qualified",
"source": "web" if i % 2 == 0 else "import"
}
for i in range(num_test_leads)
]

# Cria em batches para não sobrecarregar
batch_size = 100
for i in range(0, num_test_leads, batch_size):
batch = leads_data[i:i+batch_size]
response = await load_client.post(
"/api/v1/leads/bulk",
json=batch,
headers=auth_headers
)
assert response.status_code == 201

# Testa diferentes queries
test_cases = [
("Simple query - all leads", "/api/v1/leads/", {"limit": 100}),
("Filter by status", "/api/v1/leads/", {"status": "qualified", "limit": 100}),
("Filter by source", "/api/v1/leads/", {"source": "web", "limit": 100}),
("Search by name", "/api/v1/leads/search", {"q": "Perf Query"}),
("Complex query", "/api/v1/leads/", {
"status": "qualified",
"source": "web",
"skip": 0,
"limit": 50,
"sort_by": "created_at",
"sort_order": "desc"
})
]

results = []

for name, endpoint, params in test_cases:
# Executa query múltiplas vezes para média
times = []
for _ in range(5):
start_time = time.time()
response = await load_client.get(
endpoint,
headers=auth_headers,
params=params
)
end_time = time.time()

assert response.status_code == 200
times.append(end_time - start_time)

avg_time = sum(times) / len(times)
results.append((name, avg_time, response.json()))

print(f"{name}: {avg_time:.3f}s")

# Verifica tempo máximo aceitável
assert avg_time < 1.0 # Queries devem ser rápidas

# Testa query com muitos resultados
print(f"\nTesting query with large result set...")
start_time = time.time()
response = await load_client.get(
"/api/v1/leads/",
headers=auth_headers,
params={"limit": 500}
)
end_time = time.time()

assert response.status_code == 200
data = response.json()

print(f"Large query ({len(data['items'])} items): {end_time-start_time:.3f}s")
assert (end_time - start_time) < 2.0 # Query grande ainda deve ser rápida