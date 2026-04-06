"""
Roteador Omnichannel para Vexus CRM
Centraliza integrações com Instagram, Facebook, Telegram e WhatsApp
"""
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import os
import logging
from datetime import datetime
from vexus_crm.database import get_db
from sqlalchemy.orm import Session
from vexus_crm.models import Lead, Message

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/omnichannel", tags=["Omnichannel Integration"])

# Configurações (Devem ser setadas no Railway como variáveis de ambiente)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "")

class UnifiedMessage(BaseModel):
    recipient_id: str
    content: str
    channel: str # "whatsapp", "telegram", "facebook", "instagram"
    lead_id: Optional[str] = None

# ================= TELEGRAM =================
@router.post("/telegram/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    data = await request.json()
    if "message" in data:
        chat_id = str(data["message"]["chat"]["id"])
        text = data["message"].get("text", "")
        sender_name = data["message"]["from"].get("first_name", "User")
        
        background_tasks.add_task(process_incoming_message, db, chat_id, text, "telegram", sender_name)
    return {"status": "ok"}

async def send_telegram(chat_id: str, text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={"chat_id": chat_id, "text": text})

# ================= FACEBOOK / INSTAGRAM =================
@router.post("/meta/webhook")
async def meta_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Verificação de Webhook da Meta
    params = request.query_params
    if params.get("hub.mode") == "subscribe":
        return int(params.get("hub.challenge"))
    
    data = await request.json()
    for entry in data.get("entry", []):
        for messaging_event in entry.get("messaging", []):
            if messaging_event.get("message"):
                sender_id = messaging_event["sender"]["id"]
                text = messaging_event["message"].get("text", "")
                # Identificar se é IG ou FB pelo ID da página ou metadados
                channel = "instagram" if "instagram" in str(entry) else "facebook"
                
                background_tasks.add_task(process_incoming_message, db, sender_id, text, channel, "Meta User")
    return {"status": "ok"}

async def send_meta(recipient_id: str, text: str, channel: str):
    token = IG_ACCESS_TOKEN if channel == "instagram" else FB_PAGE_ACCESS_TOKEN
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={token}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)

# ================= WHATSAPP =================
async def send_whatsapp(phone_number: str, text: str):
    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": text}
    }
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload, headers=headers)

# ================= UNIFIED SEND =================
@router.post("/send")
async def send_unified_message(msg: UnifiedMessage, db: Session = Depends(get_db)):
    try:
        if msg.channel == "telegram":
            await send_telegram(msg.recipient_id, msg.content)
        elif msg.channel in ["facebook", "instagram"]:
            await send_meta(msg.recipient_id, msg.content, msg.channel)
        elif msg.channel == "whatsapp":
            await send_whatsapp(msg.recipient_id, msg.content)
        else:
            raise HTTPException(status_code=400, detail="Canal inválido")
            
        # Registrar mensagem enviada no banco
        new_msg = Message(
            lead_id=msg.lead_id,
            channel=msg.channel,
            content=msg.content,
            direction="outbound",
            sender="system",
            recipient=msg.recipient_id
        )
        db.add(new_msg)
        db.commit()
        
        return {"status": "sent", "channel": msg.channel}
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================= HELPER =================
async def process_incoming_message(db: Session, sender_id: str, text: str, channel: str, name: str):
    # 1. Tentar encontrar lead pelo ID do canal (armazenado no meta do Lead)
    # Aqui simplificamos buscando ou criando um novo lead
    lead = db.query(Lead).filter(Lead.phone == sender_id).first() # Simplificação
    
    if not lead:
        lead = Lead(name=name, phone=sender_id, source=channel, status="new")
        db.add(lead)
        db.commit()
        db.refresh(lead)
    
    # 2. Salvar mensagem recebida
    new_msg = Message(
        lead_id=lead.id,
        channel=channel,
        content=text,
        direction="inbound",
        sender=sender_id,
        recipient="system"
    )
    db.add(new_msg)
    db.commit()
    logger.info(f"Nova mensagem de {name} via {channel}: {text}")
