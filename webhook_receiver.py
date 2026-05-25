"""
🎯 WEBHOOK LISTENER SYSTEM - Nexus CRM
Recebe mensagens em tempo real de 4 canais e processa automaticamente
"""

from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any, Optional
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════
# 📱 WEBHOOK: WhatsApp (Evolution API)
# ═══════════════════════════════════════════════════════════════════════

@router.post("/webhooks/whatsapp/{instance_name}")
async def webhook_whatsapp(instance_name: str, request: Request):
    """
    WhatsApp Webhook - Escuta mensagens da Evolution API
    
    URL: https://api.nexuscrm.tech/webhooks/whatsapp/{instance_name}
    
    Example payload:
    {
        "event": "messages.upsert",
        "data": {
            "instanceName": "nexus_victor",
            "messages": [{
                "key": {...},
                "messageTimestamp": 1680000000,
                "pushName": "Victor",
                "from": "5511987654321",
                "senderId": "5511987654321",
                "text": "Olá, preciso de informações sobre o seu produto",
                "type": "text"
            }]
        }
    }
    """
    try:
        payload = await request.json()
        
        # Extrair informações da mensagem
        if payload.get("event") == "messages.upsert":
            messages = payload.get("data", {}).get("messages", [])
            
            for msg in messages:
                # Verificar se é mensagem recebida (não enviada)
                if msg.get("key", {}).get("fromMe"):
                    continue
                
                message_data = {
                    "channel": "whatsapp",
                    "instance_name": instance_name,
                    "sender": msg.get("from", ""),
                    "sender_name": msg.get("pushName", "Unknown"),
                    "message_text": msg.get("text", ""),
                    "message_type": msg.get("type", "text"),
                    "timestamp": msg.get("messageTimestamp"),
                    "received_at": datetime.now().isoformat(),
                }
                
                logger.info(f"🟢 WhatsApp recebido: {message_data}")
                
                # PROCESSAR: Passar para AI + Database
                await process_incoming_message(message_data)
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"❌ Erro webhook WhatsApp: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
# 🤖 WEBHOOK: Telegram Bot
# ═══════════════════════════════════════════════════════════════════════

@router.post("/webhooks/telegram/{chat_id}")
async def webhook_telegram(chat_id: str, request: Request):
    """
    Telegram Webhook - Escuta updates do bot
    
    URL: https://api.nexuscrm.tech/webhooks/telegram/{chat_id}
    
    Example payload (Telegram setWebhook retorna este formato):
    {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "date": 1680000000,
            "chat": {
                "id": 12345678,
                "first_name": "Victor",
                "type": "private"
            },
            "text": "Olá, preciso de uma cotação"
        }
    }
    """
    try:
        payload = await request.json()
        
        if "message" in payload:
            msg = payload["message"]
            
            # Ignorar se for comando
            if msg.get("text", "").startswith("/"):
                return {"status": "command_ignored"}
            
            message_data = {
                "channel": "telegram",
                "chat_id": chat_id,
                "sender": str(msg.get("chat", {}).get("id", "")),
                "sender_name": msg.get("chat", {}).get("first_name", "Unknown"),
                "message_text": msg.get("text", ""),
                "message_type": "text",
                "timestamp": msg.get("date"),
                "received_at": datetime.now().isoformat(),
            }
            
            logger.info(f"🤖 Telegram recebido: {message_data}")
            
            # PROCESSAR: Passar para AI + Database
            await process_incoming_message(message_data)
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"❌ Erro webhook Telegram: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
# 📸 WEBHOOK: Instagram (Meta Webhooks)
# ═══════════════════════════════════════════════════════════════════════

@router.post("/webhooks/instagram")
async def webhook_instagram_meta(request: Request):
    """
    Instagram Webhook - Meta oficial
    
    Registrar em: Facebook App > Webhooks
    Callback URL: https://api.nexuscrm.tech/webhooks/instagram
    Verify Token: seu_token_de_verificacao
    
    Meta envia payloads assim:
    {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "1234567890",
                        "id": "m_message_id",
                        "timestamp": "1680000000",
                        "text": "Olá, quero saber sobre preços"
                    }]
                }
            }]
        }]
    }
    """
    try:
        payload = await request.json()
        
        # Meta usa estrutura "entry > changes > value > messages"
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                messages = change.get("value", {}).get("messages", [])
                
                for msg in messages:
                    message_data = {
                        "channel": "instagram",
                        "sender": msg.get("from", ""),
                        "sender_name": msg.get("from", "Unknown"),  # Instagram não retorna nome
                        "message_text": msg.get("text", ""),
                        "message_type": "text",
                        "timestamp": msg.get("timestamp"),
                        "received_at": datetime.now().isoformat(),
                    }
                    
                    logger.info(f"📸 Instagram recebido: {message_data}")
                    
                    # PROCESSAR: Passar para AI + Database
                    await process_incoming_message(message_data)
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"❌ Erro webhook Instagram: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
# 📧 WEBHOOK: Email (SendGrid)
# ═══════════════════════════════════════════════════════════════════════

@router.post("/webhooks/email")
async def webhook_email_sendgrid(request: Request):
    """
    Email Webhook - SendGrid
    
    Registrar em: https://app.sendgrid.com > Settings > Mail Send
    URL: https://api.nexuscrm.tech/webhooks/email
    
    SendGrid envia payload assim:
    {
        "event": "processed",
        "email": "cliente@example.com",
        "timestamp": 1680000000,
        "subject": "Cotação solicitada"
    }
    
    NOTA: SendGrid normalmente envia como x-www-form-urlencoded
    """
    try:
        # Tentar JSON primeiro
        try:
            payload = await request.json()
        except:
            # Se não for JSON, tentar form-data (padrão SendGrid)
            payload = await request.form()
            payload = dict(payload)
        
        message_data = {
            "channel": "email",
            "sender": payload.get("email", ""),
            "sender_name": payload.get("email", "Unknown"),
            "message_text": payload.get("subject", ""),
            "message_type": "email",
            "timestamp": payload.get("timestamp"),
            "received_at": datetime.now().isoformat(),
            "raw_payload": payload,
        }
        
        logger.info(f"📧 Email recebido: {message_data}")
        
        # PROCESSAR: Passar para AI + Database
        await process_incoming_message(message_data)
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"❌ Erro webhook Email: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
# 🧠 PROCESSAMENTO CENTRAL (AI + Banco de Dados)
# ═══════════════════════════════════════════════════════════════════════

async def process_incoming_message(message_data: Dict[str, Any]):
    """Processa mensagem de qualquer canal.

    Objetivo (agora):
    - Persistir a mensagem no banco (sem quebrar o webhook)
    - Rodar um score de IA (mock) para registro/log
    - Retornar sempre sucesso HTTP para o provedor, mesmo se IA/DB falharem
    """
    from vexus_crm.database import get_db
    from vexus_crm.models import Message

    ai_score: float = 0.0
    try:
        logger.info(f"⚙️  Processando mensagem: {message_data}")

        channel = message_data.get("channel")
        sender = message_data.get("sender")
        message_text = message_data.get("message_text", "")
        received_at = message_data.get("received_at")

        # Contact/Lead: se não existir, gravamos contact_id como sender
        contact_id = sender or "unknown"
        user_id = "system"

        # Persistir no banco
        # IMPORTANTE: get_db() retorna um generator, então usamos next()
        db_gen = get_db()
        db = next(db_gen)
        try:
            msg_obj = Message(
                user_id=user_id,
                contact_id=contact_id,
                channel=str(channel),
                direction="incoming",
                message_text=message_text,
                external_message_id=message_data.get("external_message_id"),
            )
            db.add(msg_obj)
            db.commit()
            logger.info(f"✅ Mensagem salva no banco (id={msg_obj.id})")
        finally:
            # fecha generator
            try:
                next(db_gen)
            except StopIteration:
                pass

        # IA (mock)
        ai_score = await get_ai_prediction(message_data)
        logger.info(f"🧠 Score AI: {ai_score}")

        # Não dispara resposta real por enquanto (conforme solicitado)
        # if ai_score > 0.8:
        #     await send_auto_response(...)

        return {"processed": True, "score": ai_score}

    except Exception as e:
        # Não deixar o webhook quebrar
        logger.exception(f"❌ Erro ao processar webhook (não deve causar 500): {str(e)}")
        return {"processed": False, "score": ai_score, "error": str(e)}


async def get_ai_prediction(message_data: Dict[str, Any]) -> float:
    """
    Chama AI Engine para fazer predição
    Retorna score 0-100
    """
    try:
        # MOCK: Simular predição
        # Em produção, chamar NexusLearningEngine.predict()
        
        text = message_data.get("message_text", "")
        
        # Features simples para demo
        engagement_score = len(text) / 100  # Mais texto = mais engajado
        
        # Palavras-chave para intenção
        intent_keywords = ["comprar", "preço", "cotação", "informação", "contrato"]
        intention_score = 0.5
        if any(kw in text.lower() for kw in intent_keywords):
            intention_score = 0.8
        
        # Score final
        final_score = (engagement_score * 0.3 + intention_score * 0.7) * 100
        return min(final_score, 100)
    
    except Exception as e:
        logger.error(f"❌ Erro AI: {str(e)}")
        return 50  # Default


async def send_auto_response(channel: str, sender: str, ai_score: float):
    """
    Envia resposta automática para leads qualificados
    """
    try:
        if channel == "whatsapp":
            # Chamar Evolution API
            response_text = f"Olá! 👋 Recebemos sua mensagem e já estamos analisando. Um de nossos especialistas entrará em contato em breve!"
            # POST /api/send/whatsapp/{instance_name}
            logger.info(f"📱 Enviando WhatsApp para {sender}")
        
        elif channel == "telegram":
            # Chamar Telegram API
            response_text = "Obrigado pelo contato! Responderemos em breve."
            # POST /api/send/telegram/{chat_id}
            logger.info(f"🤖 Enviando Telegram para {sender}")
        
        elif channel == "instagram":
            # Chamar Meta API
            response_text = "Muito obrigado! Vamos responder em quelques minutos."
            # POST /api/send/instagram/{user_id}
            logger.info(f"📸 Enviando Instagram para {sender}")
        
        elif channel == "email":
            # Chamar SendGrid
            response_text = "Recebemos seu email. Obrigado!"
            # POST /api/send/email/{email}
            logger.info(f"📧 Enviando Email para {sender}")
    
    except Exception as e:
        logger.error(f"❌ Erro ao enviar resposta: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════
# 🔐 WEBHOOK VERIFICATION (Para Meta e outros)
# ═══════════════════════════════════════════════════════════════════════

@router.get("/webhooks/instagram")
async def verify_webhook_instagram(request: Request):
    """
    GET request usado por Meta para verificar que o webhook é legítimo
    
    Meta faz:
    GET https://api.nexuscrm.tech/webhooks/instagram?
        hub.mode=subscribe&
        hub.challenge=YOUR_CHALLENGE_TOKEN&
        hub.verify_token=YOUR_VERIFY_TOKEN
    
    Você deve retornar o hub.challenge
    """
    try:
        mode = request.query_params.get("hub.mode")
        challenge = request.query_params.get("hub.challenge")
        verify_token = request.query_params.get("hub.verify_token")
        
        # Comparar token (armazenar em .env)
        INSTAGRAM_VERIFY_TOKEN = "seu_verify_token_aqui"
        
        if mode == "subscribe" and verify_token == INSTAGRAM_VERIFY_TOKEN:
            logger.info("✅ Webhook Instagram verificado pela Meta")
            return int(challenge)
        else:
            logger.warning("❌ Token de verificação inválido")
            raise HTTPException(status_code=403, detail="Invalid token")
    
    except Exception as e:
        logger.error(f"❌ Erro na verificação: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
# 📊 MONITOR: Ver todos os webhooks em tempo real
# ═══════════════════════════════════════════════════════════════════════

webhook_log = []  # Histórico simples (em produção, usar DB)

@router.post("/api/webhooks/log")
async def log_webhook_event(event: Dict[str, Any]):
    """
    Endpoint para logar todos os eventos de webhook
    Útil para debugar
    """
    webhook_log.append({
        "timestamp": datetime.now().isoformat(),
        "event": event
    })
    return {"logged": True}


@router.get("/api/webhooks/recent")
async def get_recent_webhooks(limit: int = 10):
    """
    GET /api/webhooks/recent
    Retorna os últimos N eventos de webhook
    """
    return {
        "total": len(webhook_log),
        "recent": webhook_log[-limit:]
    }


def create_webhook_router():
    return router


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
