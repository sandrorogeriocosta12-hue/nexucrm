"""
Test Admin Dashboard APIs
Testa as funcionalidades do painel administrativo
"""

import requests
import json

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/admin"

def test_admin_dashboard():
    """Test full admin dashboard flow"""
    
    print("=" * 80)
    print("🧪 TESTE DO PAINEL ADMINISTRATIVO NEXUS CRM")
    print("=" * 80)
    
    # 1. Teste de Registro
    print("\n1️⃣  TESTANDO REGISTRO...")
    register_data = {
        "email": "admin@nexus.local",
        "password": "SecurePass123!",
        "company_name": "Nexus Company",
        "full_name": "Admin Nexus"
    }
    
    try:
        response = requests.post(f"{API_URL}/register", json=register_data)
        result = response.json()
        
        if response.status_code == 200 and result.get("success"):
            token = result["token"]
            print(f"✅ Registro bem-sucedido!")
            print(f"   Token: {token[:50]}...")
        else:
            print(f"❌ Erro no registro: {result}")
            return
    except Exception as e:
        print(f"❌ Erro ao registrar: {e}")
        return
    
    # 2. Teste de Login
    print("\n2️⃣  TESTANDO LOGIN...")
    login_data = {
        "email": "admin@nexus.local",
        "password": "SecurePass123!"
    }
    
    try:
        response = requests.post(f"{API_URL}/login", json=login_data)
        result = response.json()
        
        if response.status_code == 200 and result.get("success"):
            token = result["token"]
            print(f"✅ Login bem-sucedido!")
            print(f"   Nome: {result['user']['full_name']}")
            print(f"   Email: {result['user']['email']}")
            print(f"   Empresa: {result['user']['company_name']}")
        else:
            print(f"❌ Erro no login: {result}")
            return
    except Exception as e:
        print(f"❌ Erro ao fazer login: {e}")
        return
    
    # 3. Teste de Adicionar Tokens
    print("\n3️⃣  TESTANDO ADIÇÃO DE TOKENS...")
    tokens_data = {
        "whatsapp_token": "EAA123456789abc",
        "whatsapp_phone_id": "1234567890",
        "telegram_token": "123456:ABC-DEF",
        "sendgrid_key": "SG.sk_live_xxxx",
        "email_from": "noreply@nexus.com"
    }
    
    try:
        response = requests.post(f"{API_URL}/tokens?token={token}", json=tokens_data)
        result = response.json()
        
        if response.status_code == 200 and result.get("success"):
            print(f"✅ Tokens salvos com sucesso!")
            print(f"   Total de tokens: {result['tokens_count']}")
        else:
            print(f"❌ Erro ao salvar tokens: {result}")
    except Exception as e:
        print(f"❌ Erro ao salvar tokens: {e}")
    
    # 4. Teste de Obter Tokens (Mascarados)
    print("\n4️⃣  TESTANDO OBTENÇÃO DE TOKENS (MASCARADOS)...")
    try:
        response = requests.get(f"{API_URL}/tokens?token={token}")
        result = response.json()
        
        if response.status_code == 200:
            print(f"✅ Tokens obtidos com sucesso (mascarados)!")
            print(f"   Configurados: {result['configured']}/{result['total_channels']}")
            for key, value in result['tokens'].items():
                print(f"   {key}: {value}")
        else:
            print(f"❌ Erro ao obter tokens: {result}")
    except Exception as e:
        print(f"❌ Erro ao obter tokens: {e}")
    
    # 5. Teste de Status
    print("\n5️⃣  TESTANDO STATUS DE CONFIGURAÇÃO...")
    try:
        response = requests.get(f"{API_URL}/status?token={token}")
        result = response.json()
        
        if response.status_code == 200:
            print(f"✅ Status obtido com sucesso!")
            print(f"   Usuário: {result['user']['email']}")
            print(f"   Empresa: {result['user']['company']}")
            print(f"   Canais Configurados: {result['configured_count']}/{result['total_channels']}")
            for channel, status in result['channels'].items():
                status_text = "✅ Ativo" if status else "❌ Inativo"
                print(f"      {channel}: {status_text}")
            print(f"   APIs Status: {result['apis_status']}")
        else:
            print(f"❌ Erro ao obter status: {result}")
    except Exception as e:
        print(f"❌ Erro ao obter status: {e}")
    
    # 6. Teste de Perfil
    print("\n6️⃣  TESTANDO PERFIL DO USUÁRIO...")
    try:
        response = requests.get(f"{API_URL}/user?token={token}")
        result = response.json()
        
        if response.status_code == 200:
            print(f"✅ Perfil obtido com sucesso!")
            print(f"   Email: {result['email']}")
            print(f"   Nome: {result['full_name']}")
            print(f"   Empresa: {result['company_name']}")
            print(f"   Tokens Configurados: {result['tokens_configured']}")
            print(f"   Criado em: {result['created_at']}")
        else:
            print(f"❌ Erro ao obter perfil: {result}")
    except Exception as e:
        print(f"❌ Erro ao obter perfil: {e}")
    
    # 7. Teste de Deletar Token
    print("\n7️⃣  TESTANDO DELEÇÃO DE TOKEN...")
    try:
        response = requests.delete(f"{API_URL}/tokens/whatsapp?token={token}")
        result = response.json()
        
        if response.status_code == 200 and result.get("success"):
            print(f"✅ Token deletado com sucesso!")
            print(f"   {result['message']}")
        else:
            print(f"⚠️  Token já deletado ou não existe: {result}")
    except Exception as e:
        print(f"⚠️  Erro ao deletar token: {e}")
    
    # 8. Teste de Páginas HTML
    print("\n8️⃣  TESTANDO PÁGINAS HTML...")
    try:
        response = requests.get(f"{BASE_URL}/login")
        if response.status_code == 200 and "<html" in response.text.lower():
            print(f"✅ Página de Login carregada com sucesso!")
            print(f"   Tamanho: {len(response.text)} bytes")
        else:
            print(f"❌ Erro ao carregar página de login")
    except Exception as e:
        print(f"❌ Erro ao testar página de login: {e}")
    
    try:
        response = requests.get(f"{BASE_URL}/dashboard")
        if response.status_code == 200 and "<html" in response.text.lower():
            print(f"✅ Página de Dashboard carregada com sucesso!")
            print(f"   Tamanho: {len(response.text)} bytes")
        else:
            print(f"❌ Erro ao carregar página de dashboard")
    except Exception as e:
        print(f"❌ Erro ao testar página de dashboard: {e}")
    
    print("\n" + "=" * 80)
    print("✅ TESTES FINALIZADOS!")
    print("=" * 80)
    print("""
Endpoints de Admin:
  POST   /api/admin/register      - Registrar novo cliente
  POST   /api/admin/login         - Fazer login
  POST   /api/admin/tokens        - Adicionar/atualizar tokens
  GET    /api/admin/tokens        - Obter tokens (mascarados)
  GET    /api/admin/status        - Obter status de configuração
  GET    /api/admin/user          - Obter perfil do usuário
  DELETE /api/admin/tokens/{ch}   - Deletar token de um canal
  
Páginas HTML:
  GET /login                       - Página de login/registro
  GET /dashboard                   - Painel de controle (requer token)
    """)

if __name__ == "__main__":
    import time
    print("\n⏳ Aguardando 2 segundos para garantir que o servidor esteja pronto...")
    time.sleep(2)
    test_admin_dashboard()
