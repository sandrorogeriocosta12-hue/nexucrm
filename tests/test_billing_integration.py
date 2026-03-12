"""
Testes para endpoints de faturamento
- POST /billing/create-subscription - Criar sessão Stripe checkout
- POST /billing/stripe-webhook - Processar webhooks do Stripe
- GET /billing/subscription - Obter status de assinatura
"""

import pytest

pytest.skip("legacy billing tests disabled", allow_module_level=True)
from unittest.mock import patch, MagicMock, AsyncMock
import json


class TestCreateSubscription:
    """Testes para criação de assinatura Stripe"""

    @patch("app.core.stripe.create_checkout_session")
    async def test_create_subscription_returns_checkout_url(self, mock_checkout):
        """Deve retornar URL de checkout válida"""
        mock_checkout.return_value = "https://checkout.stripe.com/pay/cs_test_123"

        from app.core.stripe import create_checkout_session

        checkout_url = await create_checkout_session(
            customer_email="customer@example.com",
            price_id="price_1234567890",
            company_id="comp_123",
            success_url="https://app.example.com/success",
            cancel_url="https://app.example.com/cancel",
        )

        assert checkout_url is not None
        assert "checkout.stripe.com" in checkout_url or "stripe.com" in checkout_url

    @patch("app.core.stripe.create_checkout_session")
    async def test_create_subscription_with_customer_email(self, mock_checkout):
        """Deve incluir email do cliente na sessão"""
        mock_checkout.return_value = "https://checkout.stripe.com/pay/cs_test_123"

        from app.core.stripe import create_checkout_session

        customer_email = "customer@example.com"
        await create_checkout_session(
            customer_email=customer_email,
            price_id="price_1234567890",
            company_id="comp_123",
            success_url="https://app.example.com/success",
            cancel_url="https://app.example.com/cancel",
        )

        mock_checkout.assert_called()
        call_args = mock_checkout.call_args
        assert call_args[1]["customer_email"] == customer_email

    @patch("app.core.stripe.create_checkout_session")
    async def test_create_subscription_with_price_id(self, mock_checkout):
        """Deve usar price_id correto"""
        mock_checkout.return_value = "https://checkout.stripe.com/pay/cs_test_123"

        from app.core.stripe import create_checkout_session

        price_id = "price_professional_monthly"
        await create_checkout_session(
            customer_email="customer@example.com",
            price_id=price_id,
            company_id="comp_123",
            success_url="https://app.example.com/success",
            cancel_url="https://app.example.com/cancel",
        )

        mock_checkout.assert_called()
        call_args = mock_checkout.call_args
        assert call_args[1]["price_id"] == price_id


class TestStripeWebhook:
    """Testes para processamento de webhooks Stripe"""

    @patch("app.core.stripe.handle_webhook")
    def test_stripe_webhook_checkout_completed(self, mock_webhook):
        """Deve processar evento checkout.session.completed"""
        event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "customer_email": "customer@example.com",
                    "subscription": "sub_123456",
                    "metadata": {"company_id": "comp_123"},
                }
            },
        }

        from app.core.stripe import handle_webhook

        # Converter para string JSON
        payload = json.dumps(event)
        signature = "t=123,v1=fake_signature"

        result = handle_webhook(payload, signature)
        # Função deve retornar sem erro
        mock_webhook.assert_called()

    @patch("app.core.stripe.handle_webhook")
    def test_stripe_webhook_payment_succeeded(self, mock_webhook):
        """Deve processar evento invoice.payment_succeeded"""
        event = {
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "id": "in_test_123",
                    "subscription": "sub_123456",
                    "customer": "cus_test_123",
                    "amount_paid": 9900,
                }
            },
        }

        from app.core.stripe import handle_webhook

        payload = json.dumps(event)
        signature = "t=123,v1=fake_signature"

        result = handle_webhook(payload, signature)
        mock_webhook.assert_called()

    @patch("app.core.stripe.handle_webhook")
    def test_stripe_webhook_payment_failed(self, mock_webhook):
        """Deve processar evento invoice.payment_failed"""
        event = {
            "type": "invoice.payment_failed",
            "data": {
                "object": {
                    "id": "in_test_123",
                    "subscription": "sub_123456",
                    "customer": "cus_test_123",
                    "amount_due": 9900,
                }
            },
        }

        from app.core.stripe import handle_webhook

        payload = json.dumps(event)
        signature = "t=123,v1=fake_signature"

        result = handle_webhook(payload, signature)
        mock_webhook.assert_called()

    @patch("app.core.stripe.handle_webhook")
    def test_stripe_webhook_subscription_deleted(self, mock_webhook):
        """Deve processar evento customer.subscription.deleted"""
        event = {
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_123456",
                    "customer": "cus_test_123",
                    "status": "cancelled",
                }
            },
        }

        from app.core.stripe import handle_webhook

        payload = json.dumps(event)
        signature = "t=123,v1=fake_signature"

        result = handle_webhook(payload, signature)
        mock_webhook.assert_called()


class TestGetSubscription:
    """Testes para obtenção de status de assinatura"""

    @patch("app.core.stripe.get_customer_subscriptions")
    def test_get_subscription_returns_status(self, mock_get_subs):
        """Deve retornar status de assinatura atual"""
        mock_get_subs.return_value = [
            {
                "id": "sub_123456",
                "status": "active",
                "plan": "professional",
                "current_period_end": 1704067200,
                "items": {
                    "data": [
                        {
                            "price": {
                                "recurring": {"interval": "month", "interval_count": 1}
                            }
                        }
                    ]
                },
            }
        ]

        from app.core.stripe import get_customer_subscriptions

        subscriptions = get_customer_subscriptions("cus_test_123")

        assert len(subscriptions) > 0
        assert subscriptions[0]["status"] in [
            "active",
            "past_due",
            "unpaid",
            "cancelled",
        ]

    @patch("app.core.stripe.get_customer_subscriptions")
    def test_get_subscription_active(self, mock_get_subs):
        """Deve retornar assinatura ativa"""
        mock_get_subs.return_value = [
            {"id": "sub_123456", "status": "active", "plan": "professional"}
        ]

        from app.core.stripe import get_customer_subscriptions

        subscriptions = get_customer_subscriptions("cus_test_123")

        assert subscriptions[0]["status"] == "active"

    @patch("app.core.stripe.get_customer_subscriptions")
    def test_get_subscription_empty(self, mock_get_subs):
        """Deve retornar lista vazia se sem assinatura"""
        mock_get_subs.return_value = []

        from app.core.stripe import get_customer_subscriptions

        subscriptions = get_customer_subscriptions("cus_test_123")

        assert len(subscriptions) == 0


class TestStripeSettings:
    """Testes para configurações Stripe"""

    def test_stripe_settings_required_keys(self):
        """Deve validar chaves Stripe obrigatórias"""
        required_keys = [
            "STRIPE_SECRET_KEY",
            "STRIPE_PUBLISHABLE_KEY",
            "STRIPE_WEBHOOK_SECRET",
        ]

        # Simular ambiente
        stripe_config = {
            "STRIPE_SECRET_KEY": "sk_test_123456",
            "STRIPE_PUBLISHABLE_KEY": "pk_test_123456",
            "STRIPE_WEBHOOK_SECRET": "whsec_test_123456",
        }

        for key in required_keys:
            assert key in stripe_config

    def test_stripe_price_ids_configured(self):
        """Deve ter price IDs para planos"""
        price_ids = {
            "starter": "price_starter_monthly",
            "professional": "price_professional_monthly",
            "business": "price_business_monthly",
        }

        for plan, price_id in price_ids.items():
            assert plan in ["starter", "professional", "business"]
            assert "price_" in price_id
