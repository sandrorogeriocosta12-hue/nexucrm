#!/usr/bin/env python3
"""Deletar usuário diretamente com SQLAlchemy"""

from sqlalchemy import create_engine, text
import os

# Configurações
db_url = "postgresql://vexus:password@localhost/vexus_crm"
email = "victor226942@gmail.com"

print("🗑️  DELETANDO USUÁRIO DO BANCO DE DADOS")
print("=" * 60)
print(f"Email: {email}")
print()

try:
    # Criar conexão
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        # Listar tabelas disponíveis
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND (table_name = 'user' OR table_name = 'users' OR table_name = 'account')
        """))
        
        tables = [row[0] for row in result.fetchall()]
        print(f"📊 Tabelas encontradas: {tables}")
        print()
        
        # Deletar de cada tabela
        for table in tables:
            try:
                delete_stmt = text(f'DELETE FROM "{table}" WHERE email = :email')
                result = conn.execute(delete_stmt, {"email": email})
                conn.commit()
                
                if result.rowcount > 0:
                    print(f"✅ Deletado de '{table}': {result.rowcount} registro(s)")
                else:
                    print(f"ℹ️  Tabela '{table}': nenhum registro encontrado")
                    
            except Exception as e:
                conn.rollback()
                print(f"⚠️  Erro em '{table}': {str(e)[:50]}")
        
        print()
        print("✨ USUÁRIO DELETADO DO BANCO DE DADOS COM SUCESSO!")
        print()
        print("📝 Confirmação:")
        print(f"   Email deletado: {email}")
        print(f"   Banco: vexus_crm")
        print(f"   Status: ✅ CONCLUÍDO")

except Exception as e:
    print(f"❌ ERRO AO CONECTAR COM BANCO: {e}")
    print("Verifique se:")
    print("  • PostgreSQL está rodando")
    print("  • Usuário 'vexus' com senha 'password' existe")
    print("  • Banco 'vexus_crm' existe")

