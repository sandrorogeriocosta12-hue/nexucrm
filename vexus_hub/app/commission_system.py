import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from flask import current_app
from app.models import db, Partnership, PartnershipTransaction, User, Clinic, Subscription, PartnerPayment

class CommissionCalculator:
    """Calculadora avançada de comissões"""

    @staticmethod
    def calculate_monthly_commissions(month: datetime = None) -> Dict:
        """
        Calcula comissões do mês para todos os parceiros
        """
        if not month:
            month = datetime.utcnow()

        month_start = month.replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)

        # Buscar transações do mês
        transactions = PartnershipTransaction.query.filter(
            PartnershipTransaction.service_date >= month_start,
            PartnershipTransaction.service_date < next_month,
            PartnershipTransaction.status != 'cancelled'
        ).all()

        # Agrupar por parceiro
        partner_commissions = {}

        for transaction in transactions:
            partner_id = transaction.partner_id

            if partner_id not in partner_commissions:
                partner = Partnership.query.get(partner_id)
                partner_commissions[partner_id] = {
                    'partner': partner,
                    'transactions': [],
                    'total_commission': Decimal('0.00'),
                    'total_value': Decimal('0.00'),
                    'by_service_type': {}
                }

            partner_data = partner_commissions[partner_id]
            partner_data['transactions'].append(transaction)
            partner_data['total_commission'] += transaction.commission_amount
            partner_data['total_value'] += transaction.service_value

            # Agrupar por tipo de serviço
            service_type = transaction.service_type
            if service_type not in partner_data['by_service_type']:
                partner_data['by_service_type'][service_type] = {
                    'count': 0,
                    'commission': Decimal('0.00'),
                    'value': Decimal('0.00')
                }

            service_data = partner_data['by_service_type'][service_type]
            service_data['count'] += 1
            service_data['commission'] += transaction.commission_amount
            service_data['value'] += transaction.service_value

        return partner_commissions

@staticmethod
def generate_commission_report(partner_id: str, start_date: datetime, end_date: datetime) -> Dict:
        """
        Gera relatório detalhado de comissões
        """
        transactions = PartnershipTransaction.query.filter(
            PartnershipTransaction.partner_id == partner_id,
            PartnershipTransaction.service_date >= start_date,
            PartnershipTransaction.service_date <= end_date
        ).order_by(PartnershipTransaction.service_date).all()

        if not transactions:
            return {}

        # Resumo por período
        summary = {
            'period': {
                'start': start_date.strftime('%d/%m/%Y'),
                'end': end_date.strftime('%d/%m/%Y'),
                'days': (end_date - start_date).days
            },
            'totals': {
                'transactions': len(transactions),
                'service_value': Decimal('0.00'),
                'commission': Decimal('0.00'),
                'avg_commission_rate': Decimal('0.00')
            },
            'by_clinic': {},
            'by_service_type': {},
            'daily_breakdown': {},
            'pending_payments': Decimal('0.00'),
            'paid_payments': Decimal('0.00')
        }

        for transaction in transactions:
            clinic_id = transaction.clinic_id
            service_type = transaction.service_type
            service_date = transaction.service_date.date()

            # Totais
            summary['totals']['service_value'] += transaction.service_value
            summary['totals']['commission'] += transaction.commission_amount

            # Por clínica
            if clinic_id not in summary['by_clinic']:
                clinic = Clinic.query.get(clinic_id)
                summary['by_clinic'][clinic_id] = {
                    'name': clinic.name if clinic else 'N/A',
                    'transactions': 0,
                    'value': Decimal('0.00'),
                    'commission': Decimal('0.00')
                }

            clinic_data = summary['by_clinic'][clinic_id]
            clinic_data['transactions'] += 1
            clinic_data['value'] += transaction.service_value
            clinic_data['commission'] += transaction.commission_amount

            # Por tipo de serviço
            if service_type not in summary['by_service_type']:
                summary['by_service_type'][service_type] = {
                    'count': 0,
                    'value': Decimal('0.00'),
                    'commission': Decimal('0.00')
                }

            service_data = summary['by_service_type'][service_type]
            service_data['count'] += 1
            service_data['value'] += transaction.service_value
            service_data['commission'] += transaction.commission_amount

            # Por dia
            date_str = service_date.strftime('%d/%m/%Y')
            if date_str not in summary['daily_breakdown']:
                summary['daily_breakdown'][date_str] = Decimal('0.00')

            summary['daily_breakdown'][date_str] += transaction.commission_amount

            # Status de pagamento
            if transaction.status == 'pending':
                summary['pending_payments'] += transaction.commission_amount
            elif transaction.status == 'paid':
                summary['paid_payments'] += transaction.commission_amount

        # Calcular taxa média
        if summary['totals']['service_value'] > 0:
            avg_rate = (summary['totals']['commission'] / summary['totals']['service_value']) * 100
            summary['totals']['avg_commission_rate'] = round(avg_rate, 2)

        return summary


class PaymentProcessor:
    """Processador de pagamentos para parceiros"""

    @staticmethod
    def process_partner_payments(month: datetime = None) -> Dict:
        """
        Processa pagamentos mensais para parceiros
        """
        if not month:
            month = datetime.utcnow()

        month_str = month.strftime('%Y-%m')
        commissions = CommissionCalculator.calculate_monthly_commissions(month)

        payment_results = {
            'month': month_str,
            'total_partners': len(commissions),
            'total_commission': Decimal('0.00'),
            'payments_processed': 0,
            'payments_failed': 0,
            'details': []
        }

        for partner_id, data in commissions.items():
            partner = data['partner']
            total_commission = data['total_commission']

            if total_commission <= 0:
                continue

            # Verificar mínimo para pagamento
            min_payment = Decimal('50.00') # Mínimo de R$ 50,00
            if total_commission < min_payment:
                # Acumular para próximo mês
                PaymentProcessor._accumulate_commission(partner_id, total_commission)
                continue

            # Processar pagamento
            success, payment_id = PaymentProcessor._process_single_payment(
                partner=partner,
                amount=total_commission,
                description=f"Comissões {month_str}",
                transactions=data['transactions']
            )

            if success:
                payment_results['total_commission'] += total_commission
                payment_results['payments_processed'] += 1

                # Marcar transações como pagas
                for transaction in data['transactions']:
                    transaction.status = 'paid'
                    transaction.paid_at = datetime.utcnow()
                    transaction.payment_id = payment_id

                payment_results['details'].append({
                    'partner': partner.company_name,
                    'amount': float(total_commission),
                    'payment_id': payment_id,
                    'status': 'success'
                })
            else:
                payment_results['payments_failed'] += 1
                payment_results['details'].append({
                    'partner': partner.company_name,
                    'amount': float(total_commission),
                    'status': 'failed',
                    'error': payment_id # payment_id contém erro em caso de falha
                })

        db.session.commit()
        return payment_results

    @staticmethod
    def _process_single_payment(partner: Partnership, amount: Decimal,
                                description: str, transactions: List) -> Tuple[bool, str]:
        """
        Processa pagamento individual para parceiro
        """
        try:
            # Verificar método de pagamento do parceiro
            payment_method = json.loads(partner.payment_method) if partner.payment_method else {}

            if not payment_method:
                return False, "Método de pagamento não configurado"

            # Aqui você integraria com:
            # 1. Pagar.me (para PIX e boleto)
            # 2. Stripe (para cartão internacional)
            # 3. PayPal (para pagamentos internacionais)

            method_type = payment_method.get('type', 'pix')

            if method_type == 'pix':
                # Gerar PIX
                payment_result = PaymentProcessor._generate_pix_payment(
                    partner=partner,
                    amount=amount,
                    description=description
                )
            elif method_type == 'bank_transfer':
                # Agendar TED
                payment_result = PaymentProcessor._schedule_bank_transfer(
                    partner=partner,
                    amount=amount,
                    description=description
                )
            elif method_type == 'paypal':
                # Processar via PayPal
                payment_result = PaymentProcessor._process_paypal_payment(
                    partner=partner,
                    amount=amount,
                    description=description
                )
            else:
                return False, f"Método de pagamento não suportado: {method_type}"

            if payment_result['success']:
                # Registrar pagamento no sistema
                payment_record = PartnerPayment(
                    partner_id=partner.id,
                    payment_method=method_type,
                    amount=amount,
                    description=description,
                    status='processed',
                    reference_id=payment_result['payment_id'],
                    transaction_ids=json.dumps([t.id for t in transactions]),
                    processed_at=datetime.utcnow()
                )
                db.session.add(payment_record)

                return True, payment_record.id
            else:
                return False, payment_result.get('error', 'Erro desconhecido')

        except Exception as e:
            logger.error(f"Erro ao processar pagamento: {str(e)}")
            return False, str(e)

    @staticmethod
    def _generate_pix_payment(partner: Partnership, amount: Decimal, description: str) -> Dict:
        """
        Gera pagamento PIX usando Pagar.me ou similar
        """
        # Integração com Pagar.me
        # API Docs: https://docs.pagar.me/reference/criar-transacao-pix
        import requests

        payload = {
            'amount': int(amount * 100), # Converter para centavos
            'payment_method': 'pix',
            'pix': {
                'expires_in': 86400 # 24 horas
            },
            'customer': {
                'name': partner.company_name,
                'email': partner.user.email,
                'document': partner.tax_id,
                'type': 'individual' if len(partner.tax_id) == 11 else 'company'
            },
            'metadata': {
                'partner_id': partner.id,
                'description': description
            }
        }

        try:
            response = requests.post(
                'https://api.pagar.me/1/transactions',
                json=payload,
                auth=(current_app.config['PAGARME_API_KEY'], '')
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'payment_id': data['id'],
                    'pix_qr_code': data['pix_qr_code'],
                    'pix_expiration': data['pix_expiration_date']
                }
            else:
                return {
                    'success': False,
                    'error': f"Erro Pagar.me: {response.text}"
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def _accumulate_commission(partner_id: str, amount: Decimal):
        """
        Acumula comissão abaixo do mínimo para pagamento futuro
        """
        partner = Partnership.query.get(partner_id)
        if not partner:
            return

        accumulated = json.loads(partner.accumulated_commissions) if partner.accumulated_commissions else {}
        current_month = datetime.utcnow().strftime('%Y-%m')

        if current_month not in accumulated:
            accumulated[current_month] = {
                'amount': Decimal('0.00'),
                'transactions': []
            }

        accumulated[current_month]['amount'] += amount

        partner.accumulated_commissions = json.dumps(accumulated)

    @staticmethod
    def _schedule_bank_transfer(partner: Partnership, amount: Decimal, description: str) -> Dict:
        """
        Agenda transferência bancária (TED) para parceiro
        """
        # Integração com sistema bancário
        # Aqui seria integrada com APIs bancárias como Itaú, Bradesco, etc.
        try:
            # Simulação de agendamento
            return {
                'success': True,
                'payment_id': f"TED_{partner.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                'scheduled_date': (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def _process_paypal_payment(partner: Partnership, amount: Decimal, description: str) -> Dict:
        """
        Processa pagamento via PayPal
        """
        # Integração com PayPal API
        # API Docs: https://developer.paypal.com/docs/api/payments/v2/
        try:
            # Simulação de processamento PayPal
            return {
                'success': True,
                'payment_id': f"PAYPAL_{partner.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                'paypal_url': f"https://paypal.com/pay/{partner.id}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def _accumulate_commission(partner_id: str, amount: Decimal):
        """
        Acumula comissão abaixo do mínimo para pagamento futuro
        """
        partner = Partnership.query.get(partner_id)
        if not partner:
            return

        accumulated = json.loads(partner.accumulated_commissions) if partner.accumulated_commissions else {}
        current_month = datetime.utcnow().strftime('%Y-%m')

        if current_month not in accumulated:
            accumulated[current_month] = {
                'amount': Decimal('0.00'),
                'transactions': []
            }

        accumulated[current_month]['amount'] += amount

        partner.accumulated_commissions = json.dumps(accumulated)