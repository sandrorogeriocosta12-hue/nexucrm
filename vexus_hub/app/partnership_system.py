import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import and_, or_
from app.models import db, User, Clinic, Partnership, PartnershipTransaction, PartnershipAssignment
import logging

logger = logging.getLogger(__name__)

class PartnershipManager:
    """Sistema completo de gestão de parcerias"""

PARTNER_TYPES = {
'marketing': {
'name': 'Marketing Digital',
'skills': ['google_ads', 'meta_ads', 'social_media', 'seo'],
'commission_rates': {
'bronze': 0.10, # 10% da mensalidade
'silver': 0.15, # 15% da mensalidade
'gold': 0.20 # 20% da mensalidade + comissão sobre ads
}
},
'accounting': {
'name': 'Contabilidade Consultiva',
'skills': ['financial_analysis', 'tax_planning', 'bookkeeping'],
'commission_rates': {
'silver': 0.10, # 10% do valor da consultoria
'gold': 0.15 # 15% do valor da consultoria
}
},
'development': {
'name': 'Desenvolvimento',
'skills': ['api_integration', 'custom_features', 'automation'],
'commission_type': 'project' # Valor fixo por projeto
},
'sales': {
'name': 'Vendas',
'skills': ['b2b_sales', 'negotiation', 'closing'],
'commission_rates': {
'all': 0.20 # 20% da primeira mensalidade
}
}
}

@staticmethod
def register_partner(
    user_id: str,
    partner_type: str,
    company_name: str,
    skills: List[str],
    contact_info: Dict,
    pricing_model: Dict,
    min_clients: int = 1,
    max_clients: int = 10
) -> Tuple[bool, str]:
    """
    Registra um novo parceiro no sistema
    """
    try:
        # Validar tipo de parceiro
        if partner_type not in PartnershipManager.PARTNER_TYPES:
            return False, f"Tipo de parceiro inválido. Opções: {list(PartnershipManager.PARTNER_TYPES.keys())}"

        # Verificar se usuário já é parceiro
        existing = Partnership.query.filter_by(user_id=user_id, partner_type=partner_type).first()
        if existing:
            return False, "Você já está registrado como parceiro deste tipo"

        # Criar parceria
        partner = Partnership(
            user_id=user_id,
            partner_type=partner_type,
            company_name=company_name,
            skills=json.dumps(skills),
            contact_info=json.dumps(contact_info),
            pricing_model=json.dumps(pricing_model),
            status='pending', # pending, approved, active, suspended
            min_clients=min_clients,
            max_clients=max_clients,
            total_commission=0.00,
            completed_projects=0
        )

        db.session.add(partner)

        # Criar usuário do parceiro se não existir
        user = User.query.get(user_id)
        if user:
            user.role = f'partner_{partner_type}'

        db.session.commit()

        # Enviar email de confirmação
        PartnershipManager._send_partner_welcome_email(user, partner)

        return True, "Parceria registrada com sucesso! Aguarde aprovação."

    except Exception as e:
        logger.error(f"Erro ao registrar parceiro: {str(e)}")
        db.session.rollback()
        return False, f"Erro interno: {str(e)}"

@staticmethod
def approve_partner(partner_id: str, approved_by: str) -> bool:
    """
    Aprova um parceiro pendente
    """
    try:
        partner = Partnership.query.get(partner_id)
        if not partner:
            return False

        partner.status = 'approved'
        partner.approved_at = datetime.utcnow()
        partner.approved_by = approved_by

        # Criar contrato digital
        contract = PartnershipManager._generate_partner_contract(partner)
        partner.contract_details = json.dumps(contract)

        db.session.commit()

        # Enviar email com contrato
        PartnershipManager._send_partner_approval_email(partner)

        return True

    except Exception as e:
        logger.error(f"Erro ao aprovar parceiro: {str(e)}")
        db.session.rollback()
        return False

    @staticmethod
    def assign_partner_to_clinic(
        clinic_id: str,
        partner_type: str,
        service_needed: str = None,
        budget: float = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Atribui um parceiro a uma clínica
        Retorna: (success, message, partner_id)
        """
        try:
            clinic = Clinic.query.get(clinic_id)
            if not clinic:
                return False, "Clínica não encontrada", None

            # Buscar parceiros disponíveis
            available_partners = Partnership.query.filter(
                Partnership.partner_type == partner_type,
                Partnership.status == 'active',
                Partnership.current_clients < Partnership.max_clients
            ).all()

            if not available_partners:
                return False, "Nenhum parceiro disponível no momento", None

            # Escolher o melhor parceiro baseado em:
            # 1. Especialização
            # 2. Número atual de clientes (balancear carga)
            # 3. Avaliação
            selected_partner = min(
                available_partners,
                key=lambda p: p.current_clients
            )

            # Atualizar contadores
            selected_partner.current_clients += 1
            selected_partner.total_clients += 1

            # Registrar atribuição
            assignment = PartnershipAssignment(
                clinic_id=clinic_id,
                partner_id=selected_partner.id,
                partner_type=partner_type,
                service_needed=service_needed,
                budget=budget,
                status='assigned',
                assigned_at=datetime.utcnow()
            )

            db.session.add(assignment)

            # Atualizar clínica
            if partner_type == 'marketing':
                clinic.marketing_partner_id = selected_partner.id
            elif partner_type == 'accounting':
                clinic.accounting_partner_id = selected_partner.id

            db.session.commit()

            # Notificar parceiro e clínica
            PartnershipManager._notify_partner_assignment(
                selected_partner,
                clinic,
                assignment
            )

            return True, f"Parceiro {selected_partner.company_name} atribuído com sucesso", selected_partner.id

        except Exception as e:
            logger.error(f"Erro ao atribuir parceiro: {str(e)}")
            db.session.rollback()
            return False, f"Erro interno: {str(e)}", None

    @staticmethod
    def record_partner_service(
        clinic_id: str,
        partner_id: str,
        service_type: str,
        description: str,
        hours: float = 0,
        value: float = 0,
        client_plan: str = None
    ) -> Tuple[bool, str]:
        """
        Registra um serviço prestado por parceiro para cálculo de comissão
        """
        try:
            clinic = Clinic.query.get(clinic_id)
            partner = Partnership.query.get(partner_id)

            if not clinic or not partner:
                return False, "Clínica ou parceiro não encontrado"

            # Calcular comissão
            commission = PartnershipManager._calculate_commission(
                partner_type=partner.partner_type,
                client_plan=client_plan or clinic.subscription.plan,
                service_value=value,
                hours=hours
            )

            # Registrar transação
            transaction = PartnershipTransaction(
                clinic_id=clinic_id,
                partner_id=partner_id,
                service_type=service_type,
                description=description,
                hours=hours,
                service_value=value,
                commission_rate=commission['rate'],
                commission_amount=commission['amount'],
                status='pending', # pending, approved, paid
                service_date=datetime.utcnow()
            )

            db.session.add(transaction)

            # Atualizar total do parceiro
            partner.total_commission += commission['amount']
            partner.completed_projects += 1

            db.session.commit()

            return True, f"Serviço registrado. Comissão: R$ {commission['amount']:.2f}"

        except Exception as e:
            logger.error(f"Erro ao registrar serviço: {str(e)}")
            db.session.rollback()
            return False, f"Erro interno: {str(e)}"

    @staticmethod
    def _calculate_commission(
        partner_type: str,
        client_plan: str,
        service_value: float,
        hours: float = 0
    ) -> Dict:
        """
        Calcula comissão baseada no tipo de parceiro e plano do cliente
        """
        partner_config = PartnershipManager.PARTNER_TYPES.get(partner_type, {})

        if partner_type == 'marketing':
            # Comissão baseada no plano + % sobre gastos em ads
            base_rate = partner_config['commission_rates'].get(client_plan, 0.10)
            base_commission = service_value * base_rate

            # Se houver horas, adicionar rate por hora
            hourly_rate = 50 # R$ 50/hora padrão
            hourly_commission = hours * hourly_rate

            total = base_commission + hourly_commission

            return {
                'rate': base_rate,
                'amount': total,
                'breakdown': {
                    'base_commission': base_commission,
                    'hourly_commission': hourly_commission
                }
            }

        elif partner_type == 'accounting':
            # Comissão sobre valor da consultoria
            rate = partner_config['commission_rates'].get(client_plan, 0.10)
            commission = service_value * rate

            return {
                'rate': rate,
                'amount': commission,
                'breakdown': {'consultancy_commission': commission}
            }

        elif partner_type == 'sales':
            # Comissão sobre primeira mensalidade
            rate = partner_config['commission_rates'].get('all', 0.20)
            commission = service_value * rate

            return {
                'rate': rate,
                'amount': commission,
                'breakdown': {'sales_commission': commission}
            }

        else:
            # Comissão fixa para outros tipos
            return {
                'rate': 0.15,
                'amount': service_value * 0.15,
                'breakdown': {'fixed_commission': service_value * 0.15}
            }

    @staticmethod
    def generate_partner_portal(partner_id: str) -> Dict:
        """
        Gera dashboard personalizado para parceiro
        """
        partner = Partnership.query.get(partner_id)
        if not partner:
            return {}

        # Estatísticas do parceiro
        transactions = PartnershipTransaction.query.filter_by(
            partner_id=partner_id
        ).all()

        # Clínicas atribuídas
        assignments = PartnershipAssignment.query.filter_by(
            partner_id=partner_id,
            status='active'
        ).all()

        # Calcular métricas
        total_commission = sum(t.commission_amount for t in transactions if t.status == 'paid')
        pending_commission = sum(t.commission_amount for t in transactions if t.status == 'pending')

        # Serviços recentes
        recent_services = []
        for t in transactions[-10:]:
            clinic = Clinic.query.get(t.clinic_id)
            recent_services.append({
                'date': t.service_date.strftime('%d/%m/%Y'),
                'clinic': clinic.name if clinic else 'N/A',
                'service': t.service_type,
                'value': f"R$ {t.service_value:.2f}",
                'commission': f"R$ {t.commission_amount:.2f}",
                'status': t.status
            })

        return {
            'partner_info': {
                'company_name': partner.company_name,
                'partner_type': partner.partner_type,
                'status': partner.status,
                'rating': partner.rating or 5.0
            },
            'metrics': {
                'current_clients': partner.current_clients,
                'total_clients': partner.total_clients,
                'total_commission': total_commission,
                'pending_commission': pending_commission,
                'completion_rate': (partner.completed_projects / max(partner.total_projects, 1)) * 100
            },
            'assignments': [
                {
                    'clinic_id': a.clinic_id,
                    'clinic_name': Clinic.query.get(a.clinic_id).name,
                    'service': a.service_needed,
                    'assigned_date': a.assigned_at.strftime('%d/%m/%Y'),
                    'status': a.status
                }
                for a in assignments
            ],
            'recent_services': recent_services,
            'commission_breakdown': PartnershipManager._get_commission_breakdown(partner_id)
        }

    @staticmethod
    def _get_commission_breakdown(partner_id: str) -> List[Dict]:
        """Detalhamento de comissões por mês"""
        import pandas as pd

        transactions = PartnershipTransaction.query.filter_by(
            partner_id=partner_id,
            status='paid'
        ).all()

        if not transactions:
            return []

        # Agrupar por mês
        df_data = []
        for t in transactions:
            df_data.append({
                'month': t.service_date.strftime('%Y-%m'),
                'commission': float(t.commission_amount)
            })

        df = pd.DataFrame(df_data)
        monthly = df.groupby('month')['commission'].sum().reset_index()

        return [
            {'month': row['month'], 'commission': row['commission']}
            for _, row in monthly.iterrows()
        ]

    @staticmethod
    def _send_partner_welcome_email(user: User, partner: Partnership):
        """Envia email de boas-vindas ao parceiro"""
        # Implementar integração com serviço de email
        pass

    @staticmethod
    def _send_partner_approval_email(partner: Partnership):
        """Envia email de aprovação com contrato"""
        pass

        pass