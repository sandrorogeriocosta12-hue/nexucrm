#!/usr/bin/env python3
"""Script simples para deletar usuário"""
import subprocess
import sys

email = "victor226942@gmail.com"
db_url = "postgresql://vexus:password@localhost/vexus_crm"

print("🗑️  DELETANDO USUÁRIO:", email)
print("=" * 60)

# Comando SQL simples
sql_commands = [
    f"DELETE FROM \"user\" WHERE email = '{email}';",
    f"DELETE FROM \"users\" WHERE email = '{email}';",
    f"DELETE FROM \"account\" WHERE email = '{email}';",
    f"SELECT 'Usuário deletado' as status;",
]

try:
    from sqlalchemy import create_engine, text
    
    engine = create_engine(db_url)
    
    print("📊 Conectando ao banco...")
    with engine.connect() as conn:
        print("✅ Conectado!")
        
        # Deletar usuário
        for sql in sql_commands[:3]:  # Primeiras 3 são delete
            try:
                result = conn.execute(text(sql))
                conn.commit()
                if result.rowcount and result.rowcount > 0:
                    print(f"✅ Deletado: {result.rowcount} registro(s)")
            except Exception as e:
                if "does not exist" not in str(e):
                    print(f"⚠️  {str(e)[:50]}")
        
        print("\n✨ USUÁRIO DELETADO COM SUCESSO!")
        
except Exception as e:
    print(f"❌ Erro: {e}")
    sys.exit(1)