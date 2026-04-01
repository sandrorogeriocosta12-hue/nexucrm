"""
Vexus CRM Models
Database models for contacts, opportunities, and other entities
"""

# Import models here for easy access
from .crm_models import Base, Lead, Campaign, Contact, Message

__all__ = ["Base", "Lead", "Campaign", "Contact", "Message"]
