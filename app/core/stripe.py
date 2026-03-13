"""
Integração com Stripe para pagamentos recorrentes (SaaS)
"""

import stripe
import logging
from typing import Optional

# Pydantic v1: BaseSettings está no próprio pydantic
from pydantic import BaseSettings

logger = logging.getLogger(__name__)


class StripeSettings(BaseSettings):
    """Configuração do Stripe"""

    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PRICE_STARTER: Optional[str] = None  # Ex: price_1234xyz
    STRIPE_PRICE_PROFESSIONAL: Optional[str] = None
    STRIPE_PRICE_BUSINESS: Optional[str] = None

    # Pydantic v2 configuration
    model_config = {
        "extra": "ignore",
        # Load from the production env file if present
        "env_file": ".env.production",
    }


stripe_settings = StripeSettings()

# Configurar API key
if stripe_settings.STRIPE_SECRET_KEY:
    stripe.api_key = stripe_settings.STRIPE_SECRET_KEY


async def create_checkout_session(
    customer_email: str,
    price_id: str,
    company_id: str,
    success_url: str,
    cancel_url: str,
) -> Optional[str]:
    """
    Criar sessão de checkout no Stripe

    Returns:
        URL da sessão de checkout (para redirecionar usuário)
    """

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            customer_email=customer_email,
            line_items=[{"price": price_id, "quantity": 1}],
            metadata={"company_id": company_id},
            success_url=success_url,
            cancel_url=cancel_url,
        )

        logger.info(f"Sessão de checkout criada: {session.id}")
        return session.url

    except Exception as e:
        logger.error(f"Erro ao criar sessão de checkout: {str(e)}")
        return None


async def handle_webhook(
    payload: bytes,
    sig_header: str,
) -> dict:
    """
    Processar webhook do Stripe

    Eventos importantes:
    - checkout.session.completed: Assinatura criada com sucesso
    - customer.subscription.updated: Plano alterado
    - customer.subscription.deleted: Assinatura cancelada
    - invoice.payment_succeeded: Pagamento recebido
    - invoice.payment_failed: Pagamento falhou
    """

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Webhook payload inválido: {str(e)}")
        return {"status": "error", "message": "Invalid payload"}
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Assinatura de webhook inválida: {str(e)}")
        return {"status": "error", "message": "Invalid signature"}

    # Processar eventos
    event_type = event["type"]
    event_data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        # Novo cliente subscreveu
        company_id = event_data.get("metadata", {}).get("company_id")
        subscription_id = event_data.get("subscription")
        customer_id = event_data.get("customer")

        logger.info(f"Checkout completo: company={company_id}, sub={subscription_id}")
        # TODO: Atualizar company no banco com subscription_id e status='active'
        # await update_company_subscription(company_id, subscription_id, customer_id)

    elif event_type == "invoice.payment_succeeded":
        # Pagamento recebido
        subscription_id = event_data.get("subscription")
        logger.info(f"Pagamento recebido: sub={subscription_id}")

    elif event_type == "invoice.payment_failed":
        # Pagamento falhou
        subscription_id = event_data.get("subscription")
        logger.warning(f"Pagamento falhou: sub={subscription_id}")

    elif event_type == "customer.subscription.deleted":
        # Assinatura cancelada
        subscription_id = event_data.get("id")
        logger.info(f"Assinatura cancelada: {subscription_id}")
        # TODO: Atualizar company com status='cancelled'

    return {"status": "success"}


def get_customer_subscriptions(customer_id: str) -> list:
    """Obter todas as assinaturas de um cliente"""
    try:
        subscriptions = stripe.Subscription.list(
            customer=customer_id, status="all", limit=100
        )
        return subscriptions.get("data", [])
    except Exception as e:
        logger.error(f"Erro ao listar assinaturas: {str(e)}")
        return []


async def cancel_subscription(subscription_id: str) -> bool:
    """Cancelar assinatura"""
    try:
        stripe.Subscription.delete(subscription_id)
        logger.info(f"Assinatura cancelada: {subscription_id}")
        return True
    except Exception as e:
        logger.error(f"Erro ao cancelar assinatura: {str(e)}")
        return False
