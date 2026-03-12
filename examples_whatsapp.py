"""
Exemplo de uso da integração WhatsApp Business
Para testar localmente antes de configurar em produção
"""

import asyncio
import httpx
from vexus_crm.routes.whatsapp_business import whatsapp_service, WhatsAppConfig, WhatsAppMessage

# ===== EXEMPLO 1: Configurar WhatsApp BusinessAPAI =====

async def example_configure():
    """Exemplo de como configurar o WhatsApp"""
    
    config = WhatsAppConfig(
        phone_number_id="1234567890",  # Seu Phone Number ID
        business_account_id="987654321",  # Seu Business Account ID
        access_token="EAA...seu_token_aqui",  # Seu Access Token do Meta
        webhook_verify_token="seu_webhook_token_aleatorio"
    )
    
    await whatsapp_service.save_config(config)
    print("✅ WhatsApp configurado!")

# ===== EXEMPLO 2: Enviar Mensagem =====

async def example_send_message():
    """Exemplo de como enviar uma mensagem"""
    
    msg = WhatsAppMessage(
        to="5511999999999",  # Número com código país
        message="Olá! Esta é uma mensagem de teste do Nexus CRM",
        message_type="text"
    )
    
    result = await whatsapp_service.send_message(
        to=msg.to,
        message=msg.message,
        message_type=msg.message_type
    )
    
    print(f"✅ Mensagem enviada: {result}")

# ===== EXEMPLO 3: Processar Webhook (receber mensagens) =====

async def example_handle_webhook():
    """Exemplo de webhook recebido do WhatsApp"""
    
    # Este é um payload típico que o WhatsApp envia
    webhook_payload = {
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "5511987654321",
                                "phone_number_id": "123456789"
                            },
                            "contacts": [
                                {
                                    "profile": {
                                        "name": "João Silva"
                                    },
                                    "wa_id": "5511999999999"
                                }
                            ],
                            "messages": [
                                {
                                    "from": "5511999999999",
                                    "id": "wamid.xxx",
                                    "timestamp": "1234567890",
                                    "type": "text",
                                    "text": {
                                        "body": "Olá, recebi sua mensagem!"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    
    result = await whatsapp_service.handle_webhook(webhook_payload)
    print(f"✅ Webhook processado: {result}")

# ===== EXEMPLO 4: Listar Templates de Mensagens =====

async def example_list_templates():
    """Lista templates pré-aprovados para enviar em massa"""
    
    # Os templates são modelos de mensagem que você cria e aprova
    # Eles não têm limite de taxa (rate limiting)
    # Útil para confirmações, lembretes, etc.
    
    from app_server import app  # Sua app FastAPI
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    response = client.get("/api/whatsapp/template/list")
    
    if response.status_code == 200:
        templates = response.json()
        print(f"✅ Encontrados {templates['count']} templates:")
        for template in templates['templates']:
            print(f"  - {template.get('name')}")

# ===== EXEMPLO 5: Integrar com CRM (Leads) =====

async def example_integrate_with_crm():
    """
    Quando uma mensagem é recebida, criar automaticamente um lead no CRM
    """
    
    # Dados extraídos da mensagem WhatsApp
    contact_data = {
        "name": "João Silva",
        "phone": "5511999999999",
        "source": "whatsapp",
        "first_message": "Olá, gostaria de saber mais sobre seus produtos"
    }
    
    # TODO: Integrar com vexus_crm.routes.leads
    # await leads_router.create_lead(contact_data)
    
    print(f"✅ Lead criado: {contact_data['name']}")

# ===== COMO USAR =====

"""
1. CONFIGURAR EM DESENVOLVIMENTO:
   
   # Terminal 1: Configure as variáveis de ambiente
   export WHATSAPP_PHONE_ID="seu_phone_id"
   export WHATSAPP_BUSINESS_ID="seu_business_id"  
   export WHATSAPP_ACCESS_TOKEN="seu_token"
   export WHATSAPP_WEBHOOK_TOKEN="seu_token_aleatorio"
   
   # Terminal 2: Inicie o servidor
   python app_server.py
   
   # Terminal 3: Execute este script
   python examples_whatsapp.py

2. CONFIGURE NO FRONTEND:
   
   - Abra http://localhost:8000/frontend/app.html
   - Acesse Configurações > WhatsApp Business API
   - Preencha: Phone ID, Business ID, Access Token
   - Clique "Testar Conexão"
   - Se passar, salve a configuração

3. RECEBER MENSAGENS:
   
   - Configure o webhook em: https://developers.facebook.com/
   - Apps → Seu App → WhatsApp → Webhooks
   - Callback URL: https://seu-dominio.com/api/whatsapp/webhook
   - Verify Token: o mesmo que configurou
   - Subscribe aos eventos: messages, message_template_status_update

4. ENVIAR PRIMEIRA MENSAGEM:
   
   - No frontend, clique: "Configurações > WhatsApp > Enviar Mensagem"
   - Insira número (com código país: 5511999999999)
   - Digite sua mensagem
   - Clique "Enviar"

5. RECEBER RESPOSTAS:
   
   - Quando alguém responder no WhatsApp
   - Aparecerá em: "Configurações > WhatsApp > Últimas Mensagens"
   - Será sincronizado com CRM Lead List automaticamente
"""

# Para rodar manualmente:
if __name__ == "__main__":
    # Descomente o exemplo que quer testar:
    
    # asyncio.run(example_configure())
    # asyncio.run(example_send_message())
    # asyncio.run(example_handle_webhook())
    
    print("📚 Exemplos de integração WhatsApp disponíveis acima")
    print("⚠️ Configure seu app WhatsApp no Meta antes!")
