import uuid
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
from sqlalchemy import and_, or_, func
from app.models import db, Lead, Deal, Activity, User, Clinic, Subscription, Proposal, DemoEvent

class LeadSource(Enum):
    WEBSITE = "website"
    LINKEDIN = "linkedin"
    REFERRAL = "referral"
    COLD_CALL = "cold_call"
    EVENT = "event"
    PARTNER = "partner"

class LeadStatus(Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    NURTURING = "nurturing"

class SalesFunnelManager:
    """Gestão completa do funil de vendas"""

    FUNNEL_STAGES = {
        'awareness': {
            'name': 'Conscientização',
            'statuses': [LeadStatus.NEW],
            'goal': 'Gerar interesse'
        },
        'consideration': {
            'name': 'Consideração',
            'statuses': [LeadStatus.CONTACTED, LeadStatus.QUALIFIED],
            'goal': 'Agendar demonstração'
        },
        'decision': {
            'name': 'Decisão',
            'statuses': [LeadStatus.PROPOSAL_SENT, LeadStatus.NEGOTIATION],
            'goal': 'Fechar contrato'
        },
        'retention': {
            'name': 'Retenção',
            'statuses': [LeadStatus.CLOSED_WON],
            'goal': 'Onboarding e sucesso'
        }
    }

    @staticmethod
    def capture_lead(
        name: str,
        email: str,
        phone: str,
        company: str,
        source: str,
        landing_page: str = None,
        utm_params: Dict = None,
        notes: str = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Captura novo lead do funil
        Retorna: (success, message, lead_id)
        """
        try:
            # Verificar se lead já existe
            existing = Lead.query.filter(
                or_(
                    Lead.email == email,
                    Lead.phone == phone
                )
            ).first()

            if existing:
                # Atualizar lead existente
                existing.last_contact = datetime.utcnow()
                existing.contact_count += 1
                lead_id = existing.id
                message = "Lead atualizado no sistema"
            else:
                # Criar novo lead
                lead = Lead(
                    name=name,
                    email=email,
                    phone=phone,
                    company=company,
                    source=source,
                    landing_page=landing_page,
                    utm_params=json.dumps(utm_params) if utm_params else None,
                    status=LeadStatus.NEW.value,
                    score=10, # Pontuação inicial
                    notes=notes
                )

                db.session.add(lead)
                db.session.commit()
                lead_id = lead.id
                message = "Lead cadastrado com sucesso"

                # Criar atividade
                activity = Activity(
                    lead_id=lead_id,
                    type='lead_captured',
                    description=f'Lead capturado via {source}',
                    metadata=json.dumps({
                        'landing_page': landing_page,
                        'utm_params': utm_params
                    })
                )
                db.session.add(activity)

                # Disparar email de boas-vindas
                SalesFunnelManager._send_welcome_email(email, name)

                # Atribuir ao vendedor (round robin)
                seller_id = SalesFunnelManager._assign_to_seller(lead_id)

            db.session.commit()

            return True, message, lead_id

        except Exception as e:
            logger.error(f"Erro ao capturar lead: {str(e)}")
            db.session.rollback()
            return False, f"Erro interno: {str(e)}", None

    @staticmethod
    def qualify_lead(lead_id: str, qualifier_id: str, criteria: Dict) -> bool:
        """
        Qualifica um lead com base em critérios
        """
        try:
            lead = Lead.query.get(lead_id)
            if not lead:
                return False

            # Aplicar pontuação baseada nos critérios
            score = 0

            # Critérios de qualificação
            if criteria.get('has_budget', False):
                score += 30
            if criteria.get('decision_maker', False):
                score += 25
            if criteria.get('urgency', False):
                score += 20
            if criteria.get('company_size') in ['small', 'medium']:
                score += 15
            if criteria.get('industry') == 'healthcare':
                score += 10

            lead.score = score
            lead.status = LeadStatus.QUALIFIED.value if score >= 50 else LeadStatus.NURTURING.value
            lead.qualifier_id = qualifier_id
            lead.qualified_at = datetime.utcnow()
            lead.qualification_data = json.dumps(criteria)

            # Criar atividade
            activity = Activity(
                lead_id=lead_id,
                type='lead_qualified',
                description=f'Lead qualificado com score {score}/100',
                metadata=json.dumps(criteria)
            )
            db.session.add(activity)

            # Se qualificado, criar oportunidade
            if score >= 50:
                deal = Deal(
                    lead_id=lead_id,
                    owner_id=qualifier_id,
                    value=criteria.get('estimated_value', 0),
                    stage='proposal',
                    probability=0.3,
                    expected_close_date=datetime.utcnow() + timedelta(days=30)
                )
                db.session.add(deal)

            db.session.commit()
            return True

        except Exception as e:
            logger.error(f"Erro ao qualificar lead: {str(e)}")
            db.session.rollback()
            return False

    @staticmethod
    def schedule_demo(lead_id: str, scheduled_by: str, demo_details: Dict) -> bool:
        """
        Agenda demonstração para lead qualificado
        """
        try:
            lead = Lead.query.get(lead_id)
            if not lead:
                return False

            # Criar evento de demonstração
            demo = DemoEvent(
                lead_id=lead_id,
                scheduled_by=scheduled_by,
                scheduled_date=demo_details['date'],
                duration=demo_details.get('duration', 60),
                platform=demo_details.get('platform', 'google_meet'),
                agenda=demo_details.get('agenda'),
                status='scheduled'
            )
            db.session.add(demo)

            # Atualizar status do lead
            lead.status = LeadStatus.CONTACTED.value
            lead.last_contact = datetime.utcnow()

            # Criar atividade
            activity = Activity(
                lead_id=lead_id,
                type='demo_scheduled',
                description=f'Demonstração agendada para {demo_details["date"]}',
                metadata=json.dumps(demo_details)
            )
            db.session.add(activity)

            # Enviar confirmação
            SalesFunnelManager._send_demo_confirmation(lead, demo)

            db.session.commit()
            return True

        except Exception as e:
            logger.error(f"Erro ao agendar demonstração: {str(e)}")
            db.session.rollback()
            return False

    @staticmethod
    def create_proposal(lead_id: str, plan: str, customizations: Dict = None) -> Tuple[bool, str]:
        """
        Cria proposta comercial para o lead
        """
        try:
            lead = Lead.query.get(lead_id)
            if not lead:
                return False, "Lead não encontrado"

            # Buscar configuração do plano
            from app import Config
            plan_config = Config.PRICING_PLANS.get(plan)
            if not plan_config:
                return False, "Plano inválido"

            # Calcular valores
            setup_fee = plan_config['setup_fee']
            monthly_price = plan_config['monthly_price']

            # Aplicar descontos ou customizações
            if customizations:
                if customizations.get('annual_payment'):
                    monthly_price *= 0.8 # 20% de desconto para pagamento anual
                if customizations.get('multiple_clinics'):
                    monthly_price *= 0.9 # 10% de desconto por clínica adicional

            # Criar proposta
            proposal = Proposal(
                lead_id=lead_id,
                plan=plan,
                monthly_price=monthly_price,
                setup_fee=setup_fee,
                contract_duration=customizations.get('contract_duration', 12),
                customizations=json.dumps(customizations) if customizations else None,
                status='draft',
                valid_until=datetime.utcnow() + timedelta(days=15)
            )
            db.session.add(proposal)

            # Atualizar lead
            lead.status = LeadStatus.PROPOSAL_SENT.value

            # Criar atividade
            activity = Activity(
                lead_id=lead_id,
                type='proposal_created',
                description=f'Proposta criada para plano {plan}',
                metadata=json.dumps({
                    'plan': plan,
                    'monthly_price': monthly_price,
                    'setup_fee': setup_fee
                })
            )
            db.session.add(activity)

            db.session.commit()

            # Gerar PDF da proposta
            pdf_url = SalesFunnelManager._generate_proposal_pdf(proposal, lead)
            proposal.pdf_url = pdf_url

            db.session.commit()

            return True, proposal.id

        except Exception as e:
            logger.error(f"Erro ao criar proposta: {str(e)}")
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def close_deal(deal_id: str, won: bool, reason: str = None, value: float = None) -> bool:
        """
        Fecha um negócio (won ou lost)
        """
        try:
            deal = Deal.query.get(deal_id)
            if not deal:
                return False

            lead = Lead.query.get(deal.lead_id)

            if won:
                deal.stage = 'closed_won'
                deal.closed_value = value or deal.value
                deal.closed_at = datetime.utcnow()
                deal.win_reason = reason

                lead.status = LeadStatus.CLOSED_WON.value

                # Criar cliente a partir do lead
                SalesFunnelManager._convert_lead_to_client(lead, deal)

            else:
                deal.stage = 'closed_lost'
                deal.lost_reason = reason
                deal.closed_at = datetime.utcnow()

                lead.status = LeadStatus.CLOSED_LOST.value

            # Criar atividade
            activity_type = 'deal_won' if won else 'deal_lost'
            activity = Activity(
                lead_id=deal.lead_id,
                type=activity_type,
                description=f'Negócio {"ganho" if won else "perdido"} - {reason}',
                metadata=json.dumps({
                    'value': value,
                    'reason': reason
                })
            )
            db.session.add(activity)

            db.session.commit()
            return True

        except Exception as e:
            logger.error(f"Erro ao fechar negócio: {str(e)}")
            db.session.rollback()
            return False

    @staticmethod
    def _assign_to_seller(lead_id: str) -> Optional[str]:
        """
        Atribui lead a vendedor usando round robin
        """
        sellers = User.query.filter_by(role='sales').filter_by(status='active').all()

        if not sellers:
            return None

        # Encontrar vendedor com menos leads atribuídos hoje
        today = datetime.utcnow().date()
        seller_loads = []

        for seller in sellers:
            today_leads = Lead.query.filter(
                Lead.assigned_to == seller.id,
                func.date(Lead.assigned_at) == today
            ).count()

            seller_loads.append((seller.id, today_leads))

        # Escolher vendedor com menor carga
        seller_id = min(seller_loads, key=lambda x: x[1])[0]

        # Atualizar lead
        lead = Lead.query.get(lead_id)
        lead.assigned_to = seller_id
        lead.assigned_at = datetime.utcnow()

        return seller_id

    @staticmethod
    def _convert_lead_to_client(lead: Lead, deal: Deal):
        """
        Converte lead em cliente ativo
        """
        # Criar usuário
        user = User(
            email=lead.email,
            name=lead.name,
            phone=lead.phone,
            role='client'
        )
        user.password = str(uuid.uuid4())[:8] # Senha temporária
        db.session.add(user)
        db.session.flush()

        # Criar clínica
        clinic = Clinic(
            user_id=user.id,
            name=lead.company,
            phone=lead.phone,
            email=lead.email,
            status='pending'
        )
        db.session.add(clinic)
        db.session.flush()

        # Criar assinatura
        subscription = Subscription(
            user_id=user.id,
            clinic_id=clinic.id,
            plan=deal.plan,
            monthly_price=deal.closed_value,
            start_date=datetime.utcnow().date(),
            status='active'
        )
        db.session.add(subscription)

        # Linkar lead com cliente
        lead.converted_to_client = True
        lead.client_id = user.id

        # Criar atividade de conversão
        activity = Activity(
            lead_id=lead.id,
            type='lead_converted',
            description=f'Lead convertido em cliente ID: {user.id}',
            metadata=json.dumps({
                'clinic_id': clinic.id,
                'subscription_plan': deal.plan
            })
        )
        db.session.add(activity)

    @staticmethod
    def _generate_proposal_pdf(proposal, lead) -> str:
        """Gera PDF da proposta usando template HTML"""
        # Implementar geração de PDF (usando WeasyPrint ou similar)
        return f"/proposals/{proposal.id}.pdf"

    @staticmethod
    def _send_welcome_email(email: str, name: str):
        """Envia email de boas-vindas automatizado"""
        # Implementar
        pass

    @staticmethod
    def _send_demo_confirmation(lead: Lead, demo: DemoEvent):
        """Envia confirmação de demonstração"""
        # Implementar
        pass