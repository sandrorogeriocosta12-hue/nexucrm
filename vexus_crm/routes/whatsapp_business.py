"""
WhatsApp Business API Integration
Conecta Nexus CRM ao WhatsApp Business Platform (Meta)
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import httpx
import json
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/whatsapp", tags=["WhatsApp"])

# ===== MODELOS =====

class WhatsAppConfig(BaseModel):
    """Configuração do WhatsApp Business"""
    phone_number_id: str
    business_account_id: str
    access_token: str
    webhook_verify_token: str
    
class WhatsAppMessage(BaseModel):
    """Modelo para enviar mensagens"""
    to: str  # Número com código país, ex: "5511999999999"
    message: str
    message_type: str = "text"  # text, image, document, etc

class WhatsAppWebhook(BaseModel):
    """Modelo para receber webhooks do WhatsApp"""
    entry: List[dict]

# ===== SERVIÇO WHATSAPP =====

class WhatsAppService:
    """Serviço para integração com WhatsApp Business API"""
    
    GRAPH_API_URL = "https://graph.instagram.com/v18.0"
    
    def __init__(self):
        self.config = None
        self.load_config()
    
    def load_config(self):
        """Carrega configuração do banco ou variáveis de ambiente"""
        self.config = WhatsAppConfig(
            phone_number_id=os.getenv("WHATSAPP_PHONE_ID", ""),
            business_account_id=os.getenv("WHATSAPP_BUSINESS_ID", ""),
            access_token=os.getenv("WHATSAPP_ACCESS_TOKEN", ""),
            webhook_verify_token=os.getenv("WHATSAPP_WEBHOOK_TOKEN", "")
        )
    
    async def save_config(self, config: WhatsAppConfig):
        """Salva configuração do WhatsApp"""
        self.config = config
        # TODO: Salvar em banco de dados
        logger.info(f"WhatsApp config saved for phone: {config.phone_number_id}")
    
    async def send_message(self, to: str, message: str, message_type: str = "text") -> dict:
        """
        Envia mensagem via WhatsApp Business API
        
        Args:
            to: Número com código país (ex: 5511999999999)
            message: Conteúdo da mensagem
            message_type: Tipo de mensagem (text, image, document)
        """
        if not self.config.access_token:
            raise HTTPException(status_code=401, detail="WhatsApp não configurado")
        
        url = f"{self.GRAPH_API_URL}/{self.config.phone_number_id}/messages"
        
        # Montar payload baseado no tipo
        if message_type == "text":
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {
                    "body": message
                }
            }
        elif message_type == "template":
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template",
                "template": {
                    "name": message,
                    "language": {
                        "code": "pt_BR"
                    }
                }
            }
        else:
            raise HTTPException(status_code=400, detail=f"Tipo de mensagem não suportado: {message_type}")
        
        headers = {
            "Authorization": f"Bearer {self.config.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    logger.info(f"Message sent to {to}: {data.get('messages', [{}])[0].get('id', 'unknown')}")
                    return {
                        "success": True,
                        "message_id": data.get("messages", [{}])[0].get("id"),
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    error_msg = response.text
                    logger.error(f"Failed to send message: {error_msg}")
                    raise HTTPException(status_code=response.status_code, detail=f"WhatsApp API error: {error_msg}")
        
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")
    
    async def handle_webhook(self, data: dict) -> dict:
        """
        Processa webhooks recebidos do WhatsApp
        Chamado quando recebe:
        - Mensagens de usuário
        - Confirmações de entrega
        - Mudanças de status
        """
        try:
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    
                    # Processar mensagens recebidas
                    for message in value.get("messages", []):
                        await self._process_incoming_message(message, value)
                    
                    # Processar status de entrega
                    for status in value.get("statuses", []):
                        await self._process_message_status(status)
            
            return {"success": True, "status": "Webhook processado"}
        
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _process_incoming_message(self, message: dict, context: dict):
        """Processa mensagem recebida do usuário"""
        from_number = message.get("from")
        message_id = message.get("id")
        timestamp = message.get("timestamp")
        
        message_type = message.get("type")
        
        # Extrair conteúdo baseado tipo
        if message_type == "text":
            text_content = message.get("text", {}).get("body", "")
        elif message_type == "image":
            text_content = f"[Imagem] {message.get('image', {}).get('caption', '')}"
        elif message_type == "document":
            text_content = f"[Documento] {message.get('document', {}).get('filename', '')}"
        else:
            text_content = f"[{message_type.upper()}]"
        
        sender_name = context.get("contacts", [{}])[0].get("profile", {}).get("name", from_number)
        
        logger.info(f"Message from {sender_name} ({from_number}): {text_content}")
        
        # TODO: Salvar no banco de dados
        # TODO: Integrar com AI agent para responder automaticamente
        # TODO: Criar/atualizar lead no CRM
        
        return {
            "from": from_number,
            "sender_name": sender_name,
            "message": text_content,
            "type": message_type,
            "timestamp": timestamp,
            "processed": True
        }
    
    async def _process_message_status(self, status: dict):
        """Processa mudanças de status (lido, entregue, enviado)"""
        message_id = status.get("id")
        status_type = status.get("status")  # sent, delivered, read, failed
        
        logger.info(f"Message {message_id} status: {status_type}")
        
        # TODO: Atualizar status no banco de dados

# Instância global do serviço
whatsapp_service = WhatsAppService()

# ===== ROTAS =====

@router.post("/config")
async def configure_whatsapp(config: WhatsAppConfig):
    """
    Configura credenciais do WhatsApp Business
    
    Para obter essas credenciais:
    1. Acesse https://developers.facebook.com/
    2. Crie um app do tipo WhatsApp Business
    3. Gere um access token
    4. Copie o Phone Number ID e Business Account ID
    """
    await whatsapp_service.save_config(config)
    return {
        "success": True,
        "message": "WhatsApp configurado com sucesso",
        "phone_id": config.phone_number_id
    }

@router.get("/config")
async def get_whatsapp_config():
    """Retorna configuração atual (sem token por segurança)"""
    if not whatsapp_service.config:
        raise HTTPException(status_code=404, detail="WhatsApp não configurado")
    
    return {
        "phone_number_id": whatsapp_service.config.phone_number_id,
        "business_account_id": whatsapp_service.config.business_account_id,
        "configured": bool(whatsapp_service.config.access_token)
    }

@router.post("/send")
async def send_whatsapp_message(msg: WhatsAppMessage):
    """
    Envia mensagem via WhatsApp
    
    Exemplo:
    {
        "to": "5511999999999",
        "message": "Olá! Como posso ajudar?",
        "message_type": "text"
    }
    """
    result = await whatsapp_service.send_message(
        to=msg.to,
        message=msg.message,
        message_type=msg.message_type
    )
    return result

@router.post("/webhook")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook para receber mensagens e eventos do WhatsApp
    
    Configure em: https://developers.facebook.com/
    Webhook URL: https://seu-dominio.com/api/whatsapp/webhook
    """
    body = await request.json()
    
    # Verificar webhook token
    verify_token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if verify_token == whatsapp_service.config.webhook_verify_token:
        if challenge:
            # WhatsApp enviando challenge para verificar webhook
            return int(challenge)
    
    # Processar webhook em background
    background_tasks.add_task(whatsapp_service.handle_webhook, body)
    
    return {"status": "ok"}

@router.get("/webhook")
async def whatsapp_webhook_verify(request: Request):
    """Verificação de webhook do WhatsApp (GET)"""
    verify_token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if verify_token == whatsapp_service.config.webhook_verify_token:
        return int(challenge)
    
    raise HTTPException(status_code=403, detail="Invalid verify token")

@router.post("/test")
async def test_whatsapp_connection():
    """Testa conexão com WhatsApp Business API"""
    if not whatsapp_service.config.access_token:
        return {"status": "error", "message": "WhatsApp não configurado"}
    
    try:
        # Testar enviando mensagem de teste
        result = await whatsapp_service.send_message(
            to=os.getenv("WHATSAPP_TEST_NUMBER", ""),
            message="🧪 Teste de conectividade Nexus CRM",
            message_type="text"
        )
        return {"status": "success", "message": "Conectado ao WhatsApp Business", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/template/list")
async def list_templates():
    """
    Lista templates de mensagens aprovados no WhatsApp Business
    Templates são modelos pré-aprovados para enviar mensagens sem limite de taxa
    """
    if not whatsapp_service.config.access_token:
        raise HTTPException(status_code=401, detail="WhatsApp não configurado")
    
    url = f"{whatsapp_service.GRAPH_API_URL}/{whatsapp_service.config.business_account_id}/message_templates"
    
    headers = {
        "Authorization": f"Bearer {whatsapp_service.config.access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                templates = response.json().get("data", [])
                logger.info(f"Found {len(templates)} message templates")
                return {"count": len(templates), "templates": templates}
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
    
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_whatsapp_status():
    """Retorna status atual da integração WhatsApp"""
    return {
        "configured": bool(whatsapp_service.config and whatsapp_service.config.access_token),
        "phone_number": whatsapp_service.config.phone_number_id if whatsapp_service.config else None,
        "timestamp": datetime.now().isoformat()
    }

print("✅ WhatsApp Business API router carregado com sucesso")
