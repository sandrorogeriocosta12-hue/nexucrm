"""
Vexus CRM - Minimal Test Server for Railway
"""

from fastapi import FastAPI
import os
from datetime import datetime

# Criar app FastAPI minimal
app = FastAPI(
    title="Vexus CRM Test",
    openapi_url=None,
    docs_url=None,
    redoc_url=None
)

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Vexus CRM Test API",
        "timestamp": datetime.now().isoformat(),
        "port": os.environ.get("PORT", "8000")
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Test server starting on port {port}")
    uvicorn.run("app_test:app", host="0.0.0.0", port=port)