from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from pathlib import Path
import json
import os
from vexus_crm import config_manager
from vexus_crm.agents.proposal_generator import ProposalGeneratorAgent
from vexus_crm.agents.proposal_models import ProposalRequest, LineItem

router = APIRouter()

# Instanciar agents
proposal_agent = ProposalGeneratorAgent()

BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "configs"
CONFIG_DIR.mkdir(exist_ok=True)

AGENTS_FILE = CONFIG_DIR / "agents_config.json"
CHANNELS_FILE = CONFIG_DIR / "channels_config.json"


def read_json(file_path: Path, default: Dict[str, Any]):
    if not file_path.exists():
        write_json(file_path, default)
        return default
    try:
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def write_json(file_path: Path, data: Dict[str, Any]):
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# Default configs
DEFAULT_AGENTS = {
    "lead_scoring": {"enabled": True, "threshold": 60, "personality": "amigavel"},
    "conversation_analyzer": {"enabled": True, "sensitivity": "medium"},
    "next_best_action": {"enabled": True},
    "proposal_generator": {"enabled": True, "template_id": "default"},
    "followup_scheduler": {"enabled": True, "max_followups": 3},
    "channel_optimizer": {"enabled": True},
    "pipeline_manager": {"enabled": True}
}

DEFAULT_CHANNELS = {
    "whatsapp": {"enabled": False, "provider": "twilio", "api_key": "", "phone_id": ""},
    "telegram": {"enabled": False, "bot_token": ""},
    "email": {"enabled": False, "smtp_host": "", "smtp_port": 587, "username": "", "password": ""},
    "sms": {"enabled": False, "provider": "", "api_key": ""},
    "instagram": {"enabled": False, "access_token": ""},
    "facebook": {"enabled": False, "page_token": ""},
    "website": {"enabled": False, "widget_key": ""}
}


class AgentUpdate(BaseModel):
    enabled: bool | None = None
    settings: dict | None = None


class ChannelUpdate(BaseModel):
    enabled: bool | None = None
    settings: dict | None = None


@router.get("/agents")
def list_agents():
    data = read_json(AGENTS_FILE, DEFAULT_AGENTS)
    return {"agents": data}


@router.get("/agents/{agent_name}")
def get_agent(agent_name: str):
    data = read_json(AGENTS_FILE, DEFAULT_AGENTS)
    agent = data.get(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"name": agent_name, "config": agent}


@router.post("/agents/{agent_name}")
def update_agent(agent_name: str, payload: AgentUpdate):
    data = read_json(AGENTS_FILE, DEFAULT_AGENTS)
    if agent_name not in data:
        data[agent_name] = {}
    if payload.enabled is not None:
        data[agent_name]["enabled"] = payload.enabled
    if payload.settings:
        data[agent_name].setdefault("settings", {}).update(payload.settings)
    write_json(AGENTS_FILE, data)
    # Apply to runtime orchestrator if available
    try:
        config_manager.apply_agent_config(agent_name, data[agent_name])
    except Exception:
        pass
    return {"success": True, "name": agent_name, "config": data[agent_name]}


@router.post("/agents/{agent_name}/test")
def test_agent(agent_name: str, message: dict | None = None):
    data = read_json(AGENTS_FILE, DEFAULT_AGENTS)
    cfg = data.get(agent_name)
    if not cfg:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Simulate a response based on personality/settings
    personality = cfg.get("personality", "amigavel")
    example = {
        "profissional": "Prezado cliente, obrigado pelo contato. Em que posso ajudar hoje?",
        "amigavel": "Oi! Que bom falar com você — como posso ajudar?",
        "consultiva": "Posso entender melhor o seu problema para sugerir a melhor solução?",
        "vendedora": "Ótimo! Temos uma oferta que pode te interessar. Posso apresentar agora?"
    }

    reply = example.get(personality, example["amigavel"])
    return {"agent": agent_name, "personality": personality, "sample_reply": reply, "payload": message}


@router.get("/channels")
def list_channels():
    data = read_json(CHANNELS_FILE, DEFAULT_CHANNELS)
    return {"channels": data}


@router.get("/channels/{channel}")
def get_channel(channel: str):
    data = read_json(CHANNELS_FILE, DEFAULT_CHANNELS)
    cfg = data.get(channel)
    if not cfg:
        raise HTTPException(status_code=404, detail="Channel not found")
    return {"channel": channel, "config": cfg}


@router.post("/channels/{channel}")
def update_channel(channel: str, payload: ChannelUpdate):
    data = read_json(CHANNELS_FILE, DEFAULT_CHANNELS)
    if channel not in data:
        data[channel] = {}
    if payload.enabled is not None:
        data[channel]["enabled"] = payload.enabled
    if payload.settings:
        data[channel].setdefault("settings", {}).update(payload.settings)
    write_json(CHANNELS_FILE, data)
    # Apply to runtime omnichannel if available
    try:
        config_manager.apply_channel_config(channel, data[channel])
    except Exception:
        pass
    return {"success": True, "channel": channel, "config": data[channel]}


@router.get('/ai')
def get_ai_config():
    default = {
        "personalidade": "amigavel",
        "tom": "casual",
        "objecoes": "questionar",
        "prioridade": "vendas",
    }
    cfg = config_manager.read_ai_config(default)
    return {"ai_config": cfg}


@router.post('/ai')
def update_ai_config(payload: dict):
    # Persist AI configuration and apply to runtime orchestrator if possible
    config_manager.write_ai_config(payload)
    try:
        # best-effort: set on orchestrator if attribute exists
        config_manager.apply_agent_config('conversation_analyzer', payload)
    except Exception:
        pass
    return {"success": True, "ai_config": payload}


@router.post("/channels/{channel}/test")
def test_channel(channel: str, payload: dict | None = None):
    data = read_json(CHANNELS_FILE, DEFAULT_CHANNELS)
    cfg = data.get(channel)
    if not cfg:
        raise HTTPException(status_code=404, detail="Channel not found")

    # Simple simulation of a send/test
    if not cfg.get("enabled"):
        return {"ok": False, "message": f"Channel {channel} is disabled. Enable it first."}

    # If whatsapp and provider key present, simulate success
    if channel == "whatsapp":
        if cfg.get("api_key") or cfg.get("settings", {}).get("api_key"):
            return {"ok": True, "message": "WhatsApp simulated send OK"}
        else:
            return {"ok": False, "message": "WhatsApp not fully configured (api_key missing)"}

    # Generic success
    return {"ok": True, "message": f"Simulated send via {channel} OK", "payload": payload}


@router.get("/integrations")
def integrations_quickstart():
    return {
        "whatsapp": {
            "steps": [
                "Crie conta no provedor (Twilio / Meta) e obtenha API key",
                "Insira API key e Phone ID em /api/config/channels/whatsapp",
                "Ative o canal (enabled=true)"
            ],
            "note": "Recomendado usar Twilio para envios programáticos."
        },
        "telegram": {
            "steps": [
                "Crie um Bot com @BotFather e pegue o token",
                "Insira token em /api/config/channels/telegram",
                "Ative o canal"
            ]
        },
        "email": {
            "steps": [
                "Tenha um SMTP (Gmail/SendGrid/SES)",
                "Preencha smtp_host, smtp_port, username e password em /api/config/channels/email",
                "Teste com /api/config/channels/email/test"
            ]
        }
    }

# ==================== PROPOSAL GENERATOR ENDPOINTS ====================

@router.post("/proposals/analyze")
async def analyze_conversation_for_proposal(
    conversation_id: str,
    contact_id: str,
    contact_data: Dict[str, Any]
):
    """
    Analisa conversa para detectar solicitação de proposta.
    
    Usage:
    POST /api/proposals/analyze
    {
        "conversation_id": "conv_001",
        "contact_id": "contact_001",
        "contact_data": {
            "name": "João Silva",
            "email": "joao@example.com",
            "phone": "+5511999999999",
            "company": "Empresa XYZ"
        }
    }
    """
    try:
        # Simulação: buscar conversa
        messages = [
            {"sender": "cliente", "content": "Oi, tudo bem?"},
            {"sender": "bot", "content": "Oi! Como posso ajudar?"},
            {"sender": "cliente", "content": "Preciso de 50 unidades do Produto X. Qual o preço?"}
        ]
        
        # Analisar
        has_request, proposal_req = await proposal_agent.analyze_conversation(
            messages,
            contact_data
        )
        
        if not has_request:
            return {
                "detected": False,
                "message": "Nenhuma solicitação de proposta detectada"
            }
        
        if not proposal_req:
            return {
                "detected": True,
                "message": "Solicitação detectada, mas faltam dados (produtos/preços)"
            }
        
        return {
            "detected": True,
            "proposal_request": proposal_req.dict(),
            "message": "Pronto para gerar proposta!"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/proposals/generate")
async def generate_proposal(proposal_req: ProposalRequest):
    """
    Gera proposta baseada em dados.
    
    Usage:
    POST /api/proposals/generate
    {
        "contact_id": "contact_001",
        "contact_name": "João Silva",
        "contact_email": "joao@example.com",
        "contact_phone": "+5511999999999",
        "line_items": [
            {
                "product_id": "prod_001",
                "product_name": "Produto X",
                "description": "Premium",
                "quantity": 50,
                "unit_price": 100.0,
                "discount_percent": 10
            }
        ]
    }
    """
    try:
        proposal = await proposal_agent.generate(proposal_req)
        
        if not proposal:
            raise HTTPException(status_code=500, detail="Erro ao gerar proposta")
        
        return proposal.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/proposals/{proposal_id}/send")
async def send_proposal(
    proposal_id: str,
    channel: str = "whatsapp",
    vendor_email: str = ""
):
    """
    Envia proposta gerada para cliente.
    
    Usage:
    POST /api/proposals/{proposal_id}/send?channel=whatsapp&vendor_email=vendor@example.com
    """
    try:
        proposal = proposal_agent.get_proposal(proposal_id)
        
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposta não encontrada")
        
        result = await proposal_agent.send_proposal(
            proposal,
            channel=channel,
            vendor_email=vendor_email
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proposals/{proposal_id}")
async def get_proposal(proposal_id: str):
    """
    Obtém detalhes da proposta.
    
    Usage:
    GET /api/proposals/prop_abc123
    """
    proposal = proposal_agent.get_proposal(proposal_id)
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")
    
    return proposal.to_dict()


@router.get("/proposals")
async def list_proposals(contact_id: str = None):
    """
    Lista propostas (opcionalmente filtra por contato).
    
    Usage:
    GET /api/proposals
    GET /api/proposals?contact_id=contact_001
    """
    return proposal_agent.list_proposals(contact_id)


@router.get("/proposals/{proposal_id}/track")
async def track_proposal_view(proposal_id: str):
    """
    Webhook para rastrear visualização de proposta.
    
    Chamado quando cliente clica no link do PDF.
    
    Usage:
    GET /api/proposals/prop_abc123/track
    """
    result = await proposal_agent.track_view(proposal_id)
    return result


@router.get("/proposals/analytics/summary")
async def get_proposal_analytics():
    """
    Retorna analytics agregadas de propostas.
    
    Usage:
    GET /api/proposals/analytics/summary
    """
    analytics = proposal_agent.get_analytics()
    return analytics