#!/usr/bin/env python3
"""
Script de migração para adicionar colunas faltantes na tabela de mensagens
Usa ALTER TABLE para adicionar colunas sem perder dados existentes
"""

import os
import sys
from sqlalchemy import inspect, text, Column, String, Boolean, DateTime, Integer, JSON, ForeignKey
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def migrate_messages_table():
    """Migrar tabela de mensagens adicionando colunas necessárias"""
    
    from vexus_crm.database import engine, SessionLocal
    from vexus_crm.models import Base, Message
    
    print("=" * 70)
    print("🔧 MIGRAÇÃO: Corrigindo tabela de mensagens")
    print("=" * 70)
    
    # Inspecionar banco atual
    inspector = inspect(engine)
    
    # Verificar se tabela existe
    if 'messages' not in inspector.get_table_names():
        print("❌ Tabela 'messages' não existe!")
        print("   Criando tabelas do zero...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas criadas com sucesso!")
        return True
    
    # Pegar colunas existentes
    existing_columns = [col['name'] for col in inspector.get_columns('messages')]
    print(f"\n📋 Colunas existentes ({len(existing_columns)}):")
    for col in sorted(existing_columns):
        print(f"   ✓ {col}")
    
    # Colunas que precisam existir
    required_columns = {
        'user_id': 'VARCHAR',
        'contact_id': 'VARCHAR',
        'message_text': 'VARCHAR',
        'is_read': 'BOOLEAN',
        'external_message_id': 'VARCHAR',
        'ai_processed': 'BOOLEAN',
        'ai_intent': 'VARCHAR',
        'ai_sentiment': 'VARCHAR',
        'ai_entities': 'JSON',
    }
    
    # Verificar quais colunas estão faltando
    missing_columns = {col: type_ for col, type_ in required_columns.items() 
                      if col not in existing_columns}
    
    if not missing_columns:
        print("\n✅ Todas as colunas necessárias existem!")
        return True
    
    print(f"\n⚠️  Colunas faltando ({len(missing_columns)}):")
    for col, type_ in missing_columns.items():
        print(f"   • {col} ({type_})")
    
    # Adicionar colunas faltantes
    print("\n🔄 Adicionando colunas...")
    
    db_url = os.getenv('DATABASE_URL', 'sqlite:///vexus.db')
    is_sqlite = 'sqlite' in db_url
    is_postgres = 'postgres' in db_url
    
    try:
        with engine.connect() as conn:
            for col_name, col_type in missing_columns.items():
                try:
                    if is_sqlite:
                        # SQLite usar ALTER TABLE simples
                        if col_type == 'BOOLEAN':
                            sql = f'ALTER TABLE messages ADD COLUMN {col_name} INTEGER DEFAULT 0'
                        elif col_type == 'JSON':
                            sql = f'ALTER TABLE messages ADD COLUMN {col_name} TEXT'
                        else:
                            sql = f'ALTER TABLE messages ADD COLUMN {col_name} VARCHAR'
                    elif is_postgres:
                        # PostgreSQL usar ALTER TABLE com tipos corretos
                        if col_type == 'BOOLEAN':
                            sql = f'ALTER TABLE messages ADD COLUMN {col_name} BOOLEAN DEFAULT false'
                        elif col_type == 'JSON':
                            sql = f'ALTER TABLE messages ADD COLUMN {col_name} JSONB'
                        else:
                            sql = f'ALTER TABLE messages ADD COLUMN {col_name} VARCHAR'
                    else:
                        # Fallback para outros bancos
                        sql = f'ALTER TABLE messages ADD COLUMN {col_name} VARCHAR'
                    
                    print(f"   → Adicionando {col_name}...", end="")
                    conn.execute(text(sql))
                    conn.commit()
                    print(" ✅")
                    
                except Exception as e:
                    error_str = str(e).lower()
                    if 'already exists' in error_str or 'duplicate' in error_str:
                        print(f" ⚠️  (já existe)")
                    else:
                        print(f" ❌ {str(e)[:50]}")
        
        print("\n✅ Migração concluída!")
        
        # Verificar resultado
        inspector = inspect(engine)
        final_columns = [col['name'] for col in inspector.get_columns('messages')]
        print(f"\n📊 Status final: {len(final_columns)} colunas")
        
        # Validar colunas críticas
        critical = ['user_id', 'contact_id', 'message_text', 'is_read', 'external_message_id']
        all_ok = all(col in final_columns for col in critical)
        
        if all_ok:
            print("   ✅ Todas as colunas críticas presentes!")
            return True
        else:
            missing = [col for col in critical if col not in final_columns]
            print(f"   ❌ Ainda faltam: {', '.join(missing)}")
            return False
        
    except Exception as e:
        print(f"\n❌ Erro durante migração: {e}")
        return False


def reset_database():
    """Opção para resetar banco completamente (perder dados)"""
    from vexus_crm.database import engine
    from vexus_crm.models import Base
    
    print("\n" + "=" * 70)
    print("⚠️  AVISO: Isso vai deletar TODOS os dados do banco!")
    print("=" * 70)
    confirm = input("Tem certeza? (s/n): ").lower().strip()
    
    if confirm == 's':
        print("🗑️  Deletando tabelas...")
        Base.metadata.drop_all(bind=engine)
        print("🆕 Criando tabelas novas...")
        Base.metadata.create_all(bind=engine)
        print("✅ Banco resetado com sucesso!")
        return True
    else:
        print("❌ Operação cancelada")
        return False


if __name__ == "__main__":
    print("\n🚀 Sistema de Migração - Correção de Schema\n")
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--reset':
            reset_database()
        elif sys.argv[1] == '--help':
            print("""
Uso: python migrate_fix_messages_table.py [opção]

Opções:
  (nenhuma)  - Migrar tabelas adicionando colunas faltando
  --reset    - Resetar banco completamente (PERDER DADOS)
  --help     - Mostrar esta ajuda
            """)
        else:
            print(f"Opção desconhecida: {sys.argv[1]}\n")
            migrate_messages_table()
    else:
        migrate_messages_table()
