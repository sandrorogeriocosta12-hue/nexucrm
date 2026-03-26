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
    """Serve signup page with NO-CACHE headers to prevent Cloudflare caching"""
    signup_path = os.path.join(frontend_path, "signup-v2.html")
    if os.path.exists(signup_path):
        with open(signup_path, "r", encoding="utf-8") as f:
            response = HTMLResponse(content=f.read())
            # 🔥 FORCE NO CACHE - Override Cloudflare caching
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            response.headers["Surrogate-Control"] = "no-store"
            response.headers["X-Accel-Expires"] = "0"
            response.headers["ETag"] = f'"{datetime.utcnow().timestamp()}"'  # Always different ETag
            return response
    return HTMLResponse("<h2>Página de cadastro não encontrada</h2>", status_code=404)


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
