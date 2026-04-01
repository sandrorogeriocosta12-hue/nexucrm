"""
🔗 Integrações de Canais de Comunicação - Nexus CRM
Centraliza WhatsApp, Telegram, Email, Instagram, Facebook
"""

import requests
import json
from typing import Optional, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

class ChannelConnector:
    """Gerenciador centralizado de integrações de canais"""
    
    def __init__(self):
        """Inicializa credenciais de todos os canais"""
        self.credentials = {
            "whatsapp": {
                "token": os.getenv("WHATSAPP_ACCESS_TOKEN", ""),
                "phone_number_id": os.getenv("WHATSAPP_PHONE_ID", ""),
                "business_account_id": os.getenv("WHATSAPP_BUSINESS_ID", ""),
            },
            "telegram": {
                "token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
            },
            "email": {
                "sendgrid_key": os.getenv("SENDGRID_API_KEY", ""),
                "from_email": os.getenv("EMAIL_FROM", "noreply@nexuscrm.tech"),
            },
            "meta": {
                "token": os.getenv("META_BUSINESS_TOKEN", ""),
                "instagram_business_id": os.getenv("INSTAGRAM_BUSINESS_ID", ""),
            }
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # 📱 WHATSAPP
    # ═══════════════════════════════════════════════════════════════════════
    
    async def send_whatsapp(self, to_number: str, message: str, message_type: str = "template") -> Dict[str, Any]:
        """Envia mensagem WhatsApp via Meta API"""
        if not self.credentials["whatsapp"]["token"]:
            return {"success": False, "error": "WhatsApp não configurado"}
        
        try:
            url = f"https://graph.facebook.com/v18.0/{self.credentials['whatsapp']['phone_number_id']}/messages"
            headers = {
                "Authorization": f"Bearer {self.credentials['whatsapp']['token']}",
                "Content-Type": "application/json"
            }
            
            # Formatar número (adicionar código país se necessário)
            if not to_number.startswith("55"):
                to_number = f"55{to_number}"
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "text",
                "text": {"body": message}
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            result = response.json()
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ WhatsApp enviado para {to_number}")
                return {"success": True, "message_id": result.get("messages", [{}])[0].get("id")}
            else:
                logger.error(f"❌ Erro WhatsApp: {result}")
                return {"success": False, "error": result.get("error", {}).get("message", "Erro desconhecido")}
        
        except Exception as e:
            logger.error(f"❌ Exceção WhatsApp: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_whatsapp_status(self) -> Dict[str, Any]:
        """Verifica se WhatsApp está conectado"""
        if not self.credentials["whatsapp"]["token"]:
            return {"connected": False, "status": "Não configurado"}
        
        try:
            url = f"https://graph.facebook.com/v18.0/{self.credentials['whatsapp']['phone_number_id']}/message_status"
            headers = {"Authorization": f"Bearer {self.credentials['whatsapp']['token']}"}
            
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                return {"connected": True, "status": "Ativo"}
            else:
                return {"connected": False, "status": "Erro na verificação"}
        
        except Exception as e:
            return {"connected": False, "status": f"Erro: {str(e)}"}
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🤖 TELEGRAM
    # ═══════════════════════════════════════════════════════════════════════
    
    async def send_telegram(self, chat_id: str, text: str) -> Dict[str, Any]:
        """Envia mensagem Telegram"""
        if not self.credentials["telegram"]["token"]:
            return {"success": False, "error": "Telegram não configurado"}
        
        try:
            url = f"https://api.telegram.org/bot{self.credentials['telegram']['token']}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()
            
            if result.get("ok"):
                logger.info(f"✅ Telegram enviado para {chat_id}")
                return {"success": True, "message_id": result.get("result", {}).get("message_id")}
            else:
                logger.error(f"❌ Erro Telegram: {result}")
                return {"success": False, "error": result.get("description", "Erro desconhecido")}
        
        except Exception as e:
            logger.error(f"❌ Exceção Telegram: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # ═══════════════════════════════════════════════════════════════════════
    # 📧 EMAIL
    # ═══════════════════════════════════════════════════════════════════════
    
    async def send_email(self, to_email: str, subject: str, content: str, html_content: Optional[str] = None) -> Dict[str, Any]:
        """Envia email via SendGrid"""
        if not self.credentials["email"]["sendgrid_key"]:
            return {"success": False, "error": "Email não configurado"}
        
        try:
            url = "https://api.sendgrid.com/v3/mail/send"
            headers = {
                "Authorization": f"Bearer {self.credentials['email']['sendgrid_key']}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": self.credentials["email"]["from_email"]},
                "subject": subject,
                "content": [
                    {"type": "text/plain", "value": content}
                ]
            }
            
            if html_content:
                payload["content"].append({"type": "text/html", "value": html_content})
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code in [200, 202]:
                logger.info(f"✅ Email enviado para {to_email}")
                return {"success": True, "status": "Email enviado"}
            else:
                logger.error(f"❌ Erro Email: {response.text}")
                return {"success": False, "error": response.text}
        
        except Exception as e:
            logger.error(f"❌ Exceção Email: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # ═══════════════════════════════════════════════════════════════════════
    # 📸 INSTAGRAM / FACEBOOK MESSENGER
    # ═══════════════════════════════════════════════════════════════════════
    
    async def send_meta_message(self, recipient_id: str, message: str, platform: str = "instagram") -> Dict[str, Any]:
        """Envia mensagem via Instagram ou Facebook Messenger"""
        if not self.credentials["meta"]["token"]:
            return {"success": False, "error": "Meta não configurado"}
        
        try:
            url = f"https://graph.instagram.com/v18.0/me/messages?access_token={self.credentials['meta']['token']}"
            
            payload = {
                "recipient": {"id": recipient_id},
                "message": {"text": message}
            }
            
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()
            
            if "message_id" in result:
                logger.info(f"✅ {platform.upper()} enviado para {recipient_id}")
                return {"success": True, "message_id": result["message_id"]}
            else:
                logger.error(f"❌ Erro {platform}: {result}")
                return {"success": False, "error": result.get("error", {}).get("message", "Erro desconhecido")}
        
        except Exception as e:
            logger.error(f"❌ Exceção {platform}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🔄 MÉTODO GENÉRICO
    # ═══════════════════════════════════════════════════════════════════════
    
    async def send_message(self, channel: str, destination: str, message: str, **kwargs) -> Dict[str, Any]:
        """Envia mensagem para qualquer canal"""
        if channel.lower() == "whatsapp":
            return await self.send_whatsapp(destination, message)
        elif channel.lower() == "telegram":
            return await self.send_telegram(destination, message)
        elif channel.lower() == "email":
            return await self.send_email(destination, kwargs.get("subject", "Mensagem"), message, kwargs.get("html"))
        elif channel.lower() in ["instagram", "facebook"]:
            return await self.send_meta_message(destination, message, channel)
        else:
            return {"success": False, "error": f"Canal '{channel}' não suportado"}
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status de todos os canais"""
        return {
            "whatsapp": {"configured": bool(self.credentials["whatsapp"]["token"])},
            "telegram": {"configured": bool(self.credentials["telegram"]["token"])},
            "email": {"configured": bool(self.credentials["email"]["sendgrid_key"])},
            "meta": {"configured": bool(self.credentials["meta"]["token"])}
        }


# Instância global
channel_connector = ChannelConnector()
