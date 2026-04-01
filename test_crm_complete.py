#!/usr/bin/env python3
"""
🚀 CRM TEST SUITE - Teste todos os endpoints
Execute: python3 test_crm_complete.py
"""

import requests
import json
from datetime import datetime
import time

# ═════════════════════════════════════════════════════════════════════════════
BASE_URL = "https://api.nexuscrm.tech"
# BASE_URL = "http://localhost:8000"  # Para testes locais

# ═════════════════════════════════════════════════════════════════════════════
# CORES PARA CONSOLE
# ═════════════════════════════════════════════════════════════════════════════
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(title):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def print_test(msg):
    print(f"{Colors.YELLOW}🧪 {msg}{Colors.END}")

# ═════════════════════════════════════════════════════════════════════════════
# TESTES
# ═════════════════════════════════════════════════════════════════════════════

def test_integration_status():
    """Teste Status das Integrações"""
    print_test("Verificando status dos canais...")
    
    try:
        response = requests.get(f"{BASE_URL}/integrations/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success("Integrações respondendo!")
            
            channels = data.get("channels", {})
            print(f"\n  Status dos Canais:")
            for channel, info in channels.items():
                status = "🟢 ATIVO" if info.get("configured") else "⚫ NÃO CONFIGURADO"
                print(f"    {channel.upper():15} {status}")
            
            return True
        else:
            print_error(f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Erro: {str(e)}")
        return False


def test_crm_apis():
    """Teste APIs de CRM"""
    print_header("🔄 TESTANDO CRM APIs")
    
    results = {
        "leads": False,
        "campaigns": False,
        "contacts": False
    }
    
    # Test Leads
    print_test("GET /api/leads")
    try:
        response = requests.get(f"{BASE_URL}/api/leads", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Leads API respondendo! Total: {data.get('total', 0)}")
            results["leads"] = True
        else:
            print_error(f"Leads: {response.status_code}")
    except Exception as e:
        print_error(f"Leads erro: {str(e)}")
    
    # Test Campaigns
    print_test("GET /api/campaigns")
    try:
        response = requests.get(f"{BASE_URL}/api/campaigns", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Campaigns API respondendo! Total: {data.get('total', 0)}")
            results["campaigns"] = True
        else:
            print_error(f"Campaigns: {response.status_code}")
    except Exception as e:
        print_error(f"Campaigns erro: {str(e)}")
    
    # Test Contacts
    print_test("GET /api/contacts")
    try:
        response = requests.get(f"{BASE_URL}/api/contacts", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Contacts API respondendo! Total: {data.get('total', 0)}")
            results["contacts"] = True
        else:
            print_error(f"Contacts: {response.status_code}")
    except Exception as e:
        print_error(f"Contacts erro: {str(e)}")
    
    return all(results.values())


def test_create_lead():
    """Cria um lead para teste"""
    print_header("📝 CRIANDO NOVO LEAD")
    
    payload = {
        "user_id": "test-user",
        "name": f"Lead Teste {datetime.now().strftime('%H%M%S')}",
        "email": f"test-{int(time.time())}@test.com",
        "phone": "(11) 98765-4321",
        "company": "Empresa Teste",
        "job_title": "Gerente",
        "value": 5000.00,
        "status": "novo",
        "source": "whatsapp",
        "notes": "Lead criado por teste automatizado"
    }
    
    print_test(f"POST /api/leads - {payload['name']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/leads",
            json=payload,
            timeout=5
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            lead_data = data.get("lead", data)  # Pode estar dentro de "lead" ou no root
            lead_id = lead_data.get("id")
            print_success(f"Lead criado com ID: {lead_id}")
            print(f"  Nome: {lead_data.get('name')}")
            print(f"  Email: {lead_data.get('email')}")
            print(f"  Status: {lead_data.get('status')}")
            return lead_id
        else:
            print_error(f"Status: {response.status_code}")
            print_error(f"Resposta: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Erro ao criar lead: {str(e)}")
        return None


def test_create_contact():
    """Cria um contato para teste"""
    print_header("👥 CRIANDO NOVO CONTATO")
    
    payload = {
        "user_id": "test-user",
        "name": f"Contato Teste {datetime.now().strftime('%H%M%S')}",
        "email": f"contact-{int(time.time())}@test.com",
        "phone": "(21) 99876-5432",
        "whatsapp": "5521998765432",
        "company": "Tech Solutions",
        "job_title": "Diretor",
        "preferred_channel": "whatsapp",
        "tags": ["test", "demo", "whatsapp"]
    }
    
    print_test(f"POST /api/contacts - {payload['name']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/contacts",
            json=payload,
            timeout=5
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            contact_data = data.get("contact", data)  # Pode estar dentro de "contact" ou no root
            contact_id = contact_data.get("id")
            print_success(f"Contato criado com ID: {contact_id}")
            print(f"  Nome: {contact_data.get('name')}")
            print(f"  WhatsApp: {contact_data.get('whatsapp')}")
            print(f"  Canal preferido: {contact_data.get('preferred_channel')}")
            print(f"  Tags: {contact_data.get('tags')}")
            return contact_id
        else:
            print_error(f"Status: {response.status_code}")
            print_error(f"Resposta: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Erro ao criar contato: {str(e)}")
        return None


def test_send_message():
    """Testa envio de mensagem"""
    print_header("💬 TESTANDO ENVIO DE MENSAGENS")
    
    channels_test = [
        {
            "channel": "whatsapp",
            "destination": "5511999999999",  # Número fictício
            "text": "Olá! Teste de mensagem WhatsApp do Nexus CRM"
        },
        {
            "channel": "email",
            "destination": "teste@example.com",
            "text": "Corpo do email de teste",
            "subject": "Teste Nexus CRM"
        },
        {
            "channel": "telegram",
            "destination": "123456789",
            "text": "Teste de mensagem Telegram"
        }
    ]
    
    results = {}
    
    for test in channels_test:
        print_test(f"Enviando via {test['channel'].upper()}...")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/send-message",
                json=test,
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                print_success(f"{test['channel']}: Enviado!")
                results[test['channel']] = True
            else:
                # Se retorna erro pode ser porque não está configurado ou número inválido
                data = response.json()
                error = data.get("error", data.get("detail", "Erro desconhecido"))
                if "não configurado" in error.lower() or "token" in error.lower():
                    print_info(f"{test['channel']}: Canal não configurado (esperado)")
                else:
                    print_error(f"{test['channel']}: {error}")
                results[test['channel']] = False
                
        except Exception as e:
            print_error(f"{test['channel']} erro: {str(e)}")
            results[test['channel']] = False
    
    return results


def test_create_campaign():
    """Cria uma campanha"""
    print_header("📊 CRIANDO NOVA CAMPANHA")
    
    payload = {
        "user_id": "test-user",
        "name": f"Campanha Teste {datetime.now().strftime('%H%M%S')}",
        "description": "Campanha criada por teste automatizado",
        "channel": "whatsapp",
        "budget": 10000.00,
        "target_audience": "Clientes em potencial",
        "status": "planejamento"
    }
    
    print_test(f"POST /api/campaigns - {payload['name']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/campaigns",
            json=payload,
            timeout=5
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            campaign_data = data.get("campaign", data)  # Pode estar dentro de "campaign" ou no root
            campaign_id = campaign_data.get("id")
            print_success(f"Campanha criada com ID: {campaign_id}")
            print(f"  Nome: {campaign_data.get('name')}")
            print(f"  Canal: {campaign_data.get('channel')}")
            print(f"  Budget: R$ {campaign_data.get('budget', 0):,.2f}")
            print(f"  Status: {campaign_data.get('status')}")
            return campaign_id
        else:
            print_error(f"Status: {response.status_code}")
            print_error(f"Resposta: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Erro ao criar campanha: {str(e)}")
        return None


def print_summary(test_results):
    """Imprime resumo dos testes"""
    print_header("📋 RESUMO DOS TESTES")
    
    total = len(test_results)
    passed = sum(1 for v in test_results.values() if v is True)
    failed = sum(1 for v in test_results.values() if v is False)
    
    print(f"Total de testes: {total}")
    print(f"{Colors.GREEN}Sucessos: {passed}{Colors.END}")
    print(f"{Colors.RED}Falhas: {failed}{Colors.END}")
    print(f"Taxa de sucesso: {(passed/total*100):.1f}%")
    
    print(f"\n{Colors.BOLD}Detalhes:{Colors.END}")
    for test_name, result in test_results.items():
        status = f"{Colors.GREEN}✅ OK{Colors.END}" if result else f"{Colors.RED}❌ FALHA{Colors.END}"
        print(f"  {test_name:30} {status}")


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║        🚀 NEXUS CRM - SUITE DE TESTES COMPLETA               ║")
    print("║                    v1.3.0                                     ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}\n")
    
    print_info(f"Testando: {BASE_URL}")
    
    test_results = {}
    
    # Verificar conectividade
    print_header("🔌 VERIFICANDO CONECTIVIDADE")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print_success("Servidor respondendo!")
    except Exception as e:
        print_error(f"Servidor não respondendo: {str(e)}")
        print_error("Verifique se a URL está correta ou se o servidor está online")
        exit(1)
    
    # Teste 1: Status das Integrações
    test_results["Status das Integrações"] = test_integration_status()
    time.sleep(1)
    
    # Teste 2: APIs de CRM
    test_results["CRM APIs"] = test_crm_apis()
    time.sleep(1)
    
    # Teste 3: Criar Lead
    lead_id = test_create_lead()
    test_results["Criar Lead"] = lead_id is not None
    time.sleep(1)
    
    # Teste 4: Criar Contato
    contact_id = test_create_contact()
    test_results["Criar Contato"] = contact_id is not None
    time.sleep(1)
    
    # Teste 5: Enviar Mensagens
    print_header("💬 TESTANDO ENVIO DE MENSAGENS")
    test_results["Enviar Mensagens"] = test_send_message()
    time.sleep(1)
    
    # Teste 6: Criar Campanha
    campaign_id = test_create_campaign()
    test_results["Criar Campanha"] = campaign_id is not None
    time.sleep(1)
    
    # Resumo
    print_header("✨ TESTES CONCLUÍDOS")
    print_summary(test_results)
    
    print_info("Próximos passos:")
    print("   1. Configure as credenciais (WHATSAPP_TOKEN, TELEGRAM_TOKEN, etc)")
    print("   2. Configure webhooks em cada plataforma")
    print("   3. Execute novamente para testar canais ativos")
    
    print(f"\n{Colors.BOLD}Documentação disponível em:{Colors.END}")
    print("  • CRM_API_DOCUMENTATION.txt - Todos os endpoints")
    print("  • https://api.nexuscrm.tech/docs - API Interativa Swagger")
    print(f"\n{Colors.END}")
