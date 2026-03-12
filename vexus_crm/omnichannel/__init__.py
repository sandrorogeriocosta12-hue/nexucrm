"""
Integração omnichannel (WhatsApp, Instagram, Email, etc.)
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class ChannelType(Enum):
    """Tipos de canais suportados"""
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    EMAIL = "email"
    SMS = "sms"
    TELEGRAM = "telegram"
    WEBSITE_CHAT = "website_chat"


@dataclass
class ChannelConfig:
    """Configuração de um canal"""
    channel_type: ChannelType
    enabled: bool = True
    credentials: Dict[str, str] = None
    rate_limit: int = 100
    auto_reply: bool = True
    ai_enabled: bool = True
    
    def __post_init__(self):
        if self.credentials is None:
            self.credentials = {}


class Message:
    """Representa uma mensagem através de qualquer canal"""
    
    def __init__(self, channel: ChannelType, content: str, sender: str, recipient: str, **kwargs):
        self.id = str(uuid.uuid4())
        self.channel = channel
        self.content = content
        self.sender = sender
        self.recipient = recipient
        self.timestamp = datetime.now()
        self.metadata = kwargs.get('metadata', {})
        self.attachments = kwargs.get('attachments', [])
        self.direction = kwargs.get('direction', 'inbound')
        
        # Processamento de IA
        self.ai_processed = False
        self.intent = None
        self.sentiment = None
        self.entities = None


class OmnichannelManager:
    """Gerencia comunicação através de múltiplos canais"""
    
    def __init__(self):
        self.channels: Dict[ChannelType, ChannelConfig] = {}
        self.message_queue: List[Message] = []
        self.conversation_threads: Dict[str, List[Message]] = {}
        
        self._initialize_default_channels()
    
    def _initialize_default_channels(self):
        """Inicializa configurações padrão dos canais"""
        default_channels = [
            ChannelConfig(ChannelType.WHATSAPP, enabled=True),
            ChannelConfig(ChannelType.EMAIL, enabled=True),
            ChannelConfig(ChannelType.INSTAGRAM, enabled=False),
            ChannelConfig(ChannelType.SMS, enabled=False),
            ChannelConfig(ChannelType.TELEGRAM, enabled=False),
            ChannelConfig(ChannelType.FACEBOOK, enabled=False),
            ChannelConfig(ChannelType.WEBSITE_CHAT, enabled=False)
        ]
        
        for config in default_channels:
            self.channels[config.channel_type] = config
    
    async def send_message(self, channel: ChannelType, content: str, 
                         recipient: str, **kwargs) -> Dict[str, Any]:
        """Envia mensagem através de um canal"""
        
        config = self.channels.get(channel)
        if not config or not config.enabled:
            return {"success": False, "error": f"Channel {channel.value} disabled"}
        
        message = Message(
            channel=channel,
            content=content,
            sender="system",
            recipient=recipient,
            direction="outbound",
            metadata=kwargs.get('metadata', {})
        )
        
        try:
            result = {
                "success": True,
                "message_id": message.id,
                "status": "sent",
                "channel": channel.value,
                "timestamp": datetime.now().isoformat()
            }
            
            self._add_to_conversation_thread(recipient, message)
            logger.info(f"Message sent via {channel.value} to {recipient}")
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _add_to_conversation_thread(self, contact_id: str, message: Message):
        """Adiciona mensagem ao histórico da conversa"""
        if contact_id not in self.conversation_threads:
            self.conversation_threads[contact_id] = []
        
        self.conversation_threads[contact_id].append(message)
        
        # Manter apenas últimas 100 mensagens
        if len(self.conversation_threads[contact_id]) > 100:
            self.conversation_threads[contact_id] = self.conversation_threads[contact_id][-100:]
    
    async def process_incoming_message(self, channel: ChannelType, data: Dict) -> Dict:
        """Processa mensagem recebida de qualquer canal"""
        
        message_data = self._extract_message_data(channel, data)
        
        message = Message(
            channel=channel,
            content=message_data['content'],
            sender=message_data['sender'],
            recipient=message_data['recipient'],
            direction="inbound",
            metadata=message_data.get('metadata', {})
        )
        
        self._add_to_conversation_thread(message.sender, message)
        
        logger.info(f"Incoming message from {message.sender} via {channel.value}")
        
        return {
            "message": message_data,
            "processed": True
        }
    
    def _extract_message_data(self, channel: ChannelType, data: Dict) -> Dict:
        """Extrai dados da mensagem baseado no canal"""
        
        return {
            'content': str(data.get('message', '')),
            'sender': data.get('from', 'unknown'),
            'recipient': data.get('to', 'system'),
            'metadata': data
        }
    
    def get_conversation_history(self, contact_id: str, limit: int = 50) -> List[Dict]:
        """Retorna histórico de conversa de um contato"""
        thread = self.conversation_threads.get(contact_id, [])
        
        return [
            {
                "id": msg.id,
                "channel": msg.channel.value,
                "content": msg.content,
                "direction": msg.direction,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in thread[-limit:]
        ]


__all__ = ['ChannelType', 'ChannelConfig', 'Message', 'OmnichannelManager']
