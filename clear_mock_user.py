#!/usr/bin/env python3
"""Limpar usuário da memória do mock_users"""

import sys

# Importar a app
sys.path.insert(0, '/home/victor-emanuel/PycharmProjects/Vexus Service')

from app.api_main import mock_users, clear_user_from_mock

email = "victor226942@gmail.com"

print("🗑️  LIMPANDO USUÁRIO DA MEMÓRIA")
print("=" * 60)

print(f"📊 Usuários em memória ANTES: {list(mock_users.keys())}")

# Limpar
clear_user_from_mock(email)

print(f"✅ Usuário deletado: {email}")
print(f"📊 Usuários em memória DEPOIS: {list(mock_users.keys())}")

print()
print("✨ Memória limpa! Agora você pode criar novo cadastro")
