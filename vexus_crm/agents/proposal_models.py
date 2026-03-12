"""
Modelos para o Proposal Generator Agent
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime
import uuid


class ProposalStatus(str, Enum):
    """Estados possíveis de uma proposta"""
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    OPENED = "opened"
    SIGNED = "signed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class LineItem(BaseModel):
    """Item de linha na proposta"""
    product_id: str
    product_name: str
    description: str = ""
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)
    discount_percent: float = Field(default=0, ge=0, le=100)
    
    @property
    def subtotal(self) -> float:
        """Subtotal após desconto"""
        base = self.quantity * self.unit_price
        discount = base * (self.discount_percent / 100)
        return base - discount
    
    def to_dict(self) -> Dict:
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "discount_percent": self.discount_percent,
            "subtotal": round(self.subtotal, 2)
        }


class ProposalRequest(BaseModel):
    """Requisição para gerar proposta"""
    contact_id: str
    contact_name: str
    contact_email: str
    contact_phone: str
    company_name: Optional[str] = None
    
    # Itens
    line_items: List[LineItem] = Field(min_items=1)
    
    # Termos
    valid_until_days: int = Field(default=7)
    payment_terms: str = Field(default="30")  # "30", "30/60/90", etc
    notes: Optional[str] = None
    
    # Contexto
    conversation_id: Optional[str] = None
    message_context: Optional[str] = None


class ProposalData(BaseModel):
    """Proposta gerada"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request: ProposalRequest
    
    # Cálculos
    subtotal: float = 0.0
    tax_percent: float = Field(default=0)
    tax_amount: float = 0.0
    total: float = 0.0
    
    # Armazenamento
    pdf_url: str = ""
    pdf_filename: str = ""
    
    # Rastreamento
    status: ProposalStatus = ProposalStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    viewed_count: int = 0
    signed_at: Optional[datetime] = None
    signed_by: Optional[str] = None
    
    # Análise
    creation_time_ms: float = 0.0
    engagement_score: float = 0.0
    
    def calculate_totals(self, tax_percent: float = 0):
        """Calcula subtotal, impostos e total"""
        self.subtotal = sum(item.subtotal for item in self.request.line_items)
        self.tax_percent = tax_percent
        self.tax_amount = self.subtotal * (self.tax_percent / 100)
        self.total = self.subtotal + self.tax_amount
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "contact_name": self.request.contact_name,
            "status": self.status.value,
            "subtotal": round(self.subtotal, 2),
            "total": round(self.total, 2),
            "created_at": self.created_at.isoformat(),
            "pdf_url": self.pdf_url,
            "engagement_score": self.engagement_score,
            "line_items": [item.to_dict() for item in self.request.line_items]
        }


class ProposalAnalytics(BaseModel):
    """Analytics de proposta"""
    total_generated: int = 0
    total_sent: int = 0
    total_viewed: int = 0
    total_signed: int = 0
    avg_generation_time_ms: float = 0.0
    avg_view_time_minutes: float = 0.0
    send_rate: float = 0.0
    view_rate: float = 0.0
    signing_rate: float = 0.0
    conversion_rate: float = 0.0
    
    def to_report(self) -> Dict:
        return {
            "total_proposals": self.total_generated,
            "avg_generation_time": f"{self.avg_generation_time_ms:.0f}ms",
            "send_rate": f"{self.send_rate:.1f}%",
            "view_rate": f"{self.view_rate:.1f}%",
            "signing_rate": f"{self.signing_rate:.1f}%",
            "conversion_rate": f"{self.conversion_rate:.1f}%"
        }
