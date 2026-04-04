"""
📊 Modelos de CRM - Leads, Campaigns, Contacts
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, Enum
from datetime import datetime
import enum
import uuid

# Use Base from database.py instead of creating a new one
from vexus_crm.database import Base

class Lead(Base):
    """Modelo de Lead (Prospect)"""
    __tablename__ = "leads"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(20))
    company = Column(String(255))
    job_title = Column(String(255))
    value = Column(Float, default=0.0)
    status = Column(String(50), default="novo")  # novo, contato, proposta, fechado, perdido
    source = Column(String(50))  # whatsapp, email, instagram, telefone, etc
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "company": self.company,
            "job_title": self.job_title,
            "value": self.value,
            "status": self.status,
            "source": self.source,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class Campaign(Base):
    """Modelo de Campanha de Marketing"""
    __tablename__ = "campaigns"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    channel = Column(String(50))  # whatsapp, email, instagram, telegram
    budget = Column(Float, default=0.0)
    target_audience = Column(String(500))
    status = Column(String(50), default="planejamento")  # planejamento, ativa, pausada, finalizada
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    messages_sent = Column(Integer, default=0)
    messages_opened = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "channel": self.channel,
            "budget": self.budget,
            "status": self.status,
            "messages_sent": self.messages_sent,
            "conversions": self.conversions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class Contact(Base):
    """Modelo de Contato (Cliente, Parceiro, etc)"""
    __tablename__ = "contacts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(20))
    whatsapp = Column(String(20))
    company = Column(String(255))
    job_title = Column(String(255))
    department = Column(String(100))
    preferred_channel = Column(String(50))  # whatsapp, email, telegram, etc
    tags = Column(String(500))  # Separado por vírgula
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "whatsapp": self.whatsapp,
            "company": self.company,
            "job_title": self.job_title,
            "preferred_channel": self.preferred_channel,
            "tags": self.tags.split(",") if self.tags else [],
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class Message(Base):
    """Modelo de Mensagem (histórico de comunicação)"""
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    contact_id = Column(String, nullable=False, index=True)
    channel = Column(String(50))  # whatsapp, email, telegram, instagram
    direction = Column(String(10))  # incoming, outgoing
    message_text = Column(Text)
    is_read = Column(Boolean, default=False)
    external_message_id = Column(String(255))  # ID da Meta/Telegram/etc
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def dict(self):
        return {
            "id": self.id,
            "contact_id": self.contact_id,
            "channel": self.channel,
            "direction": self.direction,
            "message_text": self.message_text,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
