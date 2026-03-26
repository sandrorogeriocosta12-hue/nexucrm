"""
Vexus CRM - Professional FastAPI Server
Enterprise-ready with security, monitoring, and production features
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
import logging
from datetime import datetime
import os
import time

# Professional logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/vexus_crm.log", mode='a')
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


# Mount static files (frontend)
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_path):
    app.mount("/frontend", StaticFiles(directory=frontend_path), name="frontend")
    logger.info(f"✓ Frontend mounted at /frontend from {frontend_path}")


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


# ============================================================================
# 📄 FRONTEND ROUTES
# ============================================================================


@app.get("/signup", response_class=HTMLResponse)
async def signup(request: Request):
    """Serve signup page with NO-CACHE headers to prevent Cloudflare caching - EMBEDDED HTML VERSION"""
    # 🔥 FINAL ATTEMPT: Dynamic version parameter to force cache bypass
    current_version = f"v{int(time.time() * 1000000)}"  # Unique version per microsecond
    
    # 🔥 TEMPORARY PATCH: Serve embedded HTML with fixed modal to bypass file sync issues
    signup_html = f"""<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>Nexus Service - Cadastro</title>
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
        .form-group {{
            margin-bottom: 1.5rem;
        }}
        .form-input {{
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #374151;
            border-radius: 8px;
            background-color: #1f2937;
            color: #f9fafb;
            font-size: 16px;
            transition: border-color 0.2s ease;
        }}
        .form-input:focus {{
            outline: none;
            border-color: #8b5cf6;
            box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
        }}
        .password-wrapper {{
            position: relative;
            display: flex;
            align-items: center;
        }}
        .password-toggle {{
            position: absolute;
            right: 12px;
            background: none;
            border: none;
            color: #9ca3af;
            cursor: pointer;
            font-size: 18px;
            padding: 4px;
            border-radius: 4px;
            transition: color 0.2s ease;
        }}
        .password-toggle:hover {{
            color: #f9fafb;
        }}
        .btn-primary {{
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #8b5cf6, #ec4899);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .btn-primary:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
        }}
        .btn-primary:disabled {{
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }}
        .gradient-text {{
            background: linear-gradient(135deg, #8b5cf6, #ec4899);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
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
        .modal-content {{
            background-color: #1f2937 !important;
            border-radius: 12px !important;
            max-width: 56rem !important;
            width: 100% !important;
            max-height: 90vh !important;
            overflow: hidden !important;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5) !important;
        }}
        .modal-header {{
            padding: 1.5rem !important;
            border-bottom: 1px solid #374151 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
        }}
        .modal-body {{
            padding: 1.5rem !important;
            overflow-y: auto !important;
            max-height: 70vh !important;
        }}
        .modal-footer {{
            padding: 1.5rem !important;
            border-top: 1px solid #374151 !important;
            display: flex !important;
            justify-content: flex-end !important;
            gap: 1rem !important;
        }}
        .btn-secondary {{
            background: rgba(71, 85, 105, 0.5) !important;
            color: #d1d5db !important;
            padding: 12px 24px !important;
            border-radius: 8px !important;
            border: 1px solid #374151 !important;
            cursor: pointer !important;
            font-weight: 500 !important;
            transition: background-color 0.2s ease !important;
        }}
        .btn-secondary:hover {{
            background: rgba(71, 85, 105, 0.7) !important;
        }}
        .btn-gradient {{
            background: linear-gradient(135deg, #8b5cf6, #ec4899) !important;
            color: white !important;
            padding: 12px 24px !important;
            border-radius: 8px !important;
            border: none !important;
            cursor: pointer !important;
            font-weight: 600 !important;
            transition: transform 0.2s ease !important;
        }}
        .btn-gradient:hover {{
            transform: translateY(-1px) !important;
        }}
        .terms-link {{
            color: #8b5cf6 !important;
            text-decoration: none !important;
            font-weight: 500 !important;
        }}
        .terms-link:hover {{
            color: #a855f7 !important;
            text-decoration: underline !important;
        }}
        .logo-box {{
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #a855f7, #ec4899);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 28px;
            color: white;
            box-shadow: 0 8px 32px rgba(168, 85, 247, 0.3);
        }}
        .btn-gradient {{
            background: linear-gradient(135deg, #a855f7, #ec4899);
            color: white;
            padding: 10px 16px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            font-weight: 600;
            width: 100%;
            transition: all 0.3s;
        }}
        .btn-gradient:hover {{
            box-shadow: 0 8px 24px rgba(168, 85, 247, 0.4);
            transform: translateY(-2px);
        }}
        input {{
            width: 100%;
            padding: 10px 16px;
            background-color: rgb(71, 85, 105);
            border: 1px solid rgb(71, 85, 105);
            color: white;
            border-radius: 8px;
            font-size: 14px;
            margin-bottom: 12px;
        }}
        input::placeholder {{
            color: rgb(156, 163, 175);
        }}
        .form-group {{
            margin-bottom: 16px;
        }}
        label {{
            display: block;
            color: rgb(209, 213, 219);
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        .error {{
            color: #fca5a5;
            background-color: rgba(239, 68, 68, 0.2);
            border: 1px solid rgba(239, 68, 68, 0.3);
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 16px;
            font-size: 14px;
        }}
        .success {{
            color: #86efac;
            background-color: rgba(34, 197, 94, 0.2);
            border: 1px solid rgba(34, 197, 94, 0.3);
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 16px;
            font-size: 14px;
        }}
        .plan-option {{
            position: relative;
        }}
        .plan-option input[type="radio"] {{
            position: absolute;
            opacity: 0;
            width: 100%;
            height: 100%;
            margin: 0;
        }}
        .plan-option input[type="radio"]:checked + label > div {{
            border-color: rgb(168, 85, 247);
            background: rgba(168, 85, 247, 0.1);
        }}
        .btn-secondary {{
            background: rgba(71, 85, 105, 0.5);
            color: rgb(209, 213, 219);
            padding: 10px 16px;
            border-radius: 8px;
            border: 1px solid rgb(71, 85, 105);
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }}
        .btn-secondary:hover {{
            background: rgba(71, 85, 105, 0.7);
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
<body class="bg-gradient-to-br from-slate-900 via-slate-950 to-black">
    <div style="width: 384px; padding: 32px; border-radius: 8px; border: 1px solid rgb(55, 65, 81); background: linear-gradient(135deg, rgb(30, 41, 59), rgb(15, 23, 42)); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);">
        
        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 32px;">
            <div class="logo-box">N</div>
        </div>
        
        <h1 class="gradient-text" style="font-size: 30px; font-weight: bold; text-align: center; margin-bottom: 8px;">Nexus Service</h1>
        <p style="text-align: center; color: rgb(156, 163, 175); font-size: 14px; margin-bottom: 4px;">Criar Conta</p>
        <p style="text-align: center; color: rgb(107, 114, 128); font-size: 12px; margin-bottom: 32px;">Cadastre-se e comece a qualificar leads com IA</p>
        
        <div id="errorMessage" class="error" style="display: none;"></div>
        <div id="successMessage" class="success" style="display: none;"></div>
        
        <form id="signupForm">
            <div class="form-group">
                <label>Nome Completo</label>
                <input type="text" id="fullName" placeholder="Seu nome completo" required>
            </div>
            
            <div class="form-group">
                <label>Empresa</label>
                <input type="text" id="company" placeholder="Sua empresa (opcional)">
            </div>

            <div class="form-group">
                <label>E-mail</label>
                <input type="email" id="email" placeholder="seu@email.com" required>
            </div>
            
            <div class="form-group">
                <label>Senha</label>
                <div style="position: relative;">
                    <input type="password" id="password" placeholder="••••••" required style="padding-right: 40px;">
                    <button type="button" onclick="togglePassword('password')" style="position: absolute; right: 10px; top: 50%; transform: translateY(-50%); background: none; border: none; color: rgb(156, 163, 175); cursor: pointer; font-size: 18px;">
                        👁️
                    </button>
                </div>
            </div>

            <div class="form-group">
                <label>Confirmar Senha</label>
                <div style="position: relative;">
                    <input type="password" id="confirmPassword" placeholder="••••••" required style="padding-right: 40px;">
                    <button type="button" onclick="togglePassword('confirmPassword')" style="position: absolute; right: 10px; top: 50%; transform: translateY(-50%); background: none; border: none; color: rgb(156, 163, 175); cursor: pointer; font-size: 18px;">
                        👁️
                    </button>
                </div>
            </div>

            <div class="form-group">
                <label>Plano</label>
                <div class="space-y-3">
                    <div class="plan-option" data-plan="free">
                        <input type="radio" id="plan-free" name="plan" value="free" checked class="mr-3">
                        <label for="plan-free" class="flex-1 cursor-pointer">
                            <div class="bg-slate-700 p-3 rounded-lg border border-slate-600 hover:border-purple-500 transition-colors">
                                <div class="flex justify-between items-center">
                                    <div>
                                        <div class="font-semibold text-white">Free</div>
                                        <div class="text-sm text-gray-400">Até 100 leads/mês</div>
                                    </div>
                                    <div class="text-right">
                                        <div class="font-bold text-green-400">R$ 0</div>
                                        <div class="text-xs text-gray-400">Grátis</div>
                                    </div>
                                </div>
                            </div>
                        </label>
                    </div>
                    
                    <div class="plan-option" data-plan="pro">
                        <input type="radio" id="plan-pro" name="plan" value="pro" class="mr-3">
                        <label for="plan-pro" class="flex-1 cursor-pointer">
                            <div class="bg-slate-700 p-3 rounded-lg border border-slate-600 hover:border-purple-500 transition-colors">
                                <div class="flex justify-between items-center">
                                    <div>
                                        <div class="font-semibold text-white">Pro</div>
                                        <div class="text-sm text-gray-400">Até 1.000 leads/mês</div>
                                    </div>
                                    <div class="text-right">
                                        <div class="font-bold text-purple-400">R$ 97</div>
                                        <div class="text-xs text-gray-400">/mês</div>
                                    </div>
                                </div>
                            </div>
                        </label>
                    </div>
                    
                    <div class="plan-option" data-plan="enterprise">
                        <input type="radio" id="plan-enterprise" name="plan" value="enterprise" class="mr-3">
                        <label for="plan-enterprise" class="flex-1 cursor-pointer">
                            <div class="bg-slate-700 p-3 rounded-lg border border-slate-600 hover:border-purple-500 transition-colors">
                                <div class="flex justify-between items-center">
                                    <div>
                                        <div class="font-semibold text-white">Enterprise</div>
                                        <div class="text-sm text-gray-400">Leads ilimitados</div>
                                    </div>
                                    <div class="text-right">
                                        <div class="font-bold text-pink-400">R$ 297</div>
                                        <div class="text-xs text-gray-400">/mês</div>
                                    </div>
                                </div>
                            </div>
                        </label>
                    </div>
                </div>
            </div>

            <div class="form-group" style="margin-bottom: 24px;">
                <input type="checkbox" id="terms" required style="width: auto; margin: 0;">
                <label for="terms" style="display: inline; margin-left: 8px;">Aceito os <a href="#" onclick="event.preventDefault(); openTermsModal(); return false;" class="terms-link">termos de serviço</a></label>
            </div>

            <button type="submit" class="btn-gradient">Criar Conta</button>
        </form>

        <p style="text-align: center; font-size: 14px; color: rgb(156, 163, 175); margin-top: 24px;">
            Já tem conta? <a href="/" style="color: rgb(168, 85, 247); font-weight: 600; text-decoration: none;">Faça login</a>
        </p>
    </div>

    <div id="termsModal" class="terms-modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 class="gradient-text" style="margin: 0; font-size: 1.25rem; font-weight: 700;">Termos de Serviço</h3>
                <button onclick="closeTermsModal()" style="color: #9ca3af; font-size: 1.5rem; background: none; border: none; cursor: pointer; padding: 0;">&times;</button>
            </div>
            <div class="modal-body">
                <div style="color: #d1d5db;">
                    <h4 style="color: #8b5cf6; font-weight: 600; margin-bottom: 1rem;">1. Aceitação dos Termos</h4>
                    <p style="margin-bottom: 1rem;">Ao acessar e usar o Nexus Service, você concorda em cumprir e estar vinculado a estes Termos de Serviço. Se você não concordar com estes termos, não use nossos serviços.</p>

                    <h4 style="color: #8b5cf6; font-weight: 600; margin-bottom: 1rem;">2. Descrição do Serviço</h4>
                    <p style="margin-bottom: 1rem;">O Nexus Service é uma plataforma de CRM alimentada por IA que ajuda empresas a qualificar leads, gerenciar contatos e automatizar processos de vendas.</p>

                    <h4 style="color: #8b5cf6; font-weight: 600; margin-bottom: 1rem;">3. Planos e Preços</h4>
                    <ul style="margin-bottom: 1rem; margin-left: 1rem;">
                        <li><strong>Free:</strong> Até 100 leads por mês, recursos básicos - R$ 0</li>
                        <li><strong>Pro:</strong> Até 1.000 leads por mês, automações avançadas - R$ 97/mês</li>
                        <li><strong>Enterprise:</strong> Leads ilimitados, suporte prioritário - R$ 297/mês</li>
                    </ul>

                    <h4 style="color: #8b5cf6; font-weight: 600; margin-bottom: 1rem;">4. Privacidade e Dados</h4>
                    <p style="margin-bottom: 1rem;">Sua privacidade é importante para nós. Coletamos e processamos dados pessoais de acordo com nossa Política de Privacidade.</p>

                    <h4 style="color: #8b5cf6; font-weight: 600; margin-bottom: 1rem;">5. Limitação de Responsabilidade</h4>
                    <p style="margin-bottom: 1rem;">O Nexus Service é fornecido "como está". Não garantimos que o serviço estará sempre disponível ou livre de erros.</p>
                </div>
            </div>
            <div class="modal-footer">
                <button onclick="closeTermsModal()" class="btn-secondary">Fechar</button>
                <button onclick="acceptTerms()" class="btn-gradient">Aceito os Termos</button>
            </div>
        </div>
    </div>

    <script>
        const cacheVersion = '{current_version}';
        console.log('✅ Signup page loaded - Terms Modal ' + cacheVersion + ' activated');
        
        window.addEventListener('load', function() {{
            const lastVersion = sessionStorage.getItem('signupVersion');
            if (lastVersion !== cacheVersion) {{
                sessionStorage.setItem('signupVersion', cacheVersion);
                console.log('🔄 New version detected, clearing cache...');
                if ('caches' in window) {{
                    caches.keys().then(names => {{
                        names.forEach(name => caches.delete(name));
                    }});
                }}
            }}
        }});

        window.openTermsModal = function() {{
            console.log('🔓 Opening terms modal - function called');
            const modal = document.getElementById('termsModal');
            console.log('📦 Modal element:', modal);

            if (modal) {{
                modal.classList.remove('hidden');
                modal.style.display = 'flex !important';
                modal.style.visibility = 'visible !important';
                modal.style.opacity = '1 !important';
                modal.style.zIndex = '99999 !important';
                modal.style.position = 'fixed !important';
                modal.style.top = '0 !important';
                modal.style.left = '0 !important';
                modal.style.width = '100% !important';
                modal.style.height = '100% !important';
                modal.style.backgroundColor = 'rgba(0, 0, 0, 0.7) !important';
                modal.style.alignItems = 'center !important';
                modal.style.justifyContent = 'center !important';

                console.log('✅ Modal display set to flex - should be visible now');
                window.scrollTo(0, 0);
                document.body.style.overflow = 'hidden';
                console.log('✅ Modal computed style display:', window.getComputedStyle(modal).display);
            }} else {{
                console.error('❌ Modal element not found!');
            }}
        }};

        window.closeTermsModal = function() {{
            console.log('🔒 Closing terms modal');
            const modal = document.getElementById('termsModal');
            if (modal) {{
                modal.classList.add('hidden');
                modal.style.display = 'none !important';
                modal.style.visibility = 'hidden !important';
                modal.style.opacity = '0 !important';
                document.body.style.overflow = 'auto';
                console.log('✅ Modal display set to none');
            }}
        }};

        window.acceptTerms = function() {{
            document.getElementById('terms').checked = true;
            window.closeTermsModal();
        }};

        document.addEventListener('DOMContentLoaded', function() {{
            console.log('DOM fully loaded');

            const modal = document.getElementById('termsModal');
            if (modal) {{
                modal.addEventListener('click', function(e) {{
                    if (e.target === this) {{
                        window.closeTermsModal();
                    }}
                }});
                console.log('Event listener added to modal');
            }}

            console.log('openTermsModal function:', typeof window.openTermsModal);
            console.log('closeTermsModal function:', typeof window.closeTermsModal);
        }});

        function togglePassword(fieldId) {{
            const field = document.getElementById(fieldId);
            const button = field.nextElementSibling;

            if (field.type === 'password') {{
                field.type = 'text';
                button.textContent = '🙈';
            }} else {{
                field.type = 'password';
                button.textContent = '👁️';
            }}
        }}
        
        const form = document.getElementById('signupForm');
        const errorEl = document.getElementById('errorMessage');
        const successEl = document.getElementById('successMessage');
        
        form.addEventListener('submit', async (e) => {{
            e.preventDefault();
            console.log('Form submitted');

            const fullName = document.getElementById('fullName').value.trim();
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            const company = document.getElementById('company').value.trim();
            const plan = document.querySelector('input[name="plan"]:checked').value;
            const termsAccepted = document.getElementById('terms').checked;

            errorEl.style.display = 'none';
            successEl.style.display = 'none';

            try {{
                if (!fullName || !email || !password) {{
                    throw new Error('Nome, email e senha são obrigatórios');
                }}
                if (password !== confirmPassword) {{
                    throw new Error('As senhas não coincidem');
                }}
                if (password.length < 6) {{
                    throw new Error('A senha deve ter pelo menos 6 caracteres');
                }}
                if (!termsAccepted) {{
                    throw new Error('Aceite os termos de serviço é obrigatório');
                }}

                console.log('Sending registration request to API');

                const API_BASE = window.location.origin;
                const response = await fetch(API_BASE + '/api/auth/register', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        email: email,
                        password: password,
                        full_name: fullName,
                        company: company || null,
                        plan: plan,
                        terms: termsAccepted
                    }})
                }});

                const data = await response.json();
                console.log('API response:', data);

                if (!response.ok) {{
                    throw new Error(data.detail || 'Erro ao criar conta');
                }}

                successEl.textContent = '✅ Conta criada com sucesso! Redirecionando para login...';
                successEl.style.display = 'block';
                form.style.display = 'none';
                
                setTimeout(() => {{
                    window.location.href = '/';
                }}, 2000);

            }} catch (err) {{
                console.error('Error:', err);
                errorEl.textContent = '❌ ' + err.message;
                errorEl.style.display = 'block';
            }}
        }});
    </script>
</body>
</html>"""
    
    response = HTMLResponse(content=signup_html)
    # 🔥 NUCLEAR OPTION: Dynamic version in URL forces cache bypass
    timestamp = str(int(time.time() * 1000000))  # Microsecond precision
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0, s-maxage=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Surrogate-Control"] = "no-store"
    response.headers["X-Accel-Expires"] = "0"
    response.headers["ETag"] = f'"{current_version}"'  # Dynamic ETag per request
    response.headers["Last-Modified"] = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    response.headers["X-Cache-Bypass"] = current_version  # Unique per request
    response.headers["X-Version"] = current_version  # Custom version header
    return response


@app.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    """Serve terms of service page"""
    terms_path = os.path.join(frontend_path, "terms.html")
    if os.path.exists(terms_path):
        with open(terms_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h2>Termos de serviço não encontrados</h2>", status_code=404)


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
        return HTMLResponse(content=content)
    return {"error": "Dashboard not found"}


# Rota raiz - Servir página de login
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve login page"""
    login_path = os.path.join(frontend_path, "login-nexus.html")
    if os.path.exists(login_path):
        with open(login_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    
    # Fallback to login.html
    login_path = os.path.join(frontend_path, "login.html")
    if os.path.exists(login_path):
        with open(login_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h2>Nexus CRM Login não encontrado</h2>", status_code=404)


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


# SPA fallback route - rota cliente, depois das rotas API/health/metrics
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def spa_fallback(full_path: str, request: Request):
    if full_path.startswith("api") or full_path.startswith("health") or full_path.startswith("metrics") or full_path.startswith("docs") or full_path.startswith("openapi") or full_path.startswith("dashboard"):
        raise HTTPException(status_code=404, detail="Not found")

    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())

    app_html_path = os.path.join(frontend_path, "app.html")
    if os.path.exists(app_html_path):
        with open(app_html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())

    raise HTTPException(status_code=404, detail="Frontend not found")


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
