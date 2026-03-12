"""
Comprehensive tests for Vexus CRM API.
"""
import pytest

pytest.skip("legacy root tests disabled", allow_module_level=True)
import os
from fastapi.testclient import TestClient

# Avoid circular imports - get app directly from main module
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.api_main import app, mock_users
from app.core.auth import get_password_hash

client = TestClient(app)


@pytest.fixture
def setup_user():
    """Setup test user."""
    mock_users["test@vexus.com"] = {
        "id": 999,
        "email": "test@vexus.com",
        "password_hash": get_password_hash("test123"),
        "name": "Test User",
        "role": "user",
    }
    yield
    del mock_users["test@vexus.com"]


@pytest.fixture
def auth_token(setup_user):
    """Get auth token for test user and ensure cookie jar is populated."""
    response = client.post(
        "/auth/login", json={"email": "test@vexus.com", "password": "test123"}
    )
    # TestClient automatically stores cookies; they can be accessed via client.cookies
    assert "access_token" in client.cookies
    return response.json()["access_token"]


class TestHealth:
    def test_health_check(self):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestAuth:
    def test_signup_success(self):
        """Test successful signup."""
        response = client.post(
            "/auth/signup",
            json={
                "email": "newuser@vexus.com",
                "password": "password123",
                "name": "New User",
            },
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "refresh_token" in response.json()

    def test_signup_duplicate(self):
        """Test signup with duplicate email."""
        client.post(
            "/auth/signup",
            json={"email": "dup@vexus.com", "password": "pass123", "name": "User 1"},
        )
        response = client.post(
            "/auth/signup",
            json={"email": "dup@vexus.com", "password": "pass456", "name": "User 2"},
        )
        assert response.status_code == 400

    def test_login_success(self, setup_user):
        """Test successful login."""
        response = client.post(
            "/auth/login", json={"email": "test@vexus.com", "password": "test123"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

    def test_login_invalid_password(self, setup_user):
        """Test login with invalid password."""
        response = client.post(
            "/auth/login", json={"email": "test@vexus.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self):
        """Test login with nonexistent user."""
        response = client.post(
            "/auth/login",
            json={"email": "nonexistent@vexus.com", "password": "anypassword"},
        )
        assert response.status_code == 401


class TestUserProfile:
    def test_get_current_user(self, auth_token):
        """Test getting current user using header and cookie auth."""
        # header-based request (legacy)
        response = client.get("/me", headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        assert response.json()["email"] == "test@vexus.com"
        assert response.json()["name"] == "Test User"

        # cookie-based request should work without Authorization header
        response2 = client.get("/me")
        assert response2.status_code == 200
        assert response2.json()["email"] == "test@vexus.com"
        assert response2.json()["name"] == "Test User"

    def test_get_current_user_no_token(self):
        """Test getting current user without token or cookies."""
        # clear cookies first
        client.cookies.clear()
        response = client.get("/me")
        assert (
            response.status_code == 401
        )  # 401 Unauthorized is correct for missing auth


class TestChat:
    def test_send_message(self, auth_token):
        """Test sending a message."""
        response = client.post(
            "/chat/send",
            json={"content": "Hello", "sender": "user"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "sent"
        assert response.json()["message"]["content"] == "Hello"

    def test_get_chat_history(self, auth_token):
        """Test getting chat history."""
        # Send a message first
        client.post(
            "/chat/send",
            json={"content": "Test message", "sender": "user"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        response = client.get(
            "/chat/history", headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0


class TestKB:
    def test_upload_document(self, auth_token):
        """Test uploading document."""
        response = client.post(
            "/kb/upload?file_name=test.pdf",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "uploaded"

    def test_query_kb(self, auth_token):
        """Test querying KB."""
        response = client.post(
            "/kb/query",
            json={"query": "What are the pricing plans?", "top_k": 5},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        assert "results" in response.json()
        assert len(response.json()["results"]) > 0


class TestLeads:
    def test_get_leads(self, auth_token):
        """Test getting leads."""
        response = client.get(
            "/leads", headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert "leads" in response.json()
        assert len(response.json()["leads"]) > 0

    def test_get_lead_details(self, auth_token):
        """Test getting lead details."""
        response = client.get(
            "/leads/1", headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert response.json()["id"] == 1
        assert "score" in response.json()
        assert "stage" in response.json()


class TestProposals:
    def test_generate_proposal(self, auth_token):
        """Test generating a proposal."""
        response = client.post(
            "/proposals/generate",
            json={"lead_id": 1, "template": "basic"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        assert response.json()["lead_id"] == 1
        assert "content" in response.json()

    def test_get_proposals(self, auth_token):
        """Test getting proposals."""
        response = client.get(
            "/proposals", headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert "proposals" in response.json()


class TestAgents:
    def test_get_agents(self, auth_token):
        """Test getting agents."""
        response = client.get(
            "/agents", headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert "agents" in response.json()
        assert len(response.json()["agents"]) > 0

    def test_update_agent_config(self, auth_token):
        """Test updating agent config."""
        response = client.put(
            "/agents/1/config",
            json={
                "name": "Agente Vendas",
                "model": "GPT-4",
                "temperature": 0.7,
                "max_tokens": 2048,
                "auto_response": True,
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "atualizado"


class TestAnalytics:
    def test_get_analytics_summary(self, auth_token):
        """Test getting analytics."""
        response = client.get(
            "/analytics/summary", headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert "total_leads" in response.json()
        assert "conversion_rate" in response.json()
        assert "revenue_month" in response.json()


class TestFuzzyEndpoints:
    @pytest.fixture(scope="session")
    def fuzzy_available(self):
        # skip tests if fuzzy C library is not built
        path = os.path.join(os.path.dirname(__file__), "../c_modules/fuzzy/libfuzzy.so")
        if not os.path.exists(path):
            pytest.skip("fuzzy lib not available")
        return True

    def test_lead_score_endpoint(self, auth_token, fuzzy_available):
        response = client.post(
            "/fuzzy/lead-score",
            json={"engagement": 50.0, "likelihood": 75.0},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "score" in data and "classification" in data
        assert 0 <= data["score"] <= 100
        assert data["classification"] in ("hot", "warm", "cold")

    def test_agent_performance_endpoint(self, auth_token, fuzzy_available):
        response = client.post(
            "/fuzzy/agent-performance",
            json={"response_time": 30.0, "satisfaction": 0.8, "conversion_rate": 0.1},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert 0 <= data["score"] <= 100

    def test_appointment_priority_endpoint(self, auth_token, fuzzy_available):
        response = client.post(
            "/fuzzy/appointment-priority",
            json={"days_until": 3, "lead_score": 85.0, "cancel_history": 0},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "priority" in data
        assert 0 <= data["priority"] <= 100

    def test_metrics_dashboard_endpoint(self):
        response = client.get("/fuzzy/metrics/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "avg_score" in data
        assert "distribution" in data
        assert isinstance(data["distribution"], dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app", "--cov-report=html"])
