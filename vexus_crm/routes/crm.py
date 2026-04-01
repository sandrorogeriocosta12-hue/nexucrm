"""
🚀 Rotas de CRM - Leads, Campaigns, Contacts, Webhooks
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
import json
import logging
from datetime import datetime

from vexus_crm.database import get_db
from vexus_crm.models.crm_models import Lead, Campaign, Contact, Message
from vexus_crm.integrations.channels import channel_connector

router = APIRouter(prefix="/api", tags=["CRM"])
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# 📋 LEADS - ROTAS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/leads")
async def list_leads(db: Session = Depends(get_db), user_id: str = None, status: str = None):
    """Listar todos os leads do usuário"""
    try:
        query = db.query(Lead)
        
        if user_id:
            query = query.filter(Lead.user_id == user_id)
        if status:
            query = query.filter(Lead.status == status)
        
        leads = query.all()
        return {"leads": [lead.dict() for lead in leads], "total": len(leads)}
    
    except Exception as e:
        logger.error(f"❌ Erro ao listar leads: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/leads")
async def create_lead(lead_data: dict, db: Session = Depends(get_db)):
    """Criar novo lead"""
    try:
        new_lead = Lead(
            user_id=lead_data.get("user_id", "system"),
            name=lead_data.get("name", ""),
            email=lead_data.get("email"),
            phone=lead_data.get("phone"),
            company=lead_data.get("company"),
            job_title=lead_data.get("job_title"),
            value=float(lead_data.get("value", 0)),
            status=lead_data.get("status", "novo"),
            source=lead_data.get("source"),
            notes=lead_data.get("notes")
        )
        
        db.add(new_lead)
        db.commit()
        db.refresh(new_lead)
        
        logger.info(f"✅ Lead criado: {new_lead.id}")
        return {"success": True, "lead": new_lead.dict()}
    
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao criar lead: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/leads/{lead_id}")
async def update_lead(lead_id: str, lead_data: dict, db: Session = Depends(get_db)):
    """Atualizar lead existente"""
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead não encontrado")
        
        for key, value in lead_data.items():
            if hasattr(lead, key) and key != "id":
                setattr(lead, key, value)
        
        lead.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(lead)
        
        logger.info(f"✅ Lead atualizado: {lead_id}")
        return {"success": True, "lead": lead.dict()}
    
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao atualizar lead: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str, db: Session = Depends(get_db)):
    """Deletar lead"""
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead não encontrado")
        
        db.delete(lead)
        db.commit()
        
        logger.info(f"✅ Lead deletado: {lead_id}")
        return {"success": True, "message": "Lead deletado"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# 📢 CAMPAIGNS - ROTAS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/campaigns")
async def list_campaigns(db: Session = Depends(get_db), user_id: str = None, channel: str = None):
    """Listar todas as campanhas do usuário"""
    try:
        query = db.query(Campaign)
        
        if user_id:
            query = query.filter(Campaign.user_id == user_id)
        if channel:
            query = query.filter(Campaign.channel == channel)
        
        campaigns = query.all()
        return {"campaigns": [campaign.dict() for campaign in campaigns], "total": len(campaigns)}
    
    except Exception as e:
        logger.error(f"❌ Erro ao listar campanhas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/campaigns")
async def create_campaign(campaign_data: dict, db: Session = Depends(get_db)):
    """Criar nova campanha"""
    try:
        new_campaign = Campaign(
            user_id=campaign_data.get("user_id", "system"),
            name=campaign_data.get("name", ""),
            description=campaign_data.get("description"),
            channel=campaign_data.get("channel", "email"),
            budget=float(campaign_data.get("budget", 0)),
            target_audience=campaign_data.get("target_audience"),
            status=campaign_data.get("status", "planejamento")
        )
        
        db.add(new_campaign)
        db.commit()
        db.refresh(new_campaign)
        
        logger.info(f"✅ Campanha criada: {new_campaign.id}")
        return {"success": True, "campaign": new_campaign.dict()}
    
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao criar campanha: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/campaigns/{campaign_id}")
async def update_campaign(campaign_id: str, campaign_data: dict, db: Session = Depends(get_db)):
    """Atualizar campanha"""
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            raise HTTPException(status_code=404, detail="Campanha não encontrada")
        
        for key, value in campaign_data.items():
            if hasattr(campaign, key) and key != "id":
                setattr(campaign, key, value)
        
        campaign.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(campaign)
        
        logger.info(f"✅ Campanha atualizada: {campaign_id}")
        return {"success": True, "campaign": campaign.dict()}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# 👥 CONTACTS - ROTAS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/contacts")
async def list_contacts(db: Session = Depends(get_db), user_id: str = None):
    """Listar todos os contatos"""
    try:
        query = db.query(Contact)
        
        if user_id:
            query = query.filter(Contact.user_id == user_id)
        
        contacts = query.filter(Contact.is_active == True).all()
        return {"contacts": [contact.dict() for contact in contacts], "total": len(contacts)}
    
    except Exception as e:
        logger.error(f"❌ Erro ao listar contatos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contacts")
async def create_contact(contact_data: dict, db: Session = Depends(get_db)):
    """Criar novo contato"""
    try:
        new_contact = Contact(
            user_id=contact_data.get("user_id", "system"),
            name=contact_data.get("name", ""),
            email=contact_data.get("email"),
            phone=contact_data.get("phone"),
            whatsapp=contact_data.get("whatsapp"),
            company=contact_data.get("company"),
            job_title=contact_data.get("job_title"),
            preferred_channel=contact_data.get("preferred_channel", "whatsapp"),
            tags=",".join(contact_data.get("tags", []))
        )
        
        db.add(new_contact)
        db.commit()
        db.refresh(new_contact)
        
        logger.info(f"✅ Contato criado: {new_contact.id}")
        return {"success": True, "contact": new_contact.dict()}
    
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao criar contato: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/contacts/{contact_id}")
async def update_contact(contact_id: str, contact_data: dict, db: Session = Depends(get_db)):
    """Atualizar contato"""
    try:
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            raise HTTPException(status_code=404, detail="Contato não encontrado")
        
        for key, value in contact_data.items():
            if hasattr(contact, key) and key != "id":
                if key == "tags" and isinstance(value, list):
                    setattr(contact, key, ",".join(value))
                else:
                    setattr(contact, key, value)
        
        contact.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(contact)
        
        logger.info(f"✅ Contato atualizado: {contact_id}")
        return {"success": True, "contact": contact.dict()}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: str, db: Session = Depends(get_db)):
    """Deletar contato (soft delete)"""
    try:
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            raise HTTPException(status_code=404, detail="Contato não encontrado")
        
        contact.is_active = False
        contact.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"✅ Contato deletado: {contact_id}")
        return {"success": True, "message": "Contato deletado"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# 💬 MESSAGES / WEBHOOKS - RECEBER MENSAGENS
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db), background_tasks: BackgroundTasks):
    """Webhook para receber mensagens do WhatsApp"""
    try:
        body = await request.json()
        
        # Processar entrada de mensagens
        if "entry" in body:
            for entry in body["entry"]:
                for change in entry.get("changes", []):
                    if change.get("field") == "messages":
                        for message in change.get("value", {}).get("messages", []):
                            # Extrair dados
                            from_number = change.get("value", {}).get("contacts", [{}])[0].get("wa_id")
                            message_text = message.get("text", {}).get("body", "")
                            contact_name = change.get("value", {}).get("contacts", [{}])[0].get("profile", {}).get("name", "")
                            
                            # Salvar mensagem
                            new_message = Message(
                                user_id="system",
                                contact_id=from_number,
                                channel="whatsapp",
                                direction="incoming",
                                message_text=message_text,
                                external_message_id=message.get("id")
                            )
                            db.add(new_message)
                            db.commit()
                            
                            logger.info(f"📱 WhatsApp recebido de {from_number}: {message_text}")
        
        return {"success": True, "status": "received"}
    
    except Exception as e:
        logger.error(f"❌ Erro webhook WhatsApp: {str(e)}")
        return {"success": False, "error": str(e)}


@router.post("/webhooks/telegram")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)):
    """Webhook para receber mensagens do Telegram"""
    try:
        body = await request.json()
        
        if "message" in body:
            message = body["message"]
            chat_id = message.get("chat", {}).get("id")
            message_text = message.get("text", "")
            user_id = message.get("from", {}).get("id")
            
            # Salvar mensagem
            new_message = Message(
                user_id="system",
                contact_id=str(chat_id),
                channel="telegram",
                direction="incoming",
                message_text=message_text,
                external_message_id=str(message.get("message_id"))
            )
            db.add(new_message)
            db.commit()
            
            logger.info(f"🤖 Telegram recebido: {message_text}")
        
        return {"success": True, "status": "received"}
    
    except Exception as e:
        logger.error(f"❌ Erro webhook Telegram: {str(e)}")
        return {"success": False, "error": str(e)}


@router.post("/webhooks/instagram")
async def instagram_webhook(request: Request, db: Session = Depends(get_db)):
    """Webhook para receber mensagens do Instagram"""
    try:
        body = await request.json()
        
        # Estrutura similar ao WhatsApp (ambos usam Meta)
        if "entry" in body:
            for entry in body["entry"]:
                for change in entry.get("changes", []):
                    if change.get("field") == "messages":
                        for message in change.get("value", {}).get("messages", []):
                            sender_id = change.get("value", {}).get("contacts", [{}])[0].get("wa_id")
                            message_text = message.get("text", {}).get("body", "")
                            
                            new_message = Message(
                                user_id="system",
                                contact_id=sender_id,
                                channel="instagram",
                                direction="incoming",
                                message_text=message_text,
                                external_message_id=message.get("id")
                            )
                            db.add(new_message)
                            db.commit()
                            
                            logger.info(f"📸 Instagram recebido: {message_text}")
        
        return {"success": True, "status": "received"}
    
    except Exception as e:
        logger.error(f"❌ Erro webhook Instagram: {str(e)}")
        return {"success": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# 📤 ENVIAR MENSAGENS
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/send-message")
async def send_message(message_data: dict, db: Session = Depends(get_db), background_tasks: BackgroundTasks):
    """Enviar mensagem por qualquer canal"""
    try:
        channel = message_data.get("channel", "whatsapp")
        destination = message_data.get("destination")  # Número, email, etc
        text = message_data.get("text")
        contact_id = message_data.get("contact_id")
        
        if not all([channel, destination, text]):
            raise HTTPException(status_code=400, detail="Faltam dados obrigatórios")
        
        # Enviar via conector
        result = await channel_connector.send_message(channel, destination, text)
        
        # Salvar histórico
        if result.get("success"):
            msg = Message(
                user_id="system",
                contact_id=contact_id or destination,
                channel=channel,
                direction="outgoing",
                message_text=text,
                external_message_id=result.get("message_id")
            )
            db.add(msg)
            db.commit()
            
            logger.info(f"✅ Mensagem enviada via {channel}")
        
        return result
    
    except Exception as e:
        logger.error(f"❌ Erro ao enviar mensagem: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# 🔗 STATUS DE INTEGRAÇÕES
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/channels/status")
async def get_channels_status():
    """Retorna status de todos os canais de comunicação"""
    return channel_connector.get_status()


logger.info("✅ Rotas de CRM carregadas com sucesso")
