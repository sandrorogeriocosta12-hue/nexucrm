"""
Integração WhatsApp Business API para Vexus CRM
Permite envio de mensagens automáticas e notificações
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel
import requests
import json
import os
from datetime import datetime

from vexus_crm.database import get_db
from vexus_crm.models import User, Lead
from vexus_crm.routes.auth import get_current_user

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Integration"])

# Configurações WhatsApp (em produção, usar variáveis de ambiente)
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "your_access_token_here")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "your_phone_number_id")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "your_verify_token_here")
WHATSAPP_API_VERSION = "v17.0"
WHATSAPP_BASE_URL = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}"

# Modelos Pydantic
class WhatsAppMessage(BaseModel):
    to: str  # Número do destinatário (formato internacional sem +)
    message: str
    lead_id: Optional[str] = None

class WhatsAppTemplateMessage(BaseModel):
    to: str
    template_name: str
    language_code: str = "pt_BR"
    components: Optional[Dict[str, Any]] = None
    lead_id: Optional[str] = None

class WhatsAppResponse(BaseModel):
    message_id: str
    status: str
    to: str
    timestamp: datetime

@router.post("/send-message", response_model=WhatsAppResponse)
async def send_whatsapp_message(
    message_data: WhatsAppMessage,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a WhatsApp message"""

    # Validate phone number format
    if not message_data.to.startswith(("55", "1", "44", "49")):  # Brazil, US, UK, Germany
        raise HTTPException(status_code=400, detail="Invalid phone number format")

    # Send message in background
    background_tasks.add_task(
        _send_whatsapp_message_task,
        message_data.to,
        message_data.message,
        message_data.lead_id
    )

    # Return immediate response
    return WhatsAppResponse(
        message_id=f"temp_{datetime.now().timestamp()}",
        status="queued",
        to=message_data.to,
        timestamp=datetime.now()
    )

@router.post("/send-template", response_model=WhatsAppResponse)
async def send_whatsapp_template(
    template_data: WhatsAppTemplateMessage,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a WhatsApp template message"""

    # Send template message in background
    background_tasks.add_task(
        _send_whatsapp_template_task,
        template_data.to,
        template_data.template_name,
        template_data.language_code,
        template_data.components,
        template_data.lead_id
    )

    return WhatsAppResponse(
        message_id=f"temp_template_{datetime.now().timestamp()}",
        status="queued",
        to=template_data.to,
        timestamp=datetime.now()
    )

@router.post("/automated/welcome/{lead_id}")
async def send_welcome_message(
    lead_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send automated welcome message to new lead"""

    # Get lead information
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if not lead.phone:
        raise HTTPException(status_code=400, detail="Lead has no phone number")

    # Prepare welcome message
    welcome_message = f"""Olá {lead.name}! 👋

Obrigado por entrar em contato conosco!

Somos a Vexus, especialistas em soluções para o seu negócio.

Como podemos ajudar você hoje?

Responda esta mensagem ou agende uma conversa gratuita conosco.

Atenciosamente,
Equipe Vexus CRM"""

    # Send welcome message
    background_tasks.add_task(
        _send_whatsapp_message_task,
        lead.phone,
        welcome_message,
        lead_id
    )

    return {"status": "welcome_message_queued", "lead_id": lead_id}

@router.post("/automated/followup/{lead_id}")
async def send_followup_message(
    lead_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send automated follow-up message"""

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if not lead.phone:
        raise HTTPException(status_code=400, detail="Lead has no phone number")

    followup_message = f"""Oi {lead.name}! 👋

Espero que esteja tudo bem!

Gostaria de saber se você teve a oportunidade de avaliar nossas soluções.

Temos algumas novidades que podem interessar ao seu negócio.

Posso tirar alguma dúvida ou agendar uma demonstração?

Atenciosamente,
Equipe Vexus CRM"""

    background_tasks.add_task(
        _send_whatsapp_message_task,
        lead.phone,
        followup_message,
        lead_id
    )

    return {"status": "followup_message_queued", "lead_id": lead_id}

# Background tasks
async def _send_whatsapp_message_task(to: str, message: str, lead_id: Optional[str] = None):
    """Send WhatsApp message using Facebook Graph API"""

    if not WHATSAPP_ACCESS_TOKEN or WHATSAPP_ACCESS_TOKEN == "your_access_token_here":
        print("⚠️  WhatsApp not configured - skipping message send")
        return

    url = f"{WHATSAPP_BASE_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": message
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        message_id = result.get("messages", [{}])[0].get("id")

        print(f"✅ WhatsApp message sent to {to}, ID: {message_id}")

        # Log message in database (optional)
        if lead_id:
            _log_whatsapp_message(lead_id, "outbound", message, message_id)

    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send WhatsApp message to {to}: {e}")

async def _send_whatsapp_template_task(
    to: str,
    template_name: str,
    language_code: str,
    components: Optional[Dict[str, Any]] = None,
    lead_id: Optional[str] = None
):
    """Send WhatsApp template message"""

    if not WHATSAPP_ACCESS_TOKEN or WHATSAPP_ACCESS_TOKEN == "your_access_token_here":
        print("⚠️  WhatsApp not configured - skipping template send")
        return

    url = f"{WHATSAPP_BASE_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": language_code
            }
        }
    }

    if components:
        payload["template"]["components"] = components

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        message_id = result.get("messages", [{}])[0].get("id")

        print(f"✅ WhatsApp template '{template_name}' sent to {to}, ID: {message_id}")

        if lead_id:
            _log_whatsapp_message(lead_id, "template", template_name, message_id)

    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send WhatsApp template to {to}: {e}")

def _log_whatsapp_message(lead_id: str, message_type: str, content: str, message_id: str):
    """Log WhatsApp message in database (placeholder)"""
    # In production, create a WhatsAppMessage model and log here
    print(f"📝 Logged WhatsApp message: {message_type} to lead {lead_id}")

# Webhook endpoint for incoming messages (optional)
@router.post("/webhook")
async def whatsapp_webhook(request: Dict[str, Any]):
    """Handle incoming WhatsApp messages"""

    # Verify webhook (implement proper verification in production)
    if request.get("object") == "whatsapp_business_account":

        for entry in request.get("entry", []):
            for change in entry.get("changes", []):
                if change.get("field") == "messages":
                    messages = change.get("value", {}).get("messages", [])

                    for message in messages:
                        if message.get("type") == "text":
                            from_number = message.get("from")
                            text = message.get("text", {}).get("body")

                            print(f"📨 Incoming WhatsApp from {from_number}: {text}")

                            # Process incoming message (create lead, update status, etc.)
                            # This would integrate with your CRM logic

    return {"status": "ok"}

@router.get("/webhook")
async def verify_webhook(
    hub_mode: str,
    hub_challenge: str,
    hub_verify_token: str
):
    """Verify WhatsApp webhook"""

    # In production, verify the hub_verify_token
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        return int(hub_challenge)
    elif hub_mode == "subscribe":
        return {"error": "Invalid verify token"}

    raise HTTPException(status_code=403, detail="Verification failed")

@router.get("/config")
async def get_whatsapp_config(current_user: User = Depends(get_current_user)):
    """Get WhatsApp configuration status"""
    return {
        "configured": WHATSAPP_ACCESS_TOKEN != "your_access_token_here",
        "phone_number_id": WHATSAPP_PHONE_NUMBER_ID if WHATSAPP_PHONE_NUMBER_ID != "your_phone_number_id" else None,
        "has_verify_token": WHATSAPP_VERIFY_TOKEN != "your_verify_token_here"
    }

@router.post("/config")
async def update_whatsapp_config(
    access_token: str,
    phone_number_id: str,
    verify_token: str,
    current_user: User = Depends(get_current_user)
):
    """Update WhatsApp configuration (in production, save to database)"""
    # In production, save these to database or secure storage
    # For now, just validate the configuration

    if not access_token or not phone_number_id or not verify_token:
        raise HTTPException(status_code=400, detail="All fields are required")

    # Test the configuration by making a simple API call
    test_url = f"{WHATSAPP_BASE_URL}/{phone_number_id}"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.get(test_url, headers=headers, timeout=10)
        if response.status_code == 200:
            return {
                "status": "configured",
                "message": "WhatsApp Business API configured successfully",
                "phone_number": response.json().get("display_phone_number")
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid WhatsApp credentials")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to connect to WhatsApp API: {str(e)}")

# Utility functions
def format_phone_number(phone: str) -> str:
    """Format phone number for WhatsApp API"""
    # Remove all non-numeric characters
    phone = ''.join(filter(str.isdigit, phone))

    # Add country code if missing (assuming Brazil)
    if len(phone) == 10:  # Mobile without country code
        phone = f"55{phone}"
    elif len(phone) == 8:  # Old format
        phone = f"5511{phone}"  # Assume São Paulo

    return phone

def create_welcome_template() -> Dict[str, Any]:
    """Create welcome message template"""
    return {
        "type": "body",
        "parameters": [
            {"type": "text", "text": "cliente_valioso"}
        ]
    }