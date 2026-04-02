"""
Vexus CRM - Professional FastAPI Server
Enterprise-ready with security, monitoring, and production features
v1.3.0 - CRM APIs + Multi-Channel Integrations (WhatsApp, Telegram, Email, Instagram, Facebook)
# Force rebuild trigger: Admin Dashboard Deployment - $(date)
# DEBUG: Admin router should be loaded
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from pathlib import Path
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
import logging
from datetime import datetime
import os
import time

# DEBUG: Confirm app_server.py is being executed
print("🚀 DEBUG: app_server.py starting execution...")

# Professional logging configuration - Railway compatible (no file logging)
import sys
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # Only stdout for Railway
    ]
)
logger = logging.getLogger(__name__)

# Import professional configuration
try:
    from vexus_crm.config import get_settings
    settings = get_settings()
    logger.info("✓ Professional configuration loaded")
except Exception as e:
    logger.warning(f"⚠ Configuration not available: {e}")
    settings = None

# Import professional middlewares
try:
    from vexus_crm.middleware.rate_limit import RateLimitMiddleware
    from vexus_crm.middleware.security import SecurityHeadersMiddleware, RequestLoggingMiddleware, SQLInjectionProtectionMiddleware
    logger.info("✓ Professional middlewares loaded")
except Exception as e:
    logger.warning(f"⚠ Middlewares not available: {e}")
    RateLimitMiddleware = SecurityHeadersMiddleware = RequestLoggingMiddleware = SQLInjectionProtectionMiddleware = None

# Import Sentry for professional error tracking
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    logger.info("✓ Sentry SDK available")
except ImportError:
    sentry_sdk = None
    logger.info("ℹ Sentry not installed (pip install sentry-sdk)")

# Create FastAPI app with PROFESSIONAL settings (always enable docs)
app = FastAPI(
    title="Vexus CRM API",
    description="Plataforma de CRM inteligente com IA, RAG e Automação de Vendas - Enterprise Edition",
    version="1.0.0",
    openapi_url="/api/openapi.json",  # Always enable for documentation
    docs_url="/api/docs",  # Swagger UI always available
    redoc_url="/api/redoc",  # ReDoc always available
)

# Professional CORS configuration
if settings:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
        max_age=settings.CORS_MAX_AGE,
    )
else:
    # Fallback CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Security middlewares
if SecurityHeadersMiddleware:
    app.add_middleware(SecurityHeadersMiddleware)

if RequestLoggingMiddleware:
    app.add_middleware(RequestLoggingMiddleware)

if SQLInjectionProtectionMiddleware:
    app.add_middleware(SQLInjectionProtectionMiddleware)

# Rate limiting middleware
if RateLimitMiddleware and settings:
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_window=settings.RATE_LIMIT_REQUESTS,
        window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS
    )

# Trusted host middleware for production
if settings and settings.ENVIRONMENT == "production":
    allowed = [h.strip() for h in getattr(settings, 'ALLOWED_HOSTS', ['yourdomain.com']) if h.strip()]
    if allowed:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed)


# create database tables on startup
@app.on_event("startup")
async def startup_db():
    app.startup_time = time.time()
    logger.info("🚀 Vexus CRM API starting up...")
    
    # VALIDATION: Check critical environment variables
    if settings:
        critical_errors = []
        
        # Check DATABASE_URL
        db_url = os.getenv("DATABASE_URL", "").strip()
        if not db_url or "localhost" in db_url:
            critical_errors.append("❌ DATABASE_URL not set or uses localhost (Railway requires production DB)")
        
        # Check SECRET_KEY in production
        if settings.ENVIRONMENT == "production":
            secret_key = os.getenv("SECRET_KEY", "").strip()
            if not secret_key or secret_key == "dev-secret-key-change-in-production":
                critical_errors.append("❌ SECRET_KEY not configured for production")
        
        if critical_errors:
            logger.warning("⚠️  CRITICAL ENVIRONMENT ISSUES:")
            for error in critical_errors:
                logger.warning(error)
    
    try:
        from vexus_crm.database import engine, get_db
        from vexus_crm import models
        from sqlalchemy.orm import Session

        models.Base.metadata.create_all(bind=engine)
        logger.info("✓ Database schema ensured")
        
        # Create test user if it doesn't exist
        db = next(get_db())
        try:
            from vexus_crm.models import User
            from vexus_crm.routes.auth import get_password_hash
            
            test_user = db.query(User).filter(User.email == "test@nexus.com").first()
            if not test_user:
                import uuid
                hashed_password = get_password_hash("test123")
                test_user = User(
                    id=str(uuid.uuid4()),
                    email="test@nexus.com",
                    name="Test User",
                    password_hash=hashed_password,
                    role="user",
                    plan="free",
                    is_active=True,
                )
                db.add(test_user)
                db.commit()
                logger.info("✓ Test user created")
            else:
                logger.info("✓ Test user already exists")
                
        except Exception as e:
            logger.warning(f"⚠ Could not create test user: {e}")
        finally:
            db.close()
            
    except ImportError:
        logger.warning("⚠ SQLAlchemy not available - database features disabled")
    except Exception as e:
        logger.error(f"Error creating database schema: {e}")


# Importar routers (simplificado e seguro para Railway)
try:
    from vexus_crm.routes.auth import router as auth_router
    app.include_router(auth_router)
    logger.info("✓ Auth router loaded")
except Exception as e:
    logger.warning(f"⚠ Auth router not available: {e}")

try:
    from vexus_crm.routes.leads import router as leads_router
    app.include_router(leads_router, prefix="/api")
    logger.info("✓ Leads router loaded")
except Exception as e:
    logger.warning(f"⚠ Leads router not available: {e}")

try:
    from vexus_crm.routes.campaigns import router as campaigns_router
    app.include_router(campaigns_router, prefix="/api")
    logger.info("✓ Campaigns router loaded")
except Exception as e:
    logger.warning(f"⚠ Campaigns router not available: {e}")

try:
    from vexus_crm.routes.contacts import router as contacts_router
    app.include_router(contacts_router, prefix="/api")
    logger.info("✓ Contacts router loaded")
except Exception as e:
    logger.warning(f"⚠ Contacts router not available: {e}")

try:
    from vexus_crm.routes.notifications import router as notifications_router
    app.include_router(notifications_router, prefix="/api")
    logger.info("✓ Notifications router loaded")
except Exception as e:
    logger.warning(f"⚠ Notifications router not available: {e}")

try:
    from vexus_crm.routes.analytics import router as analytics_router
    app.include_router(analytics_router, prefix="/api")
    logger.info("✓ Analytics router loaded")
except Exception as e:
    logger.warning(f"⚠ Analytics router not available: {e}")

try:
    from vexus_crm.routes.whatsapp import router as whatsapp_router
    app.include_router(whatsapp_router, prefix="/api")
    logger.info("✓ WhatsApp router loaded")
except Exception as e:
    logger.warning(f"⚠ WhatsApp router not available: {e}")

try:
    from vexus_crm.routes.segmentation import router as segmentation_router
    app.include_router(segmentation_router, prefix="/api")
    logger.info("✓ Segmentation router loaded")
except Exception as e:
    logger.warning(f"⚠ Segmentation router not available: {e}")

try:
    from vexus_crm.routes.knowledge_lab import router as knowledge_router
    app.include_router(knowledge_router)
    logger.info("✓ Knowledge Lab router loaded")
except Exception as e:
    logger.warning(f"⚠ Knowledge Lab router not available: {e}")

try:
    from vexus_crm.routes.crm import router as crm_router
    app.include_router(crm_router)
    logger.info("✅ CRM router loaded - Leads, Campaigns, Contacts, Webhooks, Multi-Channel")
except Exception as e:
    logger.warning(f"⚠ CRM router not available: {e}")

try:
    from vexus_crm.admin.routes import router as admin_router
    app.include_router(admin_router)
    logger.info("✅ Admin router loaded - Dashboard, Login, Token Management")
    # Debug: Log admin routes
    admin_routes = [r.path for r in admin_router.routes]
    logger.info(f"📋 Admin routes registered: {len(admin_routes)} routes - {admin_routes[:3]}...")
except Exception as e:
    logger.error(f"❌ CRITICAL: Admin router failed to load: {e}")
    logger.error("This will prevent admin dashboard from working!")
    # Don't fail the entire app, but log the error prominently
    import traceback
    logger.error(f"Full traceback: {traceback.format_exc()}")

try:
    # Simple agents router for testing
    from fastapi import APIRouter
    agents_router = APIRouter(prefix="/api/agents", tags=["Agents"])
    
    @agents_router.get("/")
    async def get_agents_config():
        """Get agents configuration"""
        return {
            "agents": {
                "scoring_agent": {"enabled": True, "model": "gpt-4"},
                "pipeline_manager": {"enabled": True, "model": "gpt-4"},
                "conversation_analyzer": {"enabled": True, "model": "gpt-4"},
                "next_best_action": {"enabled": True, "model": "gpt-4"},
                "proposal_generator": {"enabled": True, "model": "gpt-4"},
                "followup_scheduler": {"enabled": True, "model": "gpt-4"},
                "channel_optimizer": {"enabled": True, "model": "gpt-4"}
            }
        }
    
    @agents_router.get("")  # Also handle /api/agents without trailing slash
    async def get_agents_config_alt():
        """Get agents configuration (alternative route)"""
        return await get_agents_config()
    
    app.include_router(agents_router)
    logger.info("✓ Agents router loaded")
except Exception as e:
    logger.warning(f"⚠ Agents router not available: {e}")

# Define frontend_path early for all routes to use
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")

# HOME PAGE ROUTE - DEFINED FIRST before any routers are included (critical for routing order)
@app.get("/", response_class=HTMLResponse, name="home_landing")
async def serve_landing_page(request: Request):
    """Serve the professional home.html landing page"""
    logger.info("🏠 Serving home.html landing page")
    
    home_path = Path(frontend_path) / "home.html"
    
    if not home_path.exists():
        logger.error(f"⚠️  home.html not found at {home_path}")
        return HTMLResponse("<h1>Error: home.html not found</h1>", status_code=500)
    
    content = home_path.read_text(encoding="utf-8")
    return HTMLResponse(content, headers={
        "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
        "X-Served-By": "serve_landing_page"
    })

# Include main API router from app/api_main
try:
    from app.api_main import app as api_main_app
    app.include_router(api_main_app.router)
    logger.info("✓ Main API router loaded")
except Exception as e:
    logger.warning(f"⚠ Main API router not available: {e}")

@app.get("/app", response_class=HTMLResponse)
async def app_frontend():
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())

    app_html_path = os.path.join(frontend_path, "app.html")
    if os.path.exists(app_html_path):
        with open(app_html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())

    return HTMLResponse("<h2>Vexus CRM Frontend não encontrado</h2>", status_code=404)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """🚀 Serve login.html from file with NO-CACHE headers"""
    login_file = os.path.join(frontend_path, "login.html")
    
    if os.path.exists(login_file):
        logger.info(f"✅ Serving login.html from {login_file}")
        with open(login_file, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(
            content=content,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            }
        )
    
    logger.warning(f"❌ login.html not found at {login_file}")
    return HTMLResponse("<h2>❌ Login page not found</h2>", status_code=404)


@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request, t: str = None):
    """🚀 Serve signup.html from file with NO-CACHE headers"""
    signup_file = os.path.join(frontend_path, "signup.html")
    
    if os.path.exists(signup_file):
        logger.info(f"✅ Serving signup.html from {signup_file}")
        with open(signup_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Add token to content if provided via ?t=TOKEN
        if t:
            content = content.replace("</head>", f'<script>window.inviteToken="{t}";</script></head>')
            logger.info(f"✅ Added invite token to signup: {t[:20]}...")
        
        return HTMLResponse(
            content=content,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            }
        )
    
    logger.warning(f"❌ signup.html not found at {signup_file}")
    return HTMLResponse("<h2>❌ Signup page not found</h2>", status_code=404)


@app.get("/plan-selection", response_class=HTMLResponse)
async def plan_selection_page(request: Request):
    """🎯 Serve plan-selection.html - Plan selection page"""
    plan_file = os.path.join(frontend_path, "plan-selection.html")
    
    if os.path.exists(plan_file):
        logger.info(f"✅ Serving plan-selection.html from {plan_file}")
        with open(plan_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        return HTMLResponse(
            content=content,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            }
        )
    
    logger.warning(f"❌ plan-selection.html not found at {plan_file}")
    return HTMLResponse("<h2>❌ Plan selection page not found</h2>", status_code=404)


@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    """🔒 Serve privacy.html - Privacy policy page"""
    privacy_file = os.path.join(frontend_path, "privacy.html")
    
    if os.path.exists(privacy_file):
        logger.info(f"✅ Serving privacy.html from {privacy_file}")
        with open(privacy_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        return HTMLResponse(content=content)
    
    logger.warning(f"❌ privacy.html not found at {privacy_file}")
    return HTMLResponse("<h2>❌ Privacy policy not found</h2>", status_code=404)


@app.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    """📋 Serve terms.html - Terms of service page"""
    terms_file = os.path.join(frontend_path, "terms.html")
    
    if os.path.exists(terms_file):
        logger.info(f"✅ Serving terms.html from {terms_file}")
        with open(terms_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        return HTMLResponse(content=content)
    
    logger.warning(f"❌ terms.html not found at {terms_file}")
    return HTMLResponse("<h2>❌ Terms of service not found</h2>", status_code=404)


@app.get("/payment", response_class=HTMLResponse)
async def payment_page(request: Request):
    """💳 Serve payment.html - Payment and plan selection page"""
    payment_file = os.path.join(frontend_path, "payment.html")
    
    if os.path.exists(payment_file):
        logger.info(f"✅ Serving payment.html from {payment_file}")
        with open(payment_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        return HTMLResponse(
            content=content,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            }
        )
    
    logger.warning(f"❌ payment.html not found at {payment_file}")
    return HTMLResponse("<h2>❌ Payment page not found</h2>", status_code=404)


# ============================================================================
# � AUTHENTICATION API ENDPOINTS
# ============================================================================

@app.post("/api/auth/signup")
async def signup(request: Request):
    """
    Signup endpoint - Create new user account
    Expected payload: {
        "name": "Full Name",
        "email": "user@email.com",
        "password": "secure123",
        "company": "Company Name",
        "plan": "starter|professional|premium"
    }
    """
    try:
        data = await request.json()
        logger.info(f"🚀 Signup request: {data.get('email', 'unknown')}")
        
        # Validate required fields
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        company = data.get("company", "")
        plan = data.get("plan", "professional")
        
        if not all([name, email, password]):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "detail": "Nome, email e senha são obrigatórios"
                }
            )
        
        # Basic email validation
        if "@" not in email or "." not in email:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "detail": "Email inválido"
                }
            )
        
        # Validate plan
        valid_plans = ["starter", "professional", "premium"]
        if plan not in valid_plans:
            plan = "professional"
        
        # TODO: Check if user already exists in database
        # TODO: Hash password and store in database
        # For now, we'll mock this
        
        logger.info(f"✅ Signup successful: {email}, Plan: {plan}")
        
        return JSONResponse(
            content={
                "success": True,
                "message": "Conta criada com sucesso! Redirecionando para contato...",
                "user": {
                    "email": email,
                    "name": name,
                    "plan": plan,
                    "sobrenome": data.get("sobrenome", "")
                },
                "redirect": f"/payment?email={email}&name={name}&plan={plan}"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Signup error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "detail": "Erro ao criar conta. Tente novamente."
            }
        )


# ============================================================================
# �💳 PAYMENT API ENDPOINTS
# ============================================================================

@app.post("/api/payment/subscribe")
async def process_payment_subscription(request: Request):
    """
    Process payment subscription after plan selection
    Expected JSON payload:
    {
        "plan": "starter|professional|premium",
        "payment_method": "card|boleto",
        "cnpj": "optional CNPJ for boleto payments",
        "card_data": {optional card details for card payments}
    }
    """
    try:
        data = await request.json()
        logger.info(f"💳 Processing payment subscription: {data.get('plan', 'unknown')}")

        # Validate required fields
        plan = data.get("plan")
        payment_method = data.get("payment_method")

        if not plan or not payment_method:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Plano e método de pagamento são obrigatórios"
                }
            )

        # Validate plan
        valid_plans = ["starter", "professional", "premium"]
        if plan not in valid_plans:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": f"Plano inválido. Opções: {', '.join(valid_plans)}"
                }
            )

        # Validate payment method
        valid_methods = ["card", "boleto"]
        if payment_method not in valid_methods:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": f"Método de pagamento inválido. Opções: {', '.join(valid_methods)}"
                }
            )

        # Validate CNPJ for boleto payments
        if payment_method == "boleto":
            cnpj = data.get("cnpj", "").strip()
            if not cnpj:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": "CNPJ é obrigatório para pagamentos via boleto"
                    }
                )
            # Basic CNPJ validation (remove formatting and check length)
            cnpj_clean = ''.join(filter(str.isdigit, cnpj))
            if len(cnpj_clean) != 14:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": "CNPJ deve ter 14 dígitos"
                    }
                )

        # TODO: Integrate with actual payment gateway (Stripe, PagSeguro, etc.)
        # For now, simulate successful payment processing
        logger.info(f"✅ Payment processed successfully for plan: {plan}, method: {payment_method}")

        # Mock payment processing delay
        import asyncio
        await asyncio.sleep(1)

        # Return success response
        return JSONResponse(
            content={
                "success": True,
                "message": "Pagamento processado com sucesso!",
                "subscription": {
                    "plan": plan,
                    "payment_method": payment_method,
                    "status": "active",
                    "next_billing": "2024-02-01"  # Mock date
                },
                "redirect_url": "/dashboard"
            }
        )

    except Exception as e:
        logger.error(f"❌ Payment processing error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Erro interno no processamento do pagamento"
            }
        )


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


# Mount static files (frontend)
if os.path.exists(frontend_path):
    try:
        app.mount("/frontend", StaticFiles(directory=frontend_path), name="frontend")
        logger.info(f"✓ Frontend mounted at /frontend from {frontend_path}")
    except Exception as e:
        logger.error(f"❌ Failed to mount frontend: {e}")
        logger.warning("⚠️  Frontend files may not be accessible from /frontend")
else:
    logger.warning(f"⚠️  Frontend directory not found at {frontend_path}")



# ============================================================================
# 🏥 HEALTH CHECKS & MONITORING ENDPOINTS (Professional Grade)
# ============================================================================

@app.get("/health", tags=["Monitoring"])
async def health_check():
    """
    Simple health check for load balancers.
    Responds fast with 200 OK if service is running.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }


@app.get("/status", tags=["Monitoring"])
async def detailed_status():
    """
    Detailed status check - includes database and service health.
    """
    status_data = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "api": "✓ operational",
            "frontend": "✓ operational",
        }
    }
    
    # Check database connection
    try:
        if settings:
            db_status = "✓ connected"
            status_data["services"]["database"] = db_status
    except Exception as e:
        status_data["services"]["database"] = f"✗ error: {str(e)}"
        status_data["status"] = "degraded"
    
    return status_data


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """
    Basic metrics endpoint for monitoring systems.
    Returns request stats and performance metrics.
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": (datetime.now() - datetime.fromtimestamp(os.path.getmtime(__file__) if os.path.exists(__file__) else time.time())).total_seconds(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database_configured": settings is not None,
        "debug_mode": settings.DEBUG if settings else False,
    }


@app.get("/integrations/status", tags=["Integrations"])
async def integrations_status():
    """
    🔗 Status de todas as integrações de canais de comunicação
    Retorna quais canais estão configurados (WhatsApp, Telegram, Email, Instagram, Facebook)
    """
    try:
        from vexus_crm.integrations.channels import channel_connector
        return {
            "status": "online",
            "channels": channel_connector.get_status(),
            "endpoints": {
                "send_message": "POST /api/send-message",
                "webhook_whatsapp": "POST /api/webhooks/whatsapp",
                "webhook_telegram": "POST /api/webhooks/telegram",
                "webhook_instagram": "POST /api/webhooks/instagram",
                "channels_status": "GET /api/channels/status"
            },
            "documentation": "Use POST /api/send-message para enviar mensagens em qualquer canal"
        }
    except Exception as e:
        logger.warning(f"⚠ Erro ao obter status de integrações: {e}")
        return {
            "status": "error",
            "message": "Integrações não disponíveis",
            "error": str(e)
        }


# ============================================================================
# 📄 FRONTEND ROUTES
# ============================================================================




@app.get("/signup-test", response_class=HTMLResponse)
async def signup_test(request: Request, t: str = None):
    """TEST ROUTE: Serve signup page with different URL to bypass Cloudflare cache"""
    # 🔥 TEST: Different route to bypass cache
    current_version = f"test-v{int(time.time() * 1000000)}"  # Unique version per microsecond
    
    # 🔥 TEMPORARY PATCH: Serve embedded HTML with fixed modal to bypass file sync issues
    signup_html = f"""<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>Nexus Service - Cadastro (TEST)</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            min-height: 100vh;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem 1rem;
        }}
        .terms-modal {{
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            background-color: rgba(0, 0, 0, 0.8) !important;
            z-index: 99999 !important;
            display: none !important;
            align-items: center !important;
            justify-content: center !important;
            min-height: 100vh !important;
            padding: 1rem !important;
            visibility: hidden !important;
            opacity: 0 !important;
        }}
        #termsModal {{
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            background-color: rgba(0, 0, 0, 0.5) !important;
            z-index: 99999 !important;
            display: none !important;
        }}
        #termsModal:not(.hidden) {{
            display: flex !important;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 1rem;
        }}
    </style>
</head>
<body>
    <div style="width: 384px; padding: 32px; border-radius: 8px; border: 1px solid rgb(55, 65, 81); background: linear-gradient(135deg, rgb(30, 41, 59), rgb(15, 23, 42)); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3); margin: 50px auto;">
        
        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 32px;">
            <div style="width: 60px; height: 60px; background: linear-gradient(135deg, #a855f7, #ec4899); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 28px; color: white; box-shadow: 0 8px 32px rgba(168, 85, 247, 0.3);">N</div>
        </div>
        
        <h1 style="background: linear-gradient(135deg, #8b5cf6, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-size: 30px; font-weight: bold; text-align: center; margin-bottom: 8px;">Nexus Service</h1>
        <p style="text-align: center; color: rgb(156, 163, 175); font-size: 14px; margin-bottom: 4px;">Criar Conta (TEST ROUTE)</p>
        <p style="text-align: center; color: rgb(107, 114, 128); font-size: 12px; margin-bottom: 32px;">Testando modal sem cache</p>
        
        <div id="testResult" style="color: green; background-color: rgba(34, 197, 94, 0.2); border: 1px solid rgba(34, 197, 94, 0.3); padding: 12px; border-radius: 8px; margin-bottom: 16px; display: none;"></div>
        
        <button onclick="testModal()" style="width: 100%; padding: 14px; background: linear-gradient(135deg, #8b5cf6, #ec4899); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; margin-bottom: 16px;">🧪 Testar Modal</button>
        
        <div class="form-group" style="margin-bottom: 24px;">
            <input type="checkbox" id="terms" required style="width: auto; margin: 0;">
            <label for="terms" style="display: inline; margin-left: 8px;">Aceito os <a href="#" onclick="event.preventDefault(); openTermsModal(); return false;" style="color: #8b5cf6; text-decoration: none; font-weight: 500;">termos de serviço</a></label>
        </div>

        <p style="text-align: center; font-size: 14px; color: rgb(156, 163, 175); margin-top: 24px;">
            <a href="/signup" style="color: rgb(168, 85, 247); font-weight: 600; text-decoration: none;">← Voltar para signup normal</a>
        </p>
    </div>

    <div id="termsModal" class="terms-modal">
        <div style="background-color: #1f2937; border-radius: 12px; max-width: 56rem; width: 100%; max-height: 90vh; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);">
            <div style="padding: 1.5rem; border-bottom: 1px solid #374151; display: flex; align-items: center; justify-content: space-between;">
                <h3 style="background: linear-gradient(135deg, #8b5cf6, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin: 0; font-size: 1.25rem; font-weight: 700;">Termos de Serviço</h3>
                <button onclick="closeTermsModal()" style="color: #9ca3af; font-size: 1.5rem; background: none; border: none; cursor: pointer; padding: 0;">&times;</button>
            </div>
            <div style="padding: 1.5rem; overflow-y: auto; max-height: 70vh;">
                <div style="color: #d1d5db;">
                    <h4 style="color: #8b5cf6; font-weight: 600; margin-bottom: 1rem;">1. Aceitação dos Termos</h4>
                    <p style="margin-bottom: 1rem;">Ao acessar e usar o Nexus Service, você concorda em cumprir e estar vinculado a estes Termos de Serviço.</p>
                    <h4 style="color: #8b5cf6; font-weight: 600; margin-bottom: 1rem;">2. Teste do Modal</h4>
                    <p style="margin-bottom: 1rem;">Esta é uma rota de teste para verificar se o modal funciona sem cache do Cloudflare.</p>
                </div>
            </div>
            <div style="padding: 1.5rem; border-top: 1px solid #374151; display: flex; justify-content: flex-end; gap: 1rem;">
                <button onclick="closeTermsModal()" style="background: rgba(71, 85, 105, 0.5); color: #d1d5db; padding: 12px 24px; border-radius: 8px; border: 1px solid #374151; cursor: pointer; font-weight: 500;">Fechar</button>
                <button onclick="acceptTerms()" style="background: linear-gradient(135deg, #8b5cf6, #ec4899); color: white; padding: 12px 24px; border-radius: 8px; border: none; cursor: pointer; font-weight: 600;">Aceito os Termos</button>
            </div>
        </div>
    </div>

    <script>
        const cacheVersion = '{current_version}';
        console.log('✅ TEST ROUTE: Signup page loaded - Terms Modal ' + cacheVersion + ' activated');
        
        function testModal() {{
            document.getElementById('testResult').textContent = '✅ Modal testado com sucesso!';
            document.getElementById('testResult').style.display = 'block';
            openTermsModal();
        }}

        window.openTermsModal = function() {{
            console.log('🔓 Opening terms modal - TEST ROUTE');
            const modal = document.getElementById('termsModal');
            if (modal) {{
                modal.classList.remove('hidden');
                modal.style.display = 'flex !important';
                modal.style.visibility = 'visible !important';
                modal.style.opacity = '1 !important';
                modal.style.zIndex = '99999 !important';
                console.log('✅ Modal display set to flex - should be visible now');
            }} else {{
                console.error('❌ Modal element not found!');
            }}
        }};

        window.closeTermsModal = function() {{
            console.log('🔒 Closing terms modal - TEST ROUTE');
            const modal = document.getElementById('termsModal');
            if (modal) {{
                modal.classList.add('hidden');
                modal.style.display = 'none !important';
                modal.style.visibility = 'hidden !important';
                modal.style.opacity = '0 !important';
                console.log('✅ Modal display set to none');
            }}
        }};

        window.acceptTerms = function() {{
            document.getElementById('terms').checked = true;
            document.getElementById('testResult').textContent = '✅ Termos aceitos com sucesso!';
            window.closeTermsModal();
        }};

        document.addEventListener('DOMContentLoaded', function() {{
            console.log('DOM fully loaded - TEST ROUTE');
            console.log('openTermsModal function:', typeof window.openTermsModal);
        }});
    </script>
</body>
</html>"""
    
    response = HTMLResponse(content=signup_html)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.get("/test-modal", response_class=HTMLResponse)
async def test_modal(request: Request):
    """Serve test modal page"""
    test_path = os.path.join(os.getcwd(), "test_modal.html")
    if os.path.exists(test_path):
        with open(test_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h2>Página de teste não encontrada</h2>", status_code=404)


@app.get("/dashboard")
async def dashboard():
    """Serve the functional dashboard after login"""
    dashboard_path = os.path.join(frontend_path, "dashboard-functional.html")
    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r", encoding="utf-8") as f:
            content = f.read()
        from fastapi.responses import HTMLResponse
        return HTMLResponse(
            content=content,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            }
        )
    return {"error": "Dashboard not found"}


# ⚠️ REMOVED: Duplicate route for "/" - now handled by home_page() above
# This was causing the new home.html route to be overridden


@app.get("/status")
async def status():
    """API endpoint para status da aplicação"""
    db_status = "unknown"
    try:
        from vexus_crm.database import get_db
        db = next(get_db())
        db.execute("SELECT 1")
        db_status = "healthy"
        db.close()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "online",
        "service": "Vexus CRM API",
        "version": settings.APP_VERSION if settings else "1.0.0",
        "environment": settings.ENVIRONMENT if settings else "development",
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
        "features": {
            "authentication": True,
            "leads_management": True,
            "campaigns": True,
            "analytics": True,
            "whatsapp_integration": True,
            "ai_agents": True,
            "knowledge_lab": True
        }
    }


# Enhanced health check
@app.get("/health")
async def health_check():
    """Detailed health check for monitoring systems"""
    checks = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.APP_VERSION if settings else "1.0.0",
        "checks": {}
    }

    # Database check
    try:
        from vexus_crm.database import get_db
        db = next(get_db())
        db.execute("SELECT COUNT(*) FROM users")
        db.close()
        checks["checks"]["database"] = {"status": "healthy", "details": "Connected"}
    except Exception as e:
        checks["checks"]["database"] = {"status": "unhealthy", "details": str(e)}
        checks["status"] = "unhealthy"

    return checks


# Metrics endpoint for monitoring
@app.get("/metrics")
async def metrics():
    """Prometheus-style metrics endpoint"""
    if not (settings and settings.ENABLE_METRICS):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Metrics not enabled")

    from fastapi.responses import Response

    metrics_data = f"""# Vexus CRM Metrics
# Generated at {datetime.now().isoformat()}
"""

    return Response(content=metrics_data, media_type="text/plain")


# Public routes for admin portal
@app.get("/login")
async def login_page():
    """Página de Login/Registro"""
    from vexus_crm.admin.routes import LOGIN_HTML
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=LOGIN_HTML)

@app.get("/dashboard")
async def dashboard_page():
    """Painel de Controle do Cliente"""
    from vexus_crm.admin.routes import DASHBOARD_HTML
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=DASHBOARD_HTML)


# SPA fallback route DISABLED - removed to prevent catching "/" path
# This was causing "/" to serve index.html instead of home.html
# The root_home() function now handles "/" properly above


# 404 Handler
@app.exception_handler(404)
async def not_found(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Rota não encontrada",
            "path": str(request.url),
            "available_docs": "/docs",
        },
    )

# Global exception handler (debugging)
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback

    tb = traceback.format_exc()
    logger.error("Unhandled exception: %s", exc)
    logger.error(tb)
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "trace": tb,
        },
    )


# ensure database tables exist when running directly
if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting Vexus CRM API...")
    port = int(os.environ.get("PORT", 8000))
    print(f"📡 Listening on port {port}")

    uvicorn.run(
        "app_server:app", host="0.0.0.0", port=port, reload=False, log_level="info"
    )
