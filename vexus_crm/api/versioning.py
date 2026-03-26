"""
🔀 API VERSIONING
Suporte para múltiplas versões de API simultaneamente
"""

from fastapi import APIRouter, FastAPI, Header, HTTPException, __version__ as fastapi_version
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class APIVersion:
    """Gerenciador de versões de API"""
    
    V1 = "v1"
    V2 = "v2"
    CURRENT = V1
    
    SUPPORTED_VERSIONS = [V1, V2]
    
    VERSION_FEATURES = {
        "v1": {
            "endpoints": ["users", "contacts", "campaigns"],
            "deprecated": False,
            "sunset_date": None,
        },
        "v2": {
            "endpoints": ["users", "contacts", "campaigns", "webhooks", "analytics"],
            "features": ["advanced_filtering", "bulk_operations", "webhooks"],
            "deprecated": False,
            "sunset_date": None,
        }
    }


def get_api_version(
    api_version: Optional[str] = Header(None)
) -> str:
    """
    Extrai versão da API do header
    
    Header: X-API-Version: v1
    """
    if api_version is None:
        return APIVersion.V1
    
    if api_version not in APIVersion.SUPPORTED_VERSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Versão não suportada. Versões suportadas: {APIVersion.SUPPORTED_VERSIONS}"
        )
    
    return api_version


def setup_api_versioning(app: FastAPI):
    """Configura roteamento por versão de API"""
    
    # Rota raiz com informações de versão
    @app.get("/api/version")
    async def api_version_info():
        """Informações sobre versões de API"""
        return {
            "current_version": APIVersion.CURRENT,
            "supported_versions": APIVersion.SUPPORTED_VERSIONS,
            "features_by_version": APIVersion.VERSION_FEATURES,
            "fastapi_version": fastapi_version,
        }
    
    logger.info("✅ API Versioning configurado")


# Exemplo de uso em rotas
"""
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/api/v1/users")
async def list_users_v1(api_version: str = Depends(get_api_version)):
    '''Lista usuários (versão 1 - simples)'''
    return {"version": api_version, "users": []}

@router.get("/api/v2/users")
async def list_users_v2(
    api_version: str = Depends(get_api_version),
    filter: Optional[str] = None,
    sort: Optional[str] = None,
):
    '''
    Lista usuários (versão 2 - com filtros avançados)
    
    Novos recursos na v2:
    - Filtros avançados
    - Ordenação customizável
    - Paginação melhorada
    - Webhooks
    '''
    return {
        "version": api_version,
        "users": [],
        "filter": filter,
        "sort": sort
    }
"""
