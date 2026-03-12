import requests
import pytest

pytest.skip("legacy script disabled", allow_module_level=True)
import sys

BASE_URL = "http://localhost:5000"  # servidor de desenvolvimento do Flask
API = BASE_URL + "/api"

endpoints = [
    ("POST", "/auth/forgot-password", {"email": "teste@example.com"}),
    (
        "POST",
        "/auth/reset-password",
        {"token": "fake-token", "new_password": "SenhaForte123"},
    ),
    ("GET", "/billing/subscription", None),
    ("GET", "/auth/me", None),
]

session = requests.Session()

for method, path, data in endpoints:
    url = API + path
    try:
        if method == "GET":
            r = session.get(url)
        elif method == "POST":
            r = session.post(url, json=data)
        elif method == "DELETE":
            r = session.delete(url)
        else:
            continue
    except Exception as e:
        print(f"Erro ao conectar {method} {path}: {e}")
        sys.exit(1)

    print(f"{method} {path} -> {r.status_code}")
    if r.status_code >= 500:
        print("Erro servidor:", r.text)
        sys.exit(1)

print("Teste concluído (verifique códigos de status para endpoints autenticados).")
