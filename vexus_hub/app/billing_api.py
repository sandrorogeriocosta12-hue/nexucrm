"""
Endpoints de Billing/Pagamento - Integração com Stripe

Endpoints implementados:
✓ POST /api/billing/subscribe - Cria session de checkout
✓ POST /api/billing/webhook - Processa eventos do Stripe
✓ GET /api/billing/subscription - Status da subscription
✓ DELETE /api/billing/subscription - Cancela subscription
✓ GET /api/billing/invoices - Histórico de faturas
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import db, Subscription, Clinic, User, AuditLog
from datetime import datetime, timezone, date, timedelta
import os
import json

# Importa Stripe (será instalado)
try:
    import stripe
    STRIPE_CONFIGURED = True
except ImportError:
    STRIPE_CONFIGURED = False

billing_api_bp = Blueprint('billing_api', __name__, url_prefix='/api/billing')

# Configura Stripe
if STRIPE_CONFIGURED:
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')

# ============================================================================
# SUBSCRIBE - Cria session de checkout com Stripe
# ============================================================================

@billing_api_bp.route('/subscribe', methods=['POST'])
@login_required
def create_subscription():
    """
    Cria uma session de checkout com Stripe
    
    Request:
        {
            "clinic_id": "clinic_uuid",
            "plan": "bronze",  // bronze, silver, gold
            "billing_cycle": "monthly"  // monthly, quarterly, yearly
        }
    
    Response:
        {
            "success": true,
            "checkout_url": "https://checkout.stripe.com/pay/...",
            "session_id": "cs_..."
        }
    
    Planos:
    - Bronze: $99/mês (up to 100 patients, 500 msgs)
    - Silver: $299/mês (up to 500 patients, 5000 msgs)
    - Gold: $999/mês (unlimited)
    """
    
    if not STRIPE_CONFIGURED:
        return jsonify({'error': 'Pagamento não está configurado. Contate suporte.'}), 503
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados obrigatórios não fornecidos'}), 400
    
    clinic_id = data.get('clinic_id')
    plan = data.get('plan', 'bronze')
    billing_cycle = data.get('billing_cycle', 'monthly')
    
    # Valida clinic
    clinic = Clinic.query.filter_by(id=clinic_id, user_id=current_user.id).first()
    if not clinic:
        return jsonify({'error': 'Clínica não encontrada'}), 404
    
    # Verifica se já tem subscription ativa
    existing_sub = Subscription.query.filter_by(clinic_id=clinic_id).first()
    if existing_sub and existing_sub.status in ['active', 'past_due']:
        return jsonify({
            'error': 'Esta clínica já possui uma subscription ativa',
            'subscription_id': existing_sub.id
        }), 400
    
    # Define preços por plano
    plan_prices = {
        'bronze': {'monthly': 9900, 'quarterly': 29700, 'yearly': 99000},
        'silver': {'monthly': 29900, 'quarterly': 89700, 'yearly': 299000},
        'gold': {'monthly': 99900, 'quarterly': 299700, 'yearly': 999000}
    }
    
    if plan not in plan_prices or billing_cycle not in plan_prices[plan]:
        return jsonify({'error': 'Plano ou ciclo de cobrança inválido'}), 400
    
    price_cents = plan_prices[plan][billing_cycle]
    
    try:
        # Busca ou cria customer no Stripe
        customer_id = current_user.id  # Usa user_id como customer reference
        
        try:
            # Tenta buscar customer existente
            customer = stripe.Customer.retrieve(customer_id)
        except stripe.error.InvalidRequestError:
            # Cria novo customer
            customer = stripe.Customer.create(
                id=customer_id,
                email=current_user.email,
                name=current_user.name,
                metadata={
                    'clinic_id': clinic_id,
                    'plan': plan
                }
            )
        
        # Cria session de checkout
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer=customer.id,
            mode='subscription',
            line_items=[{
                'price_data': {
                    'currency': 'brl',
                    'product_data': {
                        'name': f'Plano {plan.upper()} - {clinic.name}',
                        'description': f'Subscription {billing_cycle}',
                        'metadata': {
                            'clinic_id': clinic_id,
                            'plan': plan
                        }
                    },
                    'unit_amount': price_cents,
                    'recurring': {
                        'interval': 'month' if billing_cycle == 'monthly' else 'year' if billing_cycle == 'yearly' else None,
                        'interval_count': 1 if billing_cycle == 'monthly' else 3 if billing_cycle == 'quarterly' else 1
                    }
                },
                'quantity': 1
            }],
            success_url=f"https://app.vexuscrm.com/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"https://app.vexuscrm.com/billing/cancelled",
            metadata={
                'clinic_id': clinic_id,
                'user_id': current_user.id,
                'plan': plan
            }
        )
        
        # Salva sessão para rastrear depois
        from app.models import AuditLog
        db.session.add(AuditLog(
            user_id=current_user.id,
            clinic_id=clinic_id,
            action='subscription_checkout_created',
            resource_type='subscription',
            details=f'Checkout session criada: {session.id}'
        ))
        db.session.commit()
        
        return jsonify({
            'success': True,
            'checkout_url': session.url,
            'session_id': session.id,
            'plan': plan,
            'billing_cycle': billing_cycle,
            'amount': price_cents / 100  # Retorna em reais
        }), 200
        
    except stripe.error.StripeError as e:
        print(f"Erro Stripe: {e}")
        return jsonify({'error': 'Erro ao processar pagamento. Tente novamente.'}), 500
    except Exception as e:
        print(f"Erro ao criar checkout: {e}")
        return jsonify({'error': 'Erro ao criar sessão de pagamento.'}), 500

# ============================================================================
# WEBHOOK - Processa eventos do Stripe
# ============================================================================

@billing_api_bp.route('/webhook', methods=['POST'])
def handle_stripe_webhook():
    """
    Webhook do Stripe para processar eventos de pagamento
    
    Eventos processados:
    - checkout.session.completed: Pagamento realizado
    - invoice.payment_succeeded: Cobrança bem-sucedida
    - invoice.payment_failed: Cobrança falhou
    - customer.subscription.deleted: Subscription cancelada
    """
    
    if not STRIPE_CONFIGURED:
        return jsonify({'status': 'ok'}), 200
    
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            os.getenv('STRIPE_WEBHOOK_SECRET', '')
        )
    except ValueError:
        print("Payload inválido")
        return {'status': 'error'}, 400
    except stripe.error.SignatureVerificationError:
        print("Signature inválida")
        return {'status': 'error'}, 400
    
    # Processa eventos
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session_completed(session)
    
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        handle_invoice_payment_succeeded(invoice)
    
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        handle_invoice_payment_failed(invoice)
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_deleted(subscription)
    
    return jsonify({'status': 'ok'}), 200

def handle_checkout_session_completed(session):
    """Processa conclusão de checkout (novo pagamento)"""
    try:
        customer_id = session.get('customer')
        subscription_id = session.get('subscription')
        metadata = session.get('metadata', {})
        
        clinic_id = metadata.get('clinic_id')
        user_id = metadata.get('user_id')
        plan = metadata.get('plan')
        
        if not clinic_id or not user_id:
            print(f"Metadata incompleta no checkout: {metadata}")
            return
        
        # Busca ou atualiza subscription no BD
        subscription = Subscription.query.filter_by(clinic_id=clinic_id).first()
        
        if not subscription:
            # Cria nova subscription
            subscription = Subscription(
                user_id=user_id,
                clinic_id=clinic_id,
                plan=plan,
                status='active',
                start_date=date.today(),
                monthly_price=0,  # Será atualizado do Stripe
                gateway_subscription_id=subscription_id,
                gateway_customer_id=customer_id,
                payment_gateway='stripe'
            )
            db.session.add(subscription)
        else:
            # Atualiza subscription existente
            subscription.status = 'active'
            subscription.start_date = date.today()
            subscription.gateway_subscription_id = subscription_id
            subscription.gateway_customer_id = customer_id
        
        db.session.commit()
        
        # Log de auditoria
        db.session.add(AuditLog(
            user_id=user_id,
            clinic_id=clinic_id,
            action='subscription_activated',
            resource_type='subscription',
            details=f'Subscription ativada via Stripe: {subscription_id}'
        ))
        db.session.commit()
        
        # TODO: Enviar email de boas-vindas
        
    except Exception as e:
        print(f"Erro ao processar checkout: {e}")

def handle_invoice_payment_succeeded(invoice):
    """Processa cobrança bem-sucedida de invoice"""
    try:
        customer_id = invoice.get('customer')
        subscription_id = invoice.get('subscription')
        
        subscription = Subscription.query.filter_by(
            gateway_subscription_id=subscription_id
        ).first()
        
        if subscription:
            subscription.status = 'active'
            db.session.commit()
            
            db.session.add(AuditLog(
                user_id=subscription.user_id,
                clinic_id=subscription.clinic_id,
                action='invoice_paid',
                resource_type='invoice',
                resource_id=invoice.get('id'),
                details=f'Invoice {invoice.get("id")} paga com sucesso'
            ))
            db.session.commit()
    
    except Exception as e:
        print(f"Erro ao processar invoice_payment_succeeded: {e}")

def handle_invoice_payment_failed(invoice):
    """Processa falha de cobrança"""
    try:
        subscription_id = invoice.get('subscription')
        
        subscription = Subscription.query.filter_by(
            gateway_subscription_id=subscription_id
        ).first()
        
        if subscription:
            subscription.status = 'past_due'
            db.session.commit()
            
            # TODO: Enviar email notificando falha de pagamento
            
    except Exception as e:
        print(f"Erro ao processar invoice_payment_failed: {e}")

def handle_subscription_deleted(subscription):
    """Processa cancelamento de subscription"""
    try:
        subscription_id = subscription.get('id')
        
        db_subscription = Subscription.query.filter_by(
            gateway_subscription_id=subscription_id
        ).first()
        
        if db_subscription:
            db_subscription.status = 'cancelled'
            db_subscription.cancelled_at = datetime.now(timezone.utc)
            db.session.commit()
            
            db.session.add(AuditLog(
                user_id=db_subscription.user_id,
                clinic_id=db_subscription.clinic_id,
                action='subscription_cancelled',
                resource_type='subscription',
                details=f'Subscription cancelada no Stripe: {subscription_id}'
            ))
            db.session.commit()
    
    except Exception as e:
        print(f"Erro ao processar subscription_deleted: {e}")

# ============================================================================
# GET SUBSCRIPTION - Status atual da subscription
# ============================================================================

@billing_api_bp.route('/subscription', methods=['GET'])
@login_required
def get_subscription():
    """
    Retorna informações da subscription ativa do usuário
    
    Response:
        {
            "id": "sub_uuid",
            "clinic_id": "clinic_uuid",
            "plan": "bronze",
            "status": "active",
            "start_date": "2026-02-16",
            "end_date": "2026-03-16",
            "amount": 99.00,
            "next_billing_date": "2026-03-16"
        }
    """
    
    # Busca todas as subscriptions do usuário
    subscriptions = Subscription.query.filter_by(user_id=current_user.id).all()
    
    if not subscriptions:
        return jsonify({'subscriptions': []}), 200
    
    result = []
    for sub in subscriptions:
        result.append({
            'id': sub.id,
            'clinic_id': sub.clinic_id,
            'clinic_name': sub.clinic.name if sub.clinic else 'Unknown',
            'plan': sub.plan,
            'status': sub.status,
            'start_date': sub.start_date.isoformat() if sub.start_date else None,
            'end_date': sub.end_date.isoformat() if sub.end_date else None,
            'amount': float(sub.monthly_price) if sub.monthly_price else 0,
            'billing_cycle': sub.billing_cycle,
            'is_active': sub.is_active
        })
    
    return jsonify({'subscriptions': result}), 200

# ============================================================================
# DELETE SUBSCRIPTION - Cancela subscription (Direito de desistência)
# ============================================================================

@billing_api_bp.route('/subscription/<subscription_id>', methods=['DELETE'])
@login_required
def cancel_subscription(subscription_id):
    """
    Cancela uma subscription
    
    Response:
        {
            "success": true,
            "message": "Subscription cancelada com sucesso",
            "cancellation_date": "2026-02-16"
        }
    
    LGPD: Usuário tem direito de cancelar a qualquer momento
    """
    
    subscription = Subscription.query.filter_by(
        id=subscription_id,
        user_id=current_user.id
    ).first()
    
    if not subscription:
        return jsonify({'error': 'Subscription não encontrada'}), 404
    
    if subscription.status == 'cancelled':
        return jsonify({'error': 'Esta subscription já foi cancelada'}), 400
    
    try:
        # Cancela no Stripe também
        if STRIPE_CONFIGURED and subscription.gateway_subscription_id:
            try:
                stripe.Subscription.delete(subscription.gateway_subscription_id)
            except stripe.error.StripeError as e:
                print(f"Erro ao cancelar no Stripe: {e}")
                # Continua mesmo se Stripe falhar
        
        # Atualiza no BD
        subscription.status = 'cancelled'
        subscription.cancelled_at = datetime.now(timezone.utc)
        db.session.commit()
        
        # Log de auditoria
        db.session.add(AuditLog(
            user_id=current_user.id,
            clinic_id=subscription.clinic_id,
            action='subscription_cancelled_by_user',
            resource_type='subscription',
            resource_id=subscription.id,
            details='Subscription cancelada pelo usuário'
        ))
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Subscription cancelada com sucesso',
            'cancellation_date': subscription.cancelled_at.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao cancelar subscription: {e}")
        return jsonify({'error': 'Erro ao cancelar subscription'}), 500

# ============================================================================
# GET INVOICES - Histórico de faturas
# ============================================================================

@billing_api_bp.route('/invoices', methods=['GET'])
@login_required
def get_invoices():
    """
    Retorna histórico de faturas/invoices do usuário
    
    Query params:
    - subscription_id: Filtro por subscription
    - limit: Número máximo de invoices (default: 10)
    - offset: Paginação (default: 0)
    """
    
    subscription_id = request.args.get('subscription_id')
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    
    if not STRIPE_CONFIGURED:
        return jsonify({'invoices': []}), 200
    
    try:
        # Busca invoices no Stripe
        subscriptions = Subscription.query.filter_by(user_id=current_user.id).all()
        
        if not subscriptions:
            return jsonify({'invoices': []}), 200
        
        invoices = []
        for sub in subscriptions:
            if subscription_id and sub.id != subscription_id:
                continue
            
            if sub.gateway_subscription_id:
                try:
                    stripe_invoices = stripe.Invoice.list(
                        subscription=sub.gateway_subscription_id,
                        limit=limit
                    )
                    
                    for invoice in stripe_invoices.get('data', []):
                        invoices.append({
                            'id': invoice.get('id'),
                            'subscription_id': sub.id,
                            'amount': invoice.get('amount_paid', 0) / 100,
                            'currency': invoice.get('currency', 'brl').upper(),
                            'status': invoice.get('status'),
                            'date': datetime.fromtimestamp(invoice.get('created')).isoformat(),
                            'pdf_url': invoice.get('invoice_pdf'),
                            'number': invoice.get('number')
                        })
                except stripe.error.StripeError:
                    pass
        
        return jsonify({'invoices': invoices}), 200
        
    except Exception as e:
        print(f"Erro ao buscar invoices: {e}")
        return jsonify({'invoices': []}), 200
