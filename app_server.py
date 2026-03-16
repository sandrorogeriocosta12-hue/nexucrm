"""
Vexus CRM - FastAPI Main Server
Integra: Knowledge Lab, Proposal Generator, Chat, Analytics
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Criar app FastAPI
app = FastAPI(
    title="Vexus CRM API",
    description="Plataforma de CRM inteligente com IA, RAG e Automação de Vendas",
    version="1.0.0",
    openapi_url=None,  # Disable OpenAPI schema generation to avoid Pydantic V2 issues
    docs_url=None,     # Disable docs
    redoc_url=None,    # Disable redoc
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção: ["https://yourdomain.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# create database tables on startup
@app.on_event("startup")
async def startup_db():
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
            
            test_user = db.query(User).filter(User.email == "test@vexus.com").first()
            if not test_user:
                hashed_password = get_password_hash("test123")
                test_user = User(
                    id="test-user-id",
                    email="test@vexus.com",
                    name="Test User",
                    password_hash=hashed_password,
                    role="user",
                    is_active=True
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


# Rota raiz - Healthcheck simples para Railway
@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Vexus CRM API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


# Mount static files (frontend)
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_path):
    app.mount("/frontend", StaticFiles(directory=frontend_path), name="frontend")
    logger.info(f"✓ Frontend mounted at /frontend from {frontend_path}")


# Dashboard route
@app.get("/dashboard")
async def dashboard():
    """Serve the JWT-authenticated dashboard"""
    dashboard_path = os.path.join(frontend_path, "dashboard-jwt.html")
    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r", encoding="utf-8") as f:
            content = f.read()
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=content)
    return {"error": "Dashboard not found"}


# Health check - SIMPLIFIED for Railway
@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "service": "Vexus CRM API"}


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


# ensure database tables exist when running directly
if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting Vexus CRM API...")
    port = int(os.environ.get("PORT", 8000))
    print(f"📡 Listening on port {port}")

    uvicorn.run(
        "app_server:app", host="0.0.0.0", port=port, reload=False, log_level="info"
    )
