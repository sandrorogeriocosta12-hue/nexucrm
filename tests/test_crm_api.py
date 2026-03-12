import os

import httpx
import pytest
from httpx import AsyncClient

from app.core.auth import create_email_verification_token
from app_server import app


# ensure clean database for each run
@pytest.fixture(autouse=True)
def clean_db():
    db_path = "vexus.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    yield


@pytest.mark.asyncio
async def test_root_and_health():
    """Verifica endpoints básicos de status"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "online"

        h = await client.get("/health")
        assert h.status_code == 200
        assert h.json().get("status") == "healthy"


@pytest.mark.asyncio
async def test_agents_list_defaults():
    """/api/agents deve retornar a configuração padrão"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.get("/api/agents")
        assert r.status_code == 200
        body = r.json()
        assert "agents" in body
        assert isinstance(body["agents"], dict)


@pytest.mark.asyncio
async def test_knowledge_query_empty():
    """Consulta knowledge sem base deve informar que não há documentos indexados"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.post(
            "/api/knowledge/query",
            params={"company_id": "test", "query": "hello"},
        )
        assert r.status_code == 200
        body = r.json()
        assert "response" in body
        assert isinstance(body["response"], str)


@pytest.mark.asyncio
async def test_auth_flow(monkeypatch):
    """Registra usuário, loga, verifica perfil e renova token"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # register
        user = {
            "email": "u1@example.com",
            "password": "Pass123!",
            "full_name": "User One",
        }
        r = await client.post("/api/auth/register", json=user)
        assert r.status_code == 201
        created = r.json()
        assert created["email"] == user["email"]
        assert "hashed_password" not in created

        # login
        r2 = await client.post(
            "/api/auth/login",
            json={"username": user["email"], "password": user["password"]},
        )
        assert r2.status_code == 200
        tokens = r2.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        access = tokens["access_token"]
        headers = {"Authorization": f"Bearer {access}"}

        # profile
        prof = await client.get("/api/auth/me", headers=headers)
        assert prof.status_code == 200
        assert prof.json()["email"] == user["email"]

        # unauthorized profile
        prof2 = await client.get("/api/auth/me")
        assert prof2.status_code == 401

        # refresh token
        r3 = await client.post(
            "/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert r3.status_code == 200
        newt = r3.json()
        assert "access_token" in newt

        # password reset flow
        forgot = await client.post(
            "/api/auth/forgot-password", json={"email": user["email"]}
        )
        assert forgot.status_code == 200
        token = forgot.json().get("reset_token")
        assert token is not None
        reset = await client.post(
            "/api/auth/reset-password",
            json={"token": token, "new_password": "NewPass456!"},
        )
        assert reset.status_code == 200

        # verify email flow
        verify_resp = await client.post(
            "/api/auth/verify-email",
            json={"token": create_email_verification_token(user["email"])},
        )
        assert verify_resp.status_code == 200
        resend = await client.post(
            "/api/auth/resend-verification", json={"email": user["email"]}
        )
        assert resend.status_code == 200
        assert "token" in resend.json()

        # access protected endpoint using the full auth path
        prof3 = await client.get("/api/auth/users/profile", headers=headers)
        assert prof3.status_code == 200
        assert prof3.json()["email"] == user["email"]

        # update settings (name & email)
        new_data = {"name": "Renamed", "email": "renamed@example.com"}
        upd = await client.put(
            "/api/auth/users/settings", headers=headers, json=new_data
        )
        assert upd.status_code == 200
        assert upd.json()["email"] == new_data["email"]
        assert upd.json()["name"] == new_data["name"]

        # verify profile reflects changes - old token should now be invalid because email changed
        prof4 = await client.get("/api/auth/me", headers=headers)
        assert prof4.status_code == 401

        # login again using updated email to get a valid token
        # password was reset earlier
        r_login2 = await client.post(
            "/api/auth/login",
            json={"username": new_data["email"], "password": "NewPass456!"},
        )
        assert r_login2.status_code == 200
        tokens2 = r_login2.json()
        headers2 = {"Authorization": f"Bearer {tokens2['access_token']}"}
        prof5 = await client.get("/api/auth/me", headers=headers2)
        assert prof5.status_code == 200
        assert prof5.json()["email"] == new_data["email"]
        assert prof5.json()["name"] == new_data["name"]

        # now add some other fields (whatsapp webhook) and persist again with valid token
        extra = {
            "whatsapp_api_key": "KEY123",
            "whatsapp_phone_id": "PHID",
            "webhook_url": "https://hooks.example.com/wh",
        }
        upd2 = await client.put(
            "/api/auth/users/settings", headers=headers2, json=extra
        )
        assert upd2.status_code == 200

        # fetch settings explicitly and ensure values exist
        get_settings = await client.get("/api/auth/users/settings", headers=headers2)
        assert get_settings.status_code == 200
        settings_json = get_settings.json()
        assert settings_json.get("name") == new_data["name"]
        assert settings_json.get("email") == new_data["email"]
        assert settings_json.get("whatsapp_api_key") == "KEY123"
        assert settings_json.get("webhook_url") == "https://hooks.example.com/wh"

        # exercise webhook-test endpoint by substituting auth module's httpx
        # with a minimal stub so the test client itself is unaffected.
        import types

        import vexus_crm.routes.auth as auth_mod

        class DummyResp:
            status_code = 200
            text = "ok"

        class DummyClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                pass

            async def post(self, url, *args, **kwargs):
                return DummyResp()

        dummy_httpx = types.SimpleNamespace(AsyncClient=DummyClient)
        monkeypatch.setattr(auth_mod, "httpx", dummy_httpx)

        resp = await client.post(
            "/api/auth/users/test-whatsapp-webhook",
            headers=headers2,
            json={"url": "https://example.com/foo"},
        )
        assert resp.status_code == 200
        assert resp.json()["status_code"] == 200

        # login again using updated email to get a valid token
        # password was reset earlier
        r_login2 = await client.post(
            "/api/auth/login",
            json={"username": new_data["email"], "password": "NewPass456!"},
        )
        assert r_login2.status_code == 200
        tokens2 = r_login2.json()
        headers2 = {"Authorization": f"Bearer {tokens2['access_token']}"}
        prof5 = await client.get("/api/auth/me", headers=headers2)
        assert prof5.status_code == 200
        assert prof5.json()["email"] == new_data["email"]
        assert prof5.json()["name"] == new_data["name"]


@pytest.mark.asyncio
async def test_leads_and_campaigns():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # create a lead
        lead_data = {"email": "lead1@example.com", "full_name": "Lead One"}
        r = await client.post("/api/leads/", json=lead_data)
        assert r.status_code == 201
        lead = r.json()
        lead_id = lead["id"]

        # fetch lead
        r2 = await client.get(f"/api/leads/{lead_id}")
        assert r2.status_code == 200
        assert r2.json()["email"] == lead_data["email"]

        # update lead
        r3 = await client.put(f"/api/leads/{lead_id}", json={"status": "contacted"})
        assert r3.status_code == 200
        assert r3.json()["status"] == "contacted"

        # delete lead
        r4 = await client.delete(f"/api/leads/{lead_id}")
        assert r4.status_code == 204

        # campaigns
        cam = {"name": "Campaign One"}
        r5 = await client.post("/api/campaigns/", json=cam)
        assert r5.status_code == 201
        cam_id = r5.json()["id"]

        r6 = await client.get(f"/api/campaigns/{cam_id}")
        assert r6.status_code == 200
        assert r6.json()["name"] == cam["name"]

        r7 = await client.put(f"/api/campaigns/{cam_id}", json={"name": "Updated"})
        assert r7.status_code == 200
        assert r7.json()["name"] == "Updated"

        r8 = await client.delete(f"/api/campaigns/{cam_id}")
        assert r8.status_code == 204
