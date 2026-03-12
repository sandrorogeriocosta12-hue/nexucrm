"""
Configuração de Sentry para monitoramento de erros em produção
"""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def init_sentry(dsn: Optional[str] = None, environment: str = "production") -> None:
    """
    Inicializar Sentry para captura de erros

    Args:
        dsn: Sentry DSN (https://xxx@xxx.ingest.sentry.io/xxx)
        environment: Ambiente (production, staging, development)
    """

    if not dsn:
        logger.warning("Sentry DSN não configurado - monitoramento desativado")
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        # Capturar 10% das transações (ajustar conforme carga)
        traces_sample_rate=0.1,
        # Integrations
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            LoggingIntegration(
                level=logging.INFO,  # Capturar INFO e acima
                event_level=logging.ERROR,  # Enviar apenas ERROR para Sentry
            ),
        ],
        # Aumentar contexto capturado
        include_source_context=True,
        include_local_variables=False,  # Cuidado com senhas/tokens
        max_breadcrumbs=50,
    )

    logger.info(f"Sentry inicializado para ambiente: {environment}")


def capture_exception(exception: Exception, extra_context: dict = None) -> None:
    """
    Capturar exceção manualmente

    Args:
        exception: Exceção a capturar
        extra_context: Contexto adicional
    """

    if extra_context:
        sentry_sdk.set_context("extra", extra_context)

    sentry_sdk.capture_exception(exception)


def set_user_context(user_id: str, email: str = None, company_id: str = None) -> None:
    """
    Definir contexto do usuário para melhor rastreamento

    Args:
        user_id: ID do usuário
        email: Email do usuário
        company_id: ID da empresa (para multi-tenant)
    """

    sentry_sdk.set_user(
        {
            "id": user_id,
            "email": email,
            "company_id": company_id,
        }
    )
