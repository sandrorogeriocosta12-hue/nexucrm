#!/usr/bin/env python3
import subprocess
import sys

email = "victor226942@gmail.com"

# SQL para executar
sql = f"""
DELETE FROM "user" WHERE email = '{email}';
DELETE FROM "users" WHERE email = '{email}';
DELETE FROM account WHERE email = '{email}';
DELETE FROM accounts WHERE email = '{email}';
SELECT 'Usuário {email} foi deletado do banco de dados' as confirmação;
"""

# Executar via psql
try:
    result = subprocess.run(
        ['sudo', '-u', 'postgres', 'psql', '-d', 'vexus_crm'],
        input=sql,
        text=True,
        capture_output=True,
        timeout=10
    )
    
    print("✅ DELETANDO USUÁRIO DO BANCO DE DADOS")
    print("=" * 60)
    print(result.stdout)
    
    if result.stderr:
        print("Avisos/Erros:")
        print(result.stderr)
    
    print("✨ OPERAÇÃO CONCLUÍDA!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    sys.exit(1)
