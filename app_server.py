"""
🚀 NEXUS CRM - Server Principal (FastAPI)

Integrações:
├─ WhatsApp (Evolution API + QR Code)
├─ Telegram (Bot + Token)
├─ Instagram (Meta OAuth)
└─ Email (SendGrid)

Webhooks + AI Scoring + Auto-responses
"""

print("🚀 STARTING NEXUS CRM SERVER - BUILD: 2026-04-04")

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
from pathlib import Path

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
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
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

try:
    from app.api_main import app as api_main_app
    app.include_router(api_main_app.router, prefix="/api")
    logger.info("✅ API routes included at /api - Payment endpoint available - Build: 2026-04-04")
except ImportError as e:
    logger.warning(f"⚠️  API app not available: {e}")

# ═════════════════════════════════════════════════════════════
# SERVIR FRONTEND INTEGRATIONS
# ═════════════════════════════════════════════════════════════

@app.get("/integrations-ui")
async def integrations_ui():
    return FileResponse(os.path.join(frontend_path, "integrations-oneclick.html"))

# ═════════════════════════════════════════════════════════════
# ROTAS BÁSICAS
# ═════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def root():
    home_file = os.path.join(frontend_path, "home.html")
    if os.path.exists(home_file):
        content = Path(home_file).read_text(encoding="utf-8")
        return HTMLResponse(
            content,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            }
        )
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

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    login_file = os.path.join(frontend_path, "login.html")
    if os.path.exists(login_file):
        content = Path(login_file).read_text(encoding="utf-8")
        return HTMLResponse(
            content,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            }
        )
    raise HTTPException(status_code=404, detail="Login page not found")

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(t: str = None):
    signup_file = os.path.join(frontend_path, "signup.html")
    if os.path.exists(signup_file):
        content = Path(signup_file).read_text(encoding="utf-8")
        if t:
            content = content.replace("</head>", f'<script>window.inviteToken="{t}";</script></head>')
        return HTMLResponse(
            content,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            }
        )
    raise HTTPException(status_code=404, detail="Signup page not found")

@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page():
    forgot_file = os.path.join(frontend_path, "forgot-password.html")
    if os.path.exists(forgot_file):
        content = Path(forgot_file).read_text(encoding="utf-8")
        return HTMLResponse(
            content,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            }
        )
    raise HTTPException(status_code=404, detail="Forgot password page not found")

@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(token: str = None):
    reset_file = os.path.join(frontend_path, "reset-password.html")
    if os.path.exists(reset_file):
        content = Path(reset_file).read_text(encoding="utf-8")
        if token:
            content = content.replace("</head>", f'<script>window.resetToken="{token}";</script></head>')
        return HTMLResponse(
            content,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            }
        )
    raise HTTPException(status_code=404, detail="Reset password page not found")

@app.get("/payment", response_class=HTMLResponse)
async def payment_page():
    payment_file = os.path.join(frontend_path, "payment.html")
    if os.path.exists(payment_file):
        content = Path(payment_file).read_text(encoding="utf-8")
        return HTMLResponse(
            content,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            }
        )
    raise HTTPException(status_code=404, detail="Payment page not found")

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/debug/modules")
async def debug_modules():
    """Debug endpoint para verificar imports dos módulos"""
    import_status = {
        "webhook_receiver": False,
        "one_click_integrations": False,
        "routers_loaded": {
            "WEBHOOK_ROUTER": WEBHOOK_ROUTER is not None,
            "INTEGRATION_ROUTER": INTEGRATION_ROUTER is not None
        }
    }
    
    try:
        import webhook_receiver
        import_status["webhook_receiver"] = True
    except ImportError as e:
        import_status["webhook_receiver_error"] = str(e)
    
    try:
        import one_click_integrations
        import_status["one_click_integrations"] = True
    except ImportError as e:
        import_status["one_click_integrations_error"] = str(e)
    
    return import_status

app.mount("/", StaticFiles(directory=frontend_path), name="frontend")

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
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(
        "app_server:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
