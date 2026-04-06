#!/usr/bin/env python3
"""Script para deletar usuário do banco de dados"""
import os
from sqlalchemy import create_engine, text

# Configuração do banco
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://vexus:password@localhost/vexus_crm")

def delete_user(email: str):
    """Delete um usuário pelo email"""
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as connection:
            # Primeiro, vamos ver quais tabelas de usuários existem
            result = connection.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%user%'
            """))
            
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 Tabelas de usuários encontradas: {tables}")
            
            if not tables:
                print("❌ Nenhuma tabela de usuários encontrada")
                return False
            
            # Tentar deletar em cada tabela possível
            deleted = False
            for table in tables:
                try:
                    # Checar se a tabela tem coluna de email
                    columns_result = connection.execute(text(f"""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = '{table}'
                    """))
                    
                    columns = [row[0] for row in columns_result.fetchall()]
                    print(f"  Colunas em '{table}': {columns}")
                    
                    # Se tem coluna 'email', tentar deletar
                    if 'email' in columns:
                        delete_result = connection.execute(text(f"""
                            DELETE FROM {table} 
                            WHERE email = :email
                        """), {"email": email})
                        
                        connection.commit()
                        
                        if delete_result.rowcount > 0:
                            print(f"✅ Usuário deletado da tabela '{table}'")
                            deleted = True
                        
                except Exception as e:
                    print(f"⚠️  Erro ao deletar de '{table}': {e}")
                    connection.rollback()
            
            if deleted:
                print(f"✅ Usuário {email} foi deletado com sucesso!")
            else:
                print(f"❌ Usuário {email} não encontrado em nenhuma tabela")
            
            return deleted
            
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        return False

if __name__ == "__main__":
    email = "victor226942@gmail.com"
    print(f"🗑️  Deletando usuário: {email}")
    print("=" * 50)
    
    delete_user(email)
