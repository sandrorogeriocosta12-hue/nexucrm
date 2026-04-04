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
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
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


@app.post("/api/payment/process")
async def process_payment(request: Request):
    """
    Complete payment processing with contact info and notification
    Expected payload:
    {
        "plan": "starter|professional|premium",
        "payment_method": "card|boleto|pix",
        "email": "user@email.com",
        "whatsapp": "+55 11 99999-9999",
        "contact_preference_email": true/false,
        "contact_preference_whatsapp": true/false,
        "card_name": "João Silva" (if card),
        "card_number": "4532..." (if card),
        "cnpj": "00.000.000/0000-00" (if boleto),
        "company": "Empresa XYZ" (if boleto)
    }
    """
    try:
        data = await request.json()
        logger.info(f"💳 Processing payment with contact info: {data.get('email')}")

        # Validate required fields
        plan = data.get("plan")
        payment_method = data.get("payment_method")
        email = data.get("email", "").strip()
        whatsapp = data.get("whatsapp", "").strip()

        # Validate plan
        valid_plans = ["starter", "professional", "premium"]
        if plan not in valid_plans:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": f"Plano inválido: {plan}"}
            )

        # Validate payment method
        valid_methods = ["card", "boleto", "pix"]
        if payment_method not in valid_methods:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": f"Método inválido: {payment_method}"}
            )

        # Validate email
        if not email or "@" not in email:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Email válido é obrigatório"}
            )

        # Validate card if card payment
        if payment_method == "card":
            card_name = data.get("card_name", "").strip()
            card_number = data.get("card_number", "").strip()
            card_cvv = data.get("card_cvv", "").strip()

            if not card_name:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "detail": "Nome do titular é obrigatório"}
                )
            if not card_number or len(card_number) < 13:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "detail": "Número do cartão inválido"}
                )
            if not card_cvv or len(card_cvv) < 3:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "detail": "CVV inválido"}
                )

        # Validate CNPJ if boleto payment
        elif payment_method == "boleto":
            cnpj = data.get("boleto_cnpj") or data.get("cnpj", "")
            cnpj = cnpj.strip()
            cnpj_clean = ''.join(filter(str.isdigit, cnpj))

            if len(cnpj_clean) != 14:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "detail": "CNPJ deve ter 14 dígitos"}
                )

        # Store contact preferences
        contact_by_email = data.get("contact_preference_email", True)
        contact_by_whatsapp = data.get("contact_preference_whatsapp", False)

        # Log the payment
        payment_log = {
            "plan": plan,
            "payment_method": payment_method,
            "email": email,
            "whatsapp": whatsapp if contact_by_whatsapp else None,
            "contact_by_email": contact_by_email,
            "contact_by_whatsapp": contact_by_whatsapp,
            "timestamp": str(datetime.now())
        }

        logger.info(f"💳 Payment Details: {payment_log}")

        # Simulate payment processing
        import asyncio
        await asyncio.sleep(0.5)

        # Send confirmation to customer based on preferences
        notification_message = f"""
        ✅ Pagamento Recebido!

        Plano: {plan.upper()}
        Método: {payment_method.upper()}
        Email: {email}
        Status: ATIVO

        Você receberá em breve um email com os dados de acesso à plataforma.
        """

        logger.info(f"📧 Sending notification to: {email}")
        if contact_by_whatsapp and whatsapp:
            logger.info(f"📱 Also sending WhatsApp to: {whatsapp}")

        # Return success
        return JSONResponse(
            content={
                "success": True,
                "message": "Pagamento processado com sucesso!",
                "subscription": {
                    "plan": plan,
                    "payment_method": payment_method,
                    "status": "active",
                    "next_billing": "2024-04-30",
                    "email": email
                },
                "notification": {
                    "email_sent": contact_by_email,
                    "whatsapp_sent": contact_by_whatsapp
                }
            }
        )

    except Exception as e:
        logger.error(f"❌ Payment processing error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "detail": f"Erro ao processar pagamento: {str(e)}"
            }
        )


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
