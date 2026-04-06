"""
🎯 ONE-CLICK INTEGRATION SYSTEM
Autorização de "um clique" para WhatsApp (QR Code), Instagram (OAuth), Telegram (Manual Rápido)
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import httpx
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════
# 🟢 1. WHATSAPP: Evolution API (QR Code - UM CLIQUE)
# ═══════════════════════════════════════════════════════════════════════

class WhatsAppQRCodeRequest(BaseModel):
    client_id: str
    instance_name: str


@router.post("/integrations/whatsapp/generate-qrcode")
async def generate_whatsapp_qrcode(req: WhatsAppQRCodeRequest):
    """
    PASSO 1: Cliente clica em "Conectar WhatsApp"
    Frontend faz POST aqui
    
    Response: URL com QR Code gerada
    
    Cliente escaneia com celular
    WhatsApp conecta
    Sistema fica "listening" no webhook
    Done! ✅
    """
    try:
        EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:3000")
        EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "seu_api_key")
        
        # 1️⃣ Chamar Evolution API para criar instância
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{EVOLUTION_API_URL}/instance/create",
                headers={"apikey": EVOLUTION_API_KEY},
                json={
                    "instanceName": req.instance_name,
                    "qrcode": True,  # Gerar QR Code
                    "token": {},
                    "webhook": {
                        "url": f"https://api.nexuscrm.tech/webhooks/whatsapp/{req.instance_name}",
                        "events": ["messages.upsert", "connection.update"]
                    }
                }
            )
            
            result = response.json()
            
            if response.status_code != 201:
                raise Exception(f"Evolution API error: {result}")
            
            # 2️⃣ Retornar QR Code URL
            qrcode_url = result.get("qrcode", {}).get("imageUrl", "")
            
            logger.info(f"✅ QR Code gerado para {req.instance_name}")
            
            return {
                "status": "pending",
                "message": "Escaneie o QR Code com seu WhatsApp",
                "qrcode_url": qrcode_url,
                "instance_name": req.instance_name,
                "instruction": "1. Aponte a câmera do seu celular para o código\n2. Escaneie com o WhatsApp\n3. Aguarde conexão (leva ~10 segundos)"
            }
    
    except Exception as e:
        logger.error(f"❌ Erro ao gerar QR Code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integrations/whatsapp/status/{instance_name}")
async def check_whatsapp_status(instance_name: str):
    """
    Frontend faz polling aqui enquanto aguarda QR Code ser scanneado
    
    GET /integrations/whatsapp/status/nexus_victor
    Response: {"status": "connected"} ou {"status": "waiting"}
    """
    try:
        EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:3000")
        EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{EVOLUTION_API_URL}/instance/connectionstate/{instance_name}",
                headers={"apikey": EVOLUTION_API_KEY}
            )
            
            result = response.json()
            connection_state = result.get("connectionState", "DISCONNECTED")
            
            return {
                "status": "connected" if connection_state == "CONNECTED" else "waiting",
                "state": connection_state,
                "message": "WhatsApp conectado!" if connection_state == "CONNECTED" else "Aguardando QR Code..."
            }
    
    except Exception as e:
        logger.error(f"❌ Erro ao verificar status: {str(e)}")
        return {"status": "error", "message": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# 🔵 2. INSTAGRAM: Facebook OAuth (UM CLIQUE)
# ═══════════════════════════════════════════════════════════════════════

@router.get("/integrations/instagram/oauth-url")
async def get_instagram_oauth_url():
    """
    Cliente clica em "Conectar Instagram"
    Frontend redireciona para aqui
    Retorna URL de login OAuth da Meta
    """
    try:
        FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
        FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
        REDIRECT_URI = os.getenv("REDIRECT_URI", "https://api.nexuscrm.tech/integrations/instagram/callback")
        
        # URL oficial do Facebook Login
        oauth_url = (
            f"https://www.facebook.com/v18.0/dialog/oauth?"
            f"client_id={FACEBOOK_APP_ID}&"
            f"redirect_uri={REDIRECT_URI}&"
            f"scopes=instagram_basic,instagram_manage_messages&"
            f"response_type=code"
        )
        
        logger.info("🔵 OAuth URL gerada para Instagram")
        
        return {
            "oauth_url": oauth_url,
            "button_text": "Conectar com Instagram",
            "instruction": "Você será redirecionado para fazer login na Meta. Autorize o acesso."
        }
    
    except Exception as e:
        logger.error(f"❌ Erro ao gerar OAuth URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integrations/facebook/oauth-url")
async def get_facebook_oauth_url():
    """
    Cliente clica em "Conectar Facebook"
    Frontend redireciona para aqui
    Retorna URL de login OAuth da Meta para Facebook Messenger
    """
    try:
        FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
        FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
        REDIRECT_URI = os.getenv("REDIRECT_URI", "https://api.nexuscrm.tech/integrations/instagram/callback")
        
        # URL oficial do Facebook Login para Messenger
        oauth_url = (
            f"https://www.facebook.com/v18.0/dialog/oauth?"
            f"client_id={FACEBOOK_APP_ID}&"
            f"redirect_uri={REDIRECT_URI}&"
            f"scopes=pages_messaging,pages_show_list,pages_manage_metadata&"
            f"response_type=code"
        )
        
        logger.info("📘 OAuth URL gerada para Facebook")
        
        return {
            "oauth_url": oauth_url,
            "button_text": "Conectar com Facebook",
            "instruction": "Você será redirecionado para fazer login na Meta. Autorize o acesso ao Messenger."
        }
    
    except Exception as e:
        logger.error(f"❌ Erro ao gerar OAuth URL para Facebook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integrations/instagram/callback")
async def instagram_oauth_callback(code: str, state: str = None):
    """
    Callback após o usuário autorizar no Facebook
    Meta redireciona aqui com 'code'
    Você troca o code por um access_token
    """
    try:
        FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
        FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
        REDIRECT_URI = os.getenv("REDIRECT_URI", "https://api.nexuscrm.tech/integrations/instagram/callback")
        
        # Trocar code por access_token
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://graph.instagram.com/v18.0/oauth/access_token",
                params={
                    "client_id": FACEBOOK_APP_ID,
                    "client_secret": FACEBOOK_APP_SECRET,
                    "grant_type": "authorization_code",
                    "redirect_uri": REDIRECT_URI,
                    "code": code
                }
            )
            
            token_result = response.json()
            access_token = token_result.get("access_token")
            user_id = token_result.get("user_id")
            
            if not access_token:
                raise Exception("Falha ao obter access token")
            
            logger.info(f"✅ Instagram conectado! User ID: {user_id}")
            
            # Aqui você armazena no banco de dados
            # db.save_integration(
            #     client_id=state,
            #     channel="instagram",
            #     access_token=access_token,
            #     user_id=user_id
            # )
            
            # Redirecionar de volta para o frontend com sucesso
            return {
                "status": "success",
                "message": "Instagram conectado com sucesso!",
                "access_token": access_token,  # NÃO retornar em produção, salvar no banco
                "user_id": user_id
            }
    
    except Exception as e:
        logger.error(f"❌ Erro no callback Instagram: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
# 🤖 3. TELEGRAM: Manual Rápido (3 PASSOS - NÃO PODE MELHORAR MUITO)
# ═══════════════════════════════════════════════════════════════════════

class TelegramBotRequest(BaseModel):
    client_id: str
    bot_token: str


@router.post("/integrations/telegram/connect")
async def connect_telegram(req: TelegramBotRequest):
    """
    Cliente cola o token do bot aqui
    
    Instruções anteriores:
    1. Abrir @BotFather no Telegram
    2. Digitar /newbot
    3. Escolher nome + username
    4. Copiar o token (123456:ABC-DEF...)
    5. Colar aqui
    
    Response: Validação e setup do webhook
    """
    try:
        TELEGRAM_API_URL = "https://api.telegram.org"
        
        # 1️⃣ Validar token
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{TELEGRAM_API_URL}/bot{req.bot_token}/getMe"
            )
            
            result = response.json()
            
            if not result.get("ok"):
                raise Exception("Token do Telegram inválido")
            
            bot_data = result.get("result", {})
            bot_name = bot_data.get("first_name")
            bot_id = bot_data.get("id")
            
            # 2️⃣ Registrar webhook
            webhook_url = f"https://api.nexuscrm.tech/webhooks/telegram/{req.client_id}"
            
            webhook_response = await client.post(
                f"{TELEGRAM_API_URL}/bot{req.bot_token}/setWebhook",
                json={"url": webhook_url}
            )
            
            webhook_result = webhook_response.json()
            
            if not webhook_result.get("ok"):
                raise Exception(f"Erro ao registrar webhook: {webhook_result}")
            
            logger.info(f"✅ Telegram conectado! Bot: {bot_name}")
            
            return {
                "status": "connected",
                "message": f"Bot {bot_name} conectado com sucesso!",
                "bot_id": bot_id,
                "bot_name": bot_name,
                "webhook_url": webhook_url
            }
    
    except Exception as e:
        logger.error(f"❌ Erro ao conectar Telegram: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
# 🎯 INTEGRATIONS OVERVIEW
# ═══════════════════════════════════════════════════════════════════════

@router.get("/integrations/status/{client_id}")
async def get_all_integrations_status(client_id: str):
    """
    Dashboard mostra status de todas as integrações
    GET /integrations/status/victor_01
    
    Response: Status de WhatsApp, Instagram, Telegram, Email
    """
    try:
        # Buscar do banco de dados
        integrations = {
            "whatsapp": {
                "status": "connected",
                "instance_name": "nexus_victor",
                "connected_at": "2026-04-03T10:30:00",
                "phone": "+55 11 987654321"
            },
            "instagram": {
                "status": "connected",
                "user_id": "987654321",
                "user_name": "victor_instagram",
                "connected_at": "2026-04-03T10:45:00"
            },
            "telegram": {
                "status": "connected",
                "bot_id": "123456789",
                "bot_name": "NexusBot",
                "connected_at": "2026-04-03T11:00:00"
            },
            "email": {
                "status": "pending",
                "message": "Não configurado ainda"
            }
        }
        
        connected_count = sum(1 for i in integrations.values() if i.get("status") == "connected")
        
        return {
            "client_id": client_id,
            "integrations": integrations,
            "connected": connected_count,
            "total": len(integrations),
            "progress": f"{connected_count}/4 canais conectados"
        }
    
    except Exception as e:
        logger.error(f"❌ Erro ao buscar status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
# 💬 SEND MESSAGE API (Usar qualquer canal)
# ═══════════════════════════════════════════════════════════════════════

class SendMessageRequest(BaseModel):
    channel: str  # "whatsapp", "telegram", "instagram", "email"
    recipient: str  # Número, chat_id, user_id, email
    message: str


@router.post("/api/send/message")
async def send_message_unified(req: SendMessageRequest):
    """
    Enviar mensagem por QUALQUER canal
    POST /api/send/message
    
    {
        "channel": "whatsapp",
        "recipient": "5511987654321",
        "message": "Olá! Sua cotação está pronta!"
    }
    """
    try:
        if req.channel == "whatsapp":
            # Chamar Evolution API
            EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL")
            EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{EVOLUTION_API_URL}/message/sendText",
                    headers={"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"},
                    json={
                        "number": req.recipient,
                        "text": req.message
                    }
                )
            
            logger.info(f"📱 WhatsApp enviado para {req.recipient}")
            return {"status": "sent", "channel": "whatsapp"}
        
        elif req.channel == "telegram":
            # Chamar Telegram API
            TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": req.recipient,
                        "text": req.message
                    }
                )
            
            logger.info(f"🤖 Telegram enviado para {req.recipient}")
            return {"status": "sent", "channel": "telegram"}
        
        elif req.channel == "instagram":
            # Chamar Meta API
            INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://graph.instagram.com/v18.0/{req.recipient}/messages",
                    headers={"Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}"},
                    json={"message": req.message}
                )
            
            logger.info(f"📸 Instagram enviado para {req.recipient}")
            return {"status": "sent", "channel": "instagram"}
        
        else:
            raise HTTPException(status_code=400, detail=f"Canal desconhecido: {req.channel}")
    
    except Exception as e:
        logger.error(f"❌ Erro ao enviar: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def create_integration_router():
    return router


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
