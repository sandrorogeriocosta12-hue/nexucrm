"""
API Principal do Vexus CRM Agêntico com FastAPI
Orquestra todos os módulos (Agentes, Fluxos, Pipeline, Omnichannel)
"""

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import logging

# Importar módulos do CRM
from vexus_crm.agents import AgentOrchestrator, AgentType
from vexus_crm.automation import FlowBuilder, BlockType
from vexus_crm.pipelines import VisualPipeline, CardStatus, PipelineCard
from vexus_crm.omnichannel import OmnichannelManager, ChannelType
from vexus_crm.analytics import PipelineAnalytics, LeadAnalytics
from vexus_crm import config_manager

logger = logging.getLogger(__name__)

# Inicializar FastAPI
app = FastAPI(
    title="Vexus CRM Agêntico",
    description="CRM inteligente com IA, automações visuais e omnichannel",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar componentes globais
orchestrator = AgentOrchestrator()
omnichannel = OmnichannelManager()
pipelines: Dict[str, VisualPipeline] = {}
flows: Dict[str, Dict] = {}


# Importar API de configuração (agents & channels)
from vexus_crm.agents_api import router as agents_router
app.include_router(agents_router, prefix="/api/config", tags=["config"])


def _parse_channel(name: str) -> ChannelType:
    """Parse channel string into ChannelType accepting common aliases."""
    if not name:
        raise KeyError(name)
    s = name.strip().lower()
    # Accept simple aliases
    if s in ("website", "website_chat", "websitechat", "site"):
        return ChannelType.WEBSITE_CHAT
    # Normalize common values to enum names
    mapping = {
        "whatsapp": ChannelType.WHATSAPP,
        "instagram": ChannelType.INSTAGRAM,
        "facebook": ChannelType.FACEBOOK,
        "email": ChannelType.EMAIL,
        "sms": ChannelType.SMS,
        "telegram": ChannelType.TELEGRAM
    }
    if s in mapping:
        return mapping[s]
    # Fallback try to access by enum name
    try:
        return ChannelType[s.upper()]
    except Exception:
        # try by value
        for c in ChannelType:
            if c.value == s:
                return c
        raise KeyError(name)


# ==================== SCHEMAS ====================

class LeadCreate(BaseModel):
    """Schema para criar novo lead"""
    name: str
    email: str
    phone: str
    company: str
    interest: str
    budget: Optional[float] = None
    source: str = "manual"
    metadata: Dict[str, Any] = {}


class LeadResponse(BaseModel):
    """Response de lead"""
    id: str
    name: str
    email: str
    phone: str
    company: str
    score: int
    phase: str
    created_at: str
    ai_analysis: Dict[str, Any]


class FlowDefinition(BaseModel):
    """Schema para definir fluxo"""
    name: str
    channel: str
    description: str = ""
    blocks: List[Dict] = []


class PipelineCreate(BaseModel):
    """Schema para criar pipeline"""
    name: str
    description: str = ""


class MessageRequest(BaseModel):
    """Schema para enviar mensagem"""
    channel: str
    recipient: str
    content: str
    metadata: Dict[str, Any] = {}


# ==================== ENDPOINTS - AGENTES ====================

@app.get("/api/agents")
async def list_agents():
    """Lista todos os agentes disponíveis"""
    return {
        "agents": [
            {
                "type": agent_type.value,
                "name": agent_type.value.replace("_", " ").title(),
                "enabled": agent.config.enabled
            }
            for agent_type, agent in orchestrator.agents.items()
        ]
    }


@app.post("/api/agents/score-lead")
async def score_lead(lead: LeadCreate):
    """Score de um lead usando agentes de IA"""
    
    lead_data = {
        "lead": {
            "id": str(datetime.now().timestamp()),
            "name": lead.name,
            "email": lead.email,
            "company": lead.company,
            "company_size": "medium",
            "budget": lead.budget,
            "budget_confirmed": bool(lead.budget),
            "decision_maker": True,
            "urgency": "high" if lead.budget else "normal"
        },
        "conversation_context": lead.interest
    }
    
    # Orquestrar agentes
    result = await orchestrator.orchestrate(lead_data)
    
    return result


@app.post("/api/agents/analyze-conversation")
async def analyze_conversation(conversation: Dict):
    """Analisa conversa usando agentes de IA"""
    
    from vexus_crm.agents import ConversationAnalyzerAgent, AgentConfig, AgentType
    
    agent_config = AgentConfig(AgentType.CONVERSATION_ANALYZER)
    analyzer = ConversationAnalyzerAgent(agent_config)
    
    data = {
        "conversation": conversation.get("text", "")
    }
    
    result = await analyzer.process(data)
    
    return result


# ==================== ENDPOINTS - FLUXOS ====================

@app.post("/api/flows/create")
async def create_flow(flow_def: FlowDefinition):
    """Cria novo fluxo de automação"""
    
    builder = FlowBuilder()
    
    # Criar fluxo baseado no tipo
    if flow_def.channel == "whatsapp":
        flow_dict = builder.create_whatsapp_flow(flow_def.name)
    else:
        flow_dict = builder.to_dict()
    
    flows[flow_dict["id"]] = flow_dict
    
    return {
        "flow_id": flow_dict["id"],
        "name": flow_def.name,
        "channel": flow_def.channel,
        "blocks": len(flow_dict.get("blocks", [])),
        "status": "created"
    }


@app.get("/api/flows/{flow_id}")
async def get_flow(flow_id: str):
    """Retorna definição completa de um fluxo"""
    
    flow = flows.get(flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    
    return flow


@app.post("/api/flows/{flow_id}/execute")
async def execute_flow(flow_id: str, contact_data: Dict):
    """Executa um fluxo para um contato"""
    
    flow_dict = flows.get(flow_id)
    if not flow_dict:
        raise HTTPException(status_code=404, detail="Flow not found")
    
    # Reconstruir builder e executar
    builder = FlowBuilder()
    
    # TODO: Reconstruir blocks a partir do fluxo salvo
    execution = builder.execute(contact_data)
    
    return execution


@app.get("/api/flows")
async def list_flows():
    """Lista todos os fluxos"""
    
    return {
        "flows": [
            {
                "id": f_id,
                "name": f.get("name", "Unnamed"),
                "blocks": len(f.get("blocks", [])),
                "created_at": f.get("created_at")
            }
            for f_id, f in flows.items()
        ]
    }


# ==================== ENDPOINTS - PIPELINE ====================

@app.post("/api/pipelines/create")
async def create_pipeline(pipeline_def: PipelineCreate):
    """Cria novo pipeline visual"""
    
    pipeline = VisualPipeline(pipeline_def.name)
    pipelines[pipeline.id] = pipeline
    
    return {
        "pipeline_id": pipeline.id,
        "name": pipeline.name,
        "phases": [
            {
                "id": phase.id,
                "name": phase.name,
                "description": phase.description,
                "color": phase.color
            }
            for phase in pipeline.phases
        ]
    }


@app.get("/api/pipelines/{pipeline_id}/dashboard")
async def get_pipeline_dashboard(pipeline_id: str):
    """Retorna dashboard do pipeline"""
    
    pipeline = pipelines.get(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    dashboard = pipeline.get_dashboard_data()
    
    # Adicionar analytics
    analytics = PipelineAnalytics(pipeline)
    dashboard["metrics"] = analytics.get_metrics()
    
    return dashboard


@app.post("/api/pipelines/{pipeline_id}/cards")
async def create_card(pipeline_id: str, lead: LeadCreate):
    """Cria novo card (lead) no pipeline"""
    
    pipeline = pipelines.get(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Score o lead
    lead_score = 50
    if lead.budget:
        lead_score += 20
    
    # Criar card
    card = pipeline.add_card(
        title=lead.name,
        phase_name="📥 Leads",
        tags=["novo"],
        fields={
            "email": lead.email,
            "phone": lead.phone,
            "company": lead.company
        }
    )
    
    # Adicionar insights de IA
    card.ai_insights = {
        "score": lead_score,
        "confidence": 0.92,
        "recommendations": ["Score de contato", "Enviar welcome"]
    }
    
    return {
        "card_id": card.id,
        "title": card.title,
        "score": card.lead_score,
        "priority": card.priority
    }


@app.put("/api/pipelines/{pipeline_id}/cards/{card_id}/move")
async def move_card(pipeline_id: str, card_id: str, move_data: Dict):
    """Move card para outra fase"""
    
    pipeline = pipelines.get(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    target_phase = move_data.get("target_phase")
    success = pipeline.move_card(card_id, target_phase)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to move card")
    
    return {"success": True, "card_id": card_id, "new_phase": target_phase}


@app.get("/api/pipelines")
async def list_pipelines():
    """Lista todos os pipelines"""
    
    return {
        "pipelines": [
            {
                "id": p_id,
                "name": p.name,
                "cards": len(p.cards),
                "phases": len(p.phases)
            }
            for p_id, p in pipelines.items()
        ]
    }


# ==================== ENDPOINTS - OMNICHANNEL ====================

@app.post("/api/messages/send")
async def send_message(message: MessageRequest):
    """Envia mensagem através de canal específico"""
    try:
        channel = _parse_channel(message.channel)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Unknown channel: {message.channel}")
    
    result = await omnichannel.send_message(
        channel=channel,
        content=message.content,
        recipient=message.recipient,
        metadata=message.metadata
    )
    
    return result


@app.post("/api/messages/webhook/{channel}")
async def webhook_message(channel: str, data: Dict):
    """Webhook para receber mensagens de canais externos"""
    try:
        channel_type = _parse_channel(channel)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Unknown channel: {channel}")
    
    result = await omnichannel.process_incoming_message(channel_type, data)
    
    return result


@app.get("/api/conversations/{contact_id}")
async def get_conversation(contact_id: str, limit: int = 50):
    """Retorna histórico de conversa de um contato"""
    
    history = omnichannel.get_conversation_history(contact_id, limit)
    
    return {
        "contact_id": contact_id,
        "message_count": len(history),
        "messages": history
    }


@app.get("/api/channels")
async def list_channels():
    """Lista canais disponíveis"""
    
    return {
        "channels": [
            {
                "type": channel_type.value,
                "enabled": config.enabled,
                "name": channel_type.value.replace("_", " ").title()
            }
            for channel_type, config in omnichannel.channels.items()
        ]
    }


# ==================== ENDPOINTS - HEALTH & STATUS ====================

@app.get("/health")
async def health_check():
    """Health check da API"""
    return {
        "status": "healthy",
        "service": "Vexus CRM Agêntico",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/stats")
async def get_stats():
    """Retorna estatísticas gerais do CRM"""
    
    total_cards = sum(len(p.cards) for p in pipelines.values())
    total_flows = len(flows)
    
    return {
        "pipelines": len(pipelines),
        "total_cards": total_cards,
        "flows": total_flows,
        "channels_enabled": sum(1 for c in omnichannel.channels.values() if c.enabled),
        "agents_enabled": sum(1 for a in orchestrator.agents.values() if a.config.enabled)
    }


# ==================== STARTUP ====================

@app.on_event("startup")
async def startup():
    """Inicialização da API"""
    logger.info("Vexus CRM Agêntico iniciado")
    
    # Criar pipeline padrão
    default_pipeline = VisualPipeline("Pipeline Padrão de Vendas")
    pipelines[default_pipeline.id] = default_pipeline
    
    logger.info(f"Pipeline padrão criado: {default_pipeline.id}")
    # Register runtime objects so config updates apply immediately
    try:
        config_manager.set_orchestrator(orchestrator)
        config_manager.set_omnichannel(omnichannel)
    except Exception:
        logger.warning("Failed to register runtime objects in config_manager")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
