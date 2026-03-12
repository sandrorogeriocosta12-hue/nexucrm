#!/usr/bin/env python3
"""Script rápido para verificar os endpoints principais do Vexus CRM usando TestClient.
Salva saída no stdout com status de cada endpoint.
"""
import sys
import json
from pprint import pprint

from fastapi.testclient import TestClient

try:
    from vexus_crm import main
except Exception as e:
    print("Failed to import vexus_crm.main:", e)
    sys.exit(2)


app = main.app
client = TestClient(app)

checks = []


def check_get(path):
    try:
        r = client.get(path)
        ok = r.status_code < 400
        print(f"GET {path} -> {r.status_code}")
        if r.text:
            print(r.text[:400])
        return ok, r
    except Exception as e:
        print(f"GET {path} ERROR:", e)
        return False, None


def check_post(path, payload):
    try:
        r = client.post(path, json=payload)
        ok = r.status_code < 400
        print(f"POST {path} -> {r.status_code}")
        if r.text:
            print(r.text[:400])
        return ok, r
    except Exception as e:
        print(f"POST {path} ERROR:", e)
        return False, None


def main_check():
    results = []

    # GET health and stats
    results.append(("GET /health",) + check_get("/health"))
    results.append(("GET /api/stats",) + check_get("/api/stats"))

    # Agents endpoints
    results.append(("GET /api/agents",) + check_get("/api/agents"))
    results.append(("GET /api/config/agents",) + check_get("/api/config/agents"))
    results.append(("GET /api/config/channels",) + check_get("/api/config/channels"))
    results.append(
        ("GET /api/config/integrations",) + check_get("/api/config/integrations")
    )

    # POST score lead
    lead_payload = {
        "name": "Teste API",
        "email": "teste@example.com",
        "phone": "+5511999999999",
        "company": "ACME",
        "interest": "quero saber preço",
        "budget": 1000.0,
        "source": "api-test",
    }
    results.append(
        ("POST /api/agents/score-lead",)
        + check_post("/api/agents/score-lead", lead_payload)
    )

    # POST analyze conversation
    conv_payload = {"text": "Olá, quero contratar"}
    results.append(
        ("POST /api/agents/analyze-conversation",)
        + check_post("/api/agents/analyze-conversation", conv_payload)
    )

    # Flows create
    flow_payload = {"name": "Flow Test", "channel": "website", "description": "teste"}
    results.append(
        ("POST /api/flows/create",) + check_post("/api/flows/create", flow_payload)
    )

    # Pipelines
    pipeline_payload = {"name": "Pipeline Test", "description": "teste"}
    results.append(
        ("POST /api/pipelines/create",)
        + check_post("/api/pipelines/create", pipeline_payload)
    )

    # Send message (using website channel which should be present)
    msg_payload = {
        "channel": "website",
        "recipient": "test",
        "content": "Hello from API test",
        "metadata": {},
    }
    results.append(
        ("POST /api/messages/send",) + check_post("/api/messages/send", msg_payload)
    )

    # List channels via main channels endpoint
    results.append(("GET /api/channels",) + check_get("/api/channels"))

    # Summarize
    ok_count = sum(1 for r in results if r[2] and r[2].status_code < 400)
    total = len(results)
    print("\nSUMMARY:")
    print(f"{ok_count}/{total} endpoints OK")
    for name, ok, resp in results:
        status = resp.status_code if resp else "ERROR"
        print(f"- {name}: {status}")

    # Exit code non-zero if any failed
    if ok_count != total:
        sys.exit(1)
    print("All checks passed")


if __name__ == "__main__":
    main_check()
