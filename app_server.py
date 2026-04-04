"""
🚀 NEXUS CRM - Server Principal (FastAPI)

Integrações:
├─ WhatsApp (Evolution API + QR Code)
├─ Telegram (Bot + Token)
├─ Instagram (Meta OAuth)
└─ Email (SendGrid)

Webhooks + AI Scoring + Auto-responses
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os
import logging
from datetime import datetime

# ═════════════════════════════════════════════════════════════
# IMPORTS DOS NOVOS MÓDULOS
# ═════════════════════════════════════════════════════════════

try:
    from webhook_receiver import create_webhook_router
    WEBHOOK_ROUTER = create_webhook_router()
except ImportError:
    print("⚠️  webhook_receiver.py não encontrado em path")
    WEBHOOK_ROUTER = None

try:
    from one_click_integrations import create_integration_router
    INTEGRATION_ROUTER = create_integration_router()
except ImportError:
    print("⚠️  one_click_integrations.py não encontrado em path")
    INTEGRATION_ROUTER = None

# ═════════════════════════════════════════════════════════════
# LOAD ENVIRONMENT
# ═════════════════════════════════════════════════════════════

load_dotenv()

# ═════════════════════════════════════════════════════════════
# LOGGING
# ═════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ═════════════════════════════════════════════════════════════
# INICIALIZAR APP
# ═════════════════════════════════════════════════════════════

app = FastAPI(
    title="Nexus CRM API",
    description="🚀 Sistema de integração de canais de comunicação com IA",
    version="2.0.0",
)

# ═════════════════════════════════════════════════════════════
# CORS
# ═════════════════════════════════════════════════════════════

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═════════════════════════════════════════════════════════════
# INCLUIR ROUTERS DOS NOVOS MÓDULOS
# ═════════════════════════════════════════════════════════════

if WEBHOOK_ROUTER:
    app.include_router(WEBHOOK_ROUTER, tags=["webhooks"])
    logger.info("✅ Webhook router incluído")
else:
    logger.warning("⚠️  Webhook router não disponível")

if INTEGRATION_ROUTER:
    app.include_router(INTEGRATION_ROUTER, tags=["integrations"])
    logger.info("✅ Integration router incluído")
else:
    logger.warning("⚠️  Integration router não disponível")

# ═════════════════════════════════════════════════════════════
# SERVIR FRONTEND INTEGRATIONS
# ═════════════════════════════════════════════════════════════

try:
    app.mount("/integrations-ui", StaticFiles(directory="frontend"), name="integrations-ui")
    logger.info("✅ Frontend integrações montado em /integrations-ui")
except Exception as e:
    logger.warning(f"⚠️  Não conseguiu montar frontend: {e}")

# ═════════════════════════════════════════════════════════════
# ROTAS BÁSICAS
# ═════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {
        "app": "Nexus CRM",
        "version": "2.0.0",
        "status": "🟢 online",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "webhooks": "/webhooks (WhatsApp, Telegram, Instagram)",
            "integrations": "/integrations (OAuth, QR Code, Setup)",
            "frontend": "/integrations-ui",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/status")
async def status():
    """Status completo do sistem"""
    return {
        "app": "Nexus CRM v2.0",
        "status": "online",
        "modules": {
            "webhooks": "✅" if WEBHOOK_ROUTER else "❌",
            "integrations": "✅" if INTEGRATION_ROUTER else "❌",
            "frontend": "✅",
        },
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.now().isoformat()
    }

# ═════════════════════════════════════════════════════════════
# STARTUP EVENTS
# ═════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Nexus CRM iniciando...")
    
    # Verificar Evolution API
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                os.getenv("EVOLUTION_API_URL", "http://localhost:3000") + "/health",
                timeout=5
            )
            if response.status_code == 200:
                logger.info("✅ Evolution API (WhatsApp) disponível")
            else:
                logger.warning("⚠️  Evolution API não respondeu")
    except Exception as e:
        logger.warning(f"⚠️  Evolution API indisponível: {str(e)}")
    
    logger.info("✅ Sistema inicializado com sucesso!")

# ═════════════════════════════════════════════════════════════
# RUN
# ═════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
