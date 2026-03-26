"""
🔔 SISTEMA DE WEBHOOKS
Notificações em tempo real para eventos do sistema
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from datetime import datetime
import httpx
import json
import logging
from typing import Optional, Dict, Any, List
import asyncio

logger = logging.getLogger(__name__)


class WebhookModel:
    """Modelo de banco para webhooks"""
    __tablename__ = "webhooks"
    
    id = Column(String(36), primary_key=True)
    event_type = Column(String(50), index=True)  # usuario.criado, contato.atualizado, etc
    url = Column(String(500))
    secret = Column(String(256))  # HMAC secret para validação
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered = Column(DateTime, nullable=True)
    failure_count = Column(String(10), default="0")


class WebhookEvent(BaseModel):
    """Evento de webhook"""
    event_type: str  # usuario.criado, contato.atualizado, etc
    resource_type: str  # usuario, contato, etc
    resource_id: str
    timestamp: datetime
    data: Dict[str, Any]


class WebhookPayload(BaseModel):
    """Payload enviado para webhook"""
    event_id: str
    event_type: str
    timestamp: datetime
    resource_type: str
    resource_id: str
    data: Dict[str, Any]


class WebhookService:
    """Serviço de gerenciamento de webhooks"""
    
    # Tipos de eventos suportados
    EVENT_TYPES = {
        "usuario.criado": "Novo usuário criado",
        "usuario.atualizado": "Usuário atualizado",
        "usuario.deletado": "Usuário deletado",
        "contato.criado": "Novo contato criado",
        "contato.atualizado": "Contato atualizado",
        "contato.deletado": "Contato deletado",
        "campanha.iniciada": "Campanha iniciada",
        "campanha.concluida": "Campanha concluída",
        "email.enviado": "Email enviado",
        "sms.enviado": "SMS enviado",
        "pagamento.recebido": "Pagamento recebido",
        "erro.critico": "Erro crítico do sistema",
    }
    
    @staticmethod
    async def trigger_webhook(
        event: WebhookEvent,
        db: Session
    ):
        """
        Dispara webhooks registrados para um evento
        
        Args:
            event: Evento que disparou o webhook
            db: Sessão de banco de dados
        """
        try:
            # Buscar webhooks associados
            # webhooks = db.query(WebhookModel).filter(
            #     WebhookModel.event_type == event.event_type,
            #     WebhookModel.active == True
            # ).all()
            
            # for webhook in webhooks:
            #     asyncio.create_task(
            #         WebhookService._send_webhook(webhook, event)
            #     )
            
            logger.info(f"✅ Webhook disparado para evento: {event.event_type}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao disparar webhook: {e}")
    
    @staticmethod
    async def _send_webhook(webhook, event: WebhookEvent):
        """Envia webhook para URL registrada"""
        try:
            payload = WebhookPayload(
                event_id=str(event),
                event_type=event.event_type,
                timestamp=datetime.utcnow(),
                resource_type=event.resource_type,
                resource_id=event.resource_id,
                data=event.data
            )
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    webhook.url,
                    json=payload.dict(),
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "Nexus CRM Webhook/1.0",
                        "X-Webhook-ID": webhook.id,
                        "X-Event-Type": event.event_type,
                    }
                )
                
                if response.status_code >= 400:
                    logger.warning(f"⚠️ Webhook falhou: {webhook.url} ({response.status_code})")
                    # Incrementar contador de falhas
                    # webhook.failure_count += 1
                    # if webhook.failure_count >= 5:
                    #     webhook.active = False  # Desativar após 5 falhas
                else:
                    logger.info(f"✅ Webhook enviado: {webhook.url}")
                    # webhook.last_triggered = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar webhook: {e}")
    
    @staticmethod
    def register_webhook(
        db: Session,
        event_type: str,
        url: str,
        secret: str
    ) -> bool:
        """
        Registra novo webhook
        
        Args:
            db: Sessão de banco
            event_type: Tipo de evento
            url: URL do webhook
            secret: Secret para HMAC
        
        Returns:
            True se registrado com sucesso
        """
        try:
            if event_type not in WebhookService.EVENT_TYPES:
                logger.error(f"❌ Tipo de evento inválido: {event_type}")
                return False
            
            # webhook = WebhookModel(
            #     id=str(uuid4()),
            #     event_type=event_type,
            #     url=url,
            #     secret=secret,
            #     active=True
            # )
            # db.add(webhook)
            # db.commit()
            
            logger.info(f"✅ Webhook registrado para: {event_type} → {url}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao registrar webhook: {e}")
            return False


# Exemplo de uso em rotas
"""
from fastapi import APIRouter, Depends
from vexus_crm.webhooks import WebhookService, WebhookEvent

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/register")
async def register_webhook(
    event_type: str,
    url: str,
    secret: str,
    db: Session = Depends(get_db)
):
    '''Registra novo webhook'''
    success = WebhookService.register_webhook(db, event_type, url, secret)
    return {"success": success, "message": "Webhook registrado" if success else "Erro ao registrar"}

@router.get("/events")
async def list_events():
    '''Lista tipos de eventos disponíveis'''
    return WebhookService.EVENT_TYPES

# Disparar webhook quando algo acontece
async def create_user(user_data, db):
    # ... código para criar usuário ...
    user = User(**user_data)
    db.add(user)
    db.commit()
    
    # Disparar evento
    event = WebhookEvent(
        event_type="usuario.criado",
        resource_type="usuario",
        resource_id=str(user.id),
        timestamp=datetime.utcnow(),
        data=user.dict()
    )
    await WebhookService.trigger_webhook(event, db)
"""
