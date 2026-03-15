import pytest
import requests

# Testes E2E diretos contra a API do Railway
RAILWAY_URL = "https://web-production-c726e.up.railway.app"

class TestRailwayAPI:
    """Testes E2E diretos contra a API implantada no Railway"""

    def test_health_check(self):
        """Testa o endpoint de health check"""
        response = requests.get(f"{RAILWAY_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        print("✅ Health check passou!")

    def test_root_endpoint(self):
        """Testa o endpoint raiz"""
        response = requests.get(f"{RAILWAY_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "Vexus CRM API" in data["service"]
        print("✅ Endpoint raiz passou!")

    def test_api_response_time(self):
        """Testa o tempo de resposta da API"""
        import time
        start_time = time.time()
        response = requests.get(f"{RAILWAY_URL}/health")
        end_time = time.time()

        assert response.status_code == 200
        duration = end_time - start_time
        assert duration < 2.0  # Deve responder em menos de 2 segundos
        print(f"✅ Performance test passou em {duration:.2f}s!")

print("🚀 Executando testes E2E contra Railway...")
