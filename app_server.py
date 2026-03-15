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
        from vexus_crm.database import engine
        from vexus_crm import models

        models.Base.metadata.create_all(bind=engine)
        logger.info("✓ Database schema ensured")
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
