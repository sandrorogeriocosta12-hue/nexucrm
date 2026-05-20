"""
📦 Modelos Pydantic para Vexus CRM v1 API
Schemas para validação de requests/responses
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ═══════════════════════════════════════════════════════════════════
# AUTENTICAÇÃO
# ═══════════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: str
    email: str
    name: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ═══════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ═══════════════════════════════════════════════════════════════════

class IntegrationStatus(BaseModel):
    name: str
    enabled: bool
    connected: bool
    last_sync: Optional[datetime] = None
    error_message: Optional[str] = None


class ConfigIntegrationsResponse(BaseModel):
    openai: IntegrationStatus
    whatsapp: IntegrationStatus
    telegram: IntegrationStatus
    instagram: IntegrationStatus
    stripe: IntegrationStatus
    email: IntegrationStatus


class SetupRequest(BaseModel):
    integration: str  # "whatsapp", "telegram", "stripe", etc
    credentials: Dict[str, Any]
    enabled: bool = True


# ═══════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════

class MetricCard(BaseModel):
    title: str
    value: str
    subtitle: str
    icon: str
    trend: Optional[str] = None
    color: str = "blue"


class DashboardMetricsResponse(BaseModel):
    total_sales: MetricCard
    converted_leads: MetricCard
    roi: MetricCard
    active_deals: MetricCard
    pending_tasks: MetricCard


class ChartData(BaseModel):
    label: str
    value: float
    timestamp: Optional[datetime] = None


class DashboardChartsResponse(BaseModel):
    sales_trend: List[ChartData]
    funnel_conversion: Dict[str, int]
    top_agents: List[Dict[str, Any]]
    recent_activities: List[Dict[str, Any]]


# ═══════════════════════════════════════════════════════════════════
# PIPELINE / KANBAN
# ═══════════════════════════════════════════════════════════════════

class PipelineStage(BaseModel):
    id: str
    pipeline_id: str
    name: str
    order: int
    color: str

    class Config:
        from_attributes = True


class Deal(BaseModel):
    id: str
    title: str
    value: float
    stage_id: str
    pipeline_id: str
    contact_id: Optional[str] = None
    probability: float
    position: int
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class CreateDealRequest(BaseModel):
    title: str
    value: float
    stage_id: str
    contact_id: Optional[str] = None
    pipeline_id: Optional[str] = "pipeline_default"
    probability: float = 0.5
    notes: Optional[str] = None


class MoveDealRequest(BaseModel):
    deal_id: Optional[str] = None
    from_stage_id: Optional[str] = None
    to_stage_id: str
    new_position: int = 0


class PipelineInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class PipelineResponse(BaseModel):
    stages: List[PipelineStage]
    deals: List[Deal]


# ═══════════════════════════════════════════════════════════════════
# CONTATOS
# ═══════════════════════════════════════════════════════════════════

class Contact(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    company: Optional[str] = None
    source: str  # "manual", "whatsapp", "telegram", "instagram", "email"
    created_at: datetime
    updated_at: datetime
    tags: List[str] = []
    custom_fields: Optional[Dict[str, Any]] = None


class CreateContactRequest(BaseModel):
    name: str
    email: str
    phone: str
    company: Optional[str] = None
    source: str = "manual"
    tags: List[str] = []


class ContactHistoryEvent(BaseModel):
    id: str
    type: str  # "call", "email", "whatsapp", "telegram", "note"
    title: str
    content: str
    timestamp: datetime
    user: str


class ContactHistoryResponse(BaseModel):
    contact: Contact
    events: List[ContactHistoryEvent]


# ═══════════════════════════════════════════════════════════════════
# TAREFAS E AUTOMAÇÕES
# ═══════════════════════════════════════════════════════════════════

class Task(BaseModel):
    id: str
    title: str
    description: str
    priority: str  # "low", "medium", "high"
    status: str  # "pending", "in_progress", "completed"
    due_date: datetime
    assigned_to: str
    created_at: datetime


class Automation(BaseModel):
    id: str
    name: str
    trigger: str  # "deal_moved", "new_lead", "task_completed"
    trigger_config: Dict[str, Any]
    actions: List[Dict[str, Any]]
    enabled: bool
    created_at: datetime


class CreateAutomationRequest(BaseModel):
    name: str
    trigger: str
    trigger_config: Dict[str, Any]
    actions: List[Dict[str, Any]]


# ═══════════════════════════════════════════════════════════════════
# INBOX OMNICHANNEL
# ═══════════════════════════════════════════════════════════════════

class ChatMessage(BaseModel):
    id: str
    chat_id: str
    sender: str
    sender_id: str
    content: str
    channel: str  # "whatsapp", "telegram", "instagram", "email"
    media_url: Optional[str] = None
    created_at: datetime
    read: bool = False


class Chat(BaseModel):
    id: str
    contact_id: str
    contact_name: str
    channel: str
    last_message: str
    last_message_time: datetime
    unread_count: int
    status: str  # "active", "closed", "archived"


class SendMessageRequest(BaseModel):
    chat_id: str
    contact_id: str
    channel: str
    message: str
    media_url: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════
# KNOWLEDGE LAB - RAG
# ═══════════════════════════════════════════════════════════════════

class Document(BaseModel):
    id: str
    title: str
    file_name: str
    size: int
    uploaded_at: datetime
    status: str  # "processing", "ready", "error"
    embedding_status: str


class KnowledgeQueryRequest(BaseModel):
    query: str
    context: Optional[str] = None
    top_k: int = 3


class KnowledgeQueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float


# ═══════════════════════════════════════════════════════════════════
# WEBHOOKS - REQUEST BODIES
# ═══════════════════════════════════════════════════════════════════

class WhatsAppMessage(BaseModel):
    from_number: str
    message: str
    message_id: str
    timestamp: int
    media_url: Optional[str] = None


class TelegramUpdate(BaseModel):
    update_id: int
    message: Dict[str, Any]


class StripeWebhook(BaseModel):
    id: str
    object: str
    type: str
    data: Dict[str, Any]


class OpenAICompletion(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]


# ═══════════════════════════════════════════════════════════════════
# RESPOSTA GENÉRICA
# ═══════════════════════════════════════════════════════════════════

class SuccessResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    code: str
    details: Optional[Dict[str, Any]] = None
