#!/usr/bin/env python3
"""
Test script to verify all API routes used by frontend
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("TESTANDO ROTAS DA API")
print("=" * 70)

routes = [
    # Auth routes
    ("POST", "/api/auth/login", {"username": "test@test.com", "password": "test"}),
    ("POST", "/api/auth/register", {"email": "test@test.com", "password": "test", "full_name": "Test"}),
    ("POST", "/api/auth/logout", None),
    
    # Users routes (frontend calls these)
    ("GET", "/api/auth/users/settings", None),
    ("POST", "/api/auth/users/settings", {"setting": "value"}),
    ("POST", "/api/auth/users/test-whatsapp-webhook", None),
    
    # Other API routes frontend calls
    ("GET", "/api/leads", None),
    ("GET", "/api/agents/proposals", None),
    ("GET", "/api/campaigns/", None),
]

for method, path, body in routes:
    url = BASE_URL + path
    try:
        if method == "GET":
            resp = requests.get(url, timeout=2)
        elif method == "POST":
            resp = requests.post(url, json=body if body else {}, timeout=2)
        else:
            continue
        
        status = "✅" if resp.status_code < 400 else "❌"
        print(f"{status} {method:4} {path:40} → {resp.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"❌ {method:4} {path:40} → SERVER NOT RESPONDING")
    except Exception as e:
        print(f"❌ {method:4} {path:40} → {str(e)[:40]}")

print("=" * 70)
