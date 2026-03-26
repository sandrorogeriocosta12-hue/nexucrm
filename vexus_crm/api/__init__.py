"""
Vexus CRM API
REST API endpoints for the application
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["api"])

__all__ = ["router"]
