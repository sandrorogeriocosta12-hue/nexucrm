"""
📋 API v1 - Pipeline, Contatos, Tarefas e Inbox
Endpoints para as 4 telas principais da SPA
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import random
import uuid
import logging

from api_v1_models import (
    Deal, CreateDealRequest, MoveDealRequest, PipelineResponse, PipelineStage,
    PipelineInfo,
    Contact, CreateContactRequest, ContactHistoryResponse, ContactHistoryEvent,
    Task, Automation, CreateAutomationRequest,
    Chat, ChatMessage, SendMessageRequest,
    SuccessResponse, ErrorResponse
)
from api_v1_auth import verify_token
from api_v1_db import get_db, init_db, Pipeline, PipelineStageModel, DealModel
from sqlalchemy.orm import Session
from api_v1_workers import TaskQueue

logger = logging.getLogger(__name__)

try:
    init_db()
    logger.info("✅ API v1 Pipeline database inicializada")
except Exception as e:
    logger.warning(f"⚠️ Falha ao inicializar banco do pipeline: {e}")

# Criar routers para cada módulo
pipeline_router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])
contacts_router = APIRouter(prefix="/api/v1/contacts", tags=["contacts"])
tasks_router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])
inbox_router = APIRouter(prefix="/api/v1/inbox", tags=["inbox"])


# ═══════════════════════════════════════════════════════════════════
# PIPELINE / KANBAN
# ═══════════════════════════════════════════════════════════════════

# Dados mock (em produção: banco de dados)
# A partir de agora o pipeline é persistido em banco para suportar múltiplos funis.


def stage_to_schema(stage: PipelineStageModel) -> PipelineStage:
    return PipelineStage(
        id=stage.id,
        pipeline_id=stage.pipeline_id,
        name=stage.name,
        order=stage.order,
        color=stage.color
    )


def deal_to_schema(deal: DealModel) -> Deal:
    return Deal(
        id=deal.id,
        title=deal.title,
        value=deal.value,
        stage_id=deal.stage_id,
        pipeline_id=deal.pipeline_id,
        contact_id=deal.contact_id or "",
        probability=deal.probability,
        position=getattr(deal, "position", 0),
        created_at=deal.created_at,
        updated_at=deal.updated_at,
        notes=deal.notes
    )



@pipeline_router.get("", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: str = Query("pipeline_default"),
    payload: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    📊 Obter pipeline completo com estágios e negócios
    """
    stages = db.query(PipelineStageModel).filter_by(pipeline_id=pipeline_id).order_by(PipelineStageModel.order).all()
    deals = (
        db.query(DealModel)
        .filter_by(pipeline_id=pipeline_id)
        .order_by(DealModel.stage_id, DealModel.position)
        .all()
    )

    return PipelineResponse(
        stages=[stage_to_schema(stage) for stage in stages],
        deals=[deal_to_schema(deal) for deal in deals]
    )


@pipeline_router.get("/list", response_model=List[PipelineInfo])
async def list_pipelines(
    payload: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    📂 Listar todos os funis de vendas configurados
    """
    pipelines = db.query(Pipeline).order_by(Pipeline.name).all()
    return [PipelineInfo(id=p.id, name=p.name, description=p.description) for p in pipelines]


@pipeline_router.get("/{pipeline_id}/board", response_model=PipelineResponse)
async def get_pipeline_board(
    pipeline_id: str,
    payload: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    📋 Obter o board de um funil específico, com estágios e negócios
    """
    stages = db.query(PipelineStageModel).filter_by(pipeline_id=pipeline_id).order_by(PipelineStageModel.order).all()
    if not stages:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Funil não encontrado")

    deals = (
        db.query(DealModel)
        .filter_by(pipeline_id=pipeline_id)
        .order_by(DealModel.stage_id, DealModel.position)
        .all()
    )

    return PipelineResponse(
        stages=[stage_to_schema(stage) for stage in stages],
        deals=[deal_to_schema(deal) for deal in deals]
    )


@pipeline_router.get("/stages", response_model=List[PipelineStage])
async def get_pipeline_stages(
    pipeline_id: str = Query("pipeline_default"),
    payload: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    📊 Obter Estágios do Pipeline (Colunas do Kanban)
    """
    stages = db.query(PipelineStageModel).filter_by(pipeline_id=pipeline_id).order_by(PipelineStageModel.order).all()
    logger.info(f"📊 Pipeline stages solicitados para {pipeline_id}")
    return [stage_to_schema(stage) for stage in stages]


@pipeline_router.get("/deals", response_model=List[Deal])
async def list_pipeline_deals(
    stage_id: Optional[str] = None,
    pipeline_id: str = Query("pipeline_default"),
    payload: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    📋 Listar Deals
    
    Query params:
    - stage_id: Filtrar por estágio
    - pipeline_id: Filtrar por funil
    """
    query = db.query(DealModel).filter_by(pipeline_id=pipeline_id)
    if stage_id:
        query = query.filter_by(stage_id=stage_id)
    deals = query.order_by(DealModel.position).all()


    logger.info(f"📋 Listando {len(deals)} deals para pipeline {pipeline_id}")
    return [deal_to_schema(deal) for deal in deals]


@pipeline_router.post("/deals", response_model=Deal)
async def create_deal(
    request: CreateDealRequest,
    payload: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    ➕ Criar Novo Deal
    """
    stage = db.query(PipelineStageModel).filter_by(id=request.stage_id, pipeline_id=request.pipeline_id).first()
    if not stage:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Estágio de pipeline inválido")

    new_deal = DealModel(
        id=f"deal_{uuid.uuid4().hex[:8]}",
        title=request.title,
        value=request.value,
        stage_id=request.stage_id,
        pipeline_id=request.pipeline_id,
        contact_id=request.contact_id,
        probability=request.probability,
        position=0,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        notes=request.notes
    )

    db.add(new_deal)
    db.commit()
    db.refresh(new_deal)

    logger.info(f"✅ Deal criado: {new_deal.id} no pipeline {request.pipeline_id}")
    return deal_to_schema(new_deal)


@pipeline_router.put("/deals/{deal_id}/move", response_model=SuccessResponse)
async def move_deal(
    deal_id: str,
    request: MoveDealRequest,
    payload: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    ↔️ Mover Deal Entre Estágios (Drag & Drop do Kanban)
    """
    deal = db.query(DealModel).filter_by(id=deal_id).first()
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal não encontrado"
        )

    target_stage = db.query(PipelineStageModel).filter_by(id=request.to_stage_id, pipeline_id=deal.pipeline_id).first()
    if not target_stage:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estágio de destino inválido para este funil"
        )

    deal.stage_id = request.to_stage_id
    deal.position = int(request.new_position)
    deal.updated_at = datetime.now()
    db.commit()

    from_stage = request.from_stage_id or deal.stage_id
    logger.info(f"↔️ Deal {deal_id} movido de {from_stage} para {request.to_stage_id} (pos={request.new_position})")
    return SuccessResponse(
        success=True,
        message=f"Deal movido para {request.to_stage_id}",
        data={"deal_id": deal_id, "new_stage": request.to_stage_id, "new_position": request.new_position}
    )


# ═══════════════════════════════════════════════════════════════════
# CONTATOS
# ═══════════════════════════════════════════════════════════════════

MOCK_CONTACTS = [
    Contact(
        id="contact_1",
        name="Carlos Silva",
        email="carlos@empresa.com",
        phone="+5511999999999",
        company="Empresa XYZ",
        source="whatsapp",
        created_at=datetime.now() - timedelta(days=30),
        updated_at=datetime.now() - timedelta(days=1),
        tags=["prospect", "premium"]
    ),
    Contact(
        id="contact_2",
        name="Ana Costa",
        email="ana@startup.com",
        phone="+5511988888888",
        company="Startup ABC",
        source="email",
        created_at=datetime.now() - timedelta(days=10),
        updated_at=datetime.now(),
        tags=["hot lead"]
    ),
]


@contacts_router.get("/", response_model=List[Contact])
async def list_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    tags: Optional[str] = None,
    payload: Dict[str, Any] = Depends(verify_token)
):
    """
    👥 Listar Contatos com Paginação e Filtros
    """
    contacts = MOCK_CONTACTS

    if search:
        contacts = [c for c in contacts if search.lower() in c.name.lower() or search.lower() in c.email.lower()]

    if tags:
        tag_list = tags.split(",")
        contacts = [c for c in contacts if any(t in c.tags for t in tag_list)]

    logger.info(f"👥 Listando {len(contacts)} contatos")
    return contacts[skip:skip+limit]


@contacts_router.post("/", response_model=Contact)
async def create_contact(
    request: CreateContactRequest,
    payload: Dict[str, Any] = Depends(verify_token)
):
    """
    ➕ Criar Novo Contato
    """
    new_contact = Contact(
        id=f"contact_{uuid.uuid4().hex[:8]}",
        name=request.name,
        email=request.email,
        phone=request.phone,
        company=request.company,
        source=request.source,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        tags=request.tags
    )

    MOCK_CONTACTS.append(new_contact)
    logger.info(f"✅ Contato criado: {new_contact.id}")

    return new_contact


@contacts_router.get("/{contact_id}/history", response_model=ContactHistoryResponse)
async def get_contact_history(
    contact_id: str,
    payload: Dict[str, Any] = Depends(verify_token)
):
    """
    📖 Obter Histórico de Interações do Contato
    """
    contact = next((c for c in MOCK_CONTACTS if c.id == contact_id), None)
    if not contact:
        raise HTTPException(status_code=404, detail="Contato não encontrado")

    events = [
        ContactHistoryEvent(
            id="event_1",
            type="whatsapp",
            title="Mensagem recebida",
            content="Oi, gostaria de saber mais sobre seus serviços",
            timestamp=datetime.now() - timedelta(days=1),
            user="Cliente"
        ),
        ContactHistoryEvent(
            id="event_2",
            type="email",
            title="Email enviado",
            content="Proposta enviada",
            timestamp=datetime.now() - timedelta(days=2),
            user="João Silva"
        ),
    ]

    logger.info(f"📖 Histórico do contato {contact_id} solicitado")
    return ContactHistoryResponse(contact=contact, events=events)


# ═══════════════════════════════════════════════════════════════════
# TAREFAS E AUTOMAÇÕES
# ═══════════════════════════════════════════════════════════════════

MOCK_TASKS = [
    Task(
        id="task_1",
        title="Ligar para Carlos Silva",
        description="Follow-up sobre proposta enviada",
        priority="high",
        status="pending",
        due_date=datetime.now() + timedelta(days=1),
        assigned_to="João Silva",
        created_at=datetime.now() - timedelta(days=1)
    ),
]


@tasks_router.get("/", response_model=List[Task])
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    payload: Dict[str, Any] = Depends(verify_token)
):
    """
    ✓ Listar Tarefas
    """
    tasks = MOCK_TASKS

    if status:
        tasks = [t for t in tasks if t.status == status]
    if priority:
        tasks = [t for t in tasks if t.priority == priority]

    logger.info(f"✓ Listando {len(tasks)} tarefas")
    return tasks


@tasks_router.post("/automations", response_model=Automation)
async def create_automation(
    request: CreateAutomationRequest,
    payload: Dict[str, Any] = Depends(verify_token)
):
    """
    🤖 Criar Automação (Quando X acontecer, fazer Y)
    """
    automation = Automation(
        id=f"auto_{uuid.uuid4().hex[:8]}",
        name=request.name,
        trigger=request.trigger,
        trigger_config=request.trigger_config,
        actions=request.actions,
        enabled=True,
        created_at=datetime.now()
    )

    logger.info(f"🤖 Automação criada: {automation.id}")
    return automation


# ═══════════════════════════════════════════════════════════════════
# INBOX OMNICHANNEL
# ═══════════════════════════════════════════════════════════════════

MOCK_CHATS = [
    Chat(
        id="chat_1",
        contact_id="contact_1",
        contact_name="Carlos Silva",
        channel="whatsapp",
        last_message="Sim, estou interessado",
        last_message_time=datetime.now() - timedelta(hours=2),
        unread_count=1,
        status="active"
    ),
]


@inbox_router.get("/chats", response_model=List[Chat])
async def list_chats(
    channel: Optional[str] = None,
    payload: Dict[str, Any] = Depends(verify_token)
):
    """
    💬 Listar Conversas Ativas
    """
    chats = MOCK_CHATS

    if channel:
        chats = [c for c in chats if c.channel == channel]

    logger.info(f"💬 Listando {len(chats)} chats")
    return chats


@inbox_router.get("/chats/{chat_id}/messages", response_model=List[ChatMessage])
async def get_chat_messages(
    chat_id: str,
    limit: int = Query(50, ge=1, le=100),
    payload: Dict[str, Any] = Depends(verify_token)
):
    """
    📨 Obter Histórico de Mensagens de um Chat
    """
    messages = [
        ChatMessage(
            id="msg_1",
            chat_id=chat_id,
            sender="Carlos Silva",
            sender_id="contact_1",
            content="Olá, gostaria de saber mais sobre o serviço",
            channel="whatsapp",
            created_at=datetime.now() - timedelta(hours=3),
            read=True
        ),
        ChatMessage(
            id="msg_2",
            chat_id=chat_id,
            sender="João Silva",
            sender_id="user_1",
            content="Olá! Claro, vou enviar uma proposta",
            channel="whatsapp",
            created_at=datetime.now() - timedelta(hours=2),
            read=True
        ),
    ]

    logger.info(f"📨 Carregando {len(messages)} mensagens do chat {chat_id}")
    return messages


@inbox_router.post("/messages/send", response_model=SuccessResponse)
async def send_message(
    request: SendMessageRequest,
    payload: Dict[str, Any] = Depends(verify_token)
):
    """
    📤 Enviar Mensagem via Qualquer Canal
    
    Este endpoint é um centralizador que enfileira a mensagem
    para o canal correto (WhatsApp, Telegram, Instagram, Email)
    """

    logger.info(f"📤 Mensagem para {request.contact_id} via {request.channel} enfileirada")

    if request.channel == "whatsapp":
        await TaskQueue.enqueue_whatsapp_message({
            "chat_id": request.chat_id,
            "contact_id": request.contact_id,
            "message": request.message,
            "media_url": request.media_url
        })
    elif request.channel == "telegram":
        await TaskQueue.enqueue_telegram_message({
            "chat_id": request.chat_id,
            "contact_id": request.contact_id,
            "message": request.message
        })
    elif request.channel == "email":
        await TaskQueue.enqueue_email({
            "to": request.contact_id,
            "subject": "Mensagem do Vexus CRM",
            "body": request.message
        })

    return SuccessResponse(
        success=True,
        message=f"Mensagem enfileirada para envio via {request.channel}",
        data={"chat_id": request.chat_id, "channel": request.channel}
    )
