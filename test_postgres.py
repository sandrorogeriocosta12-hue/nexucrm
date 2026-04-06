#!/usr/bin/env python3
"""Teste rápido de conexão PostgreSQL"""
import os
from sqlalchemy import create_engine, text

def test_postgres():
    try:
        # Configurar URL do PostgreSQL
        DATABASE_URL = "postgresql://vexus:password@localhost/vexus_crm"

        print("🔍 Testando conexão com PostgreSQL...")
        print(f"📍 URL: {DATABASE_URL}")

        # Criar engine
        engine = create_engine(DATABASE_URL)

        # Testar conexão
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print("✅ CONEXÃO BEM-SUCEDIDA!")
            print(f"📊 PostgreSQL Version: {version.split(' ')[1]}")
            return True

    except Exception as e:
        print(f"❌ ERRO na conexão: {e}")
        return False

if __name__ == "__main__":
    test_postgres()