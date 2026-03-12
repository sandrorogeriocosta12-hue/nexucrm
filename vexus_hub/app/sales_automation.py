import json
from datetime import datetime, timedelta
from typing import Dict, List
from app.models import db, Lead, Activity, EmailTemplate, EmailCampaign
import logging

logger = logging.getLogger(__name__)

class SalesAutomation:
    """Automação de vendas com sequências de email e follow-up"""

    @staticmethod
    def trigger_lead_sequence(lead_id: str, sequence_name: str = 'default'):
        """
        Dispara sequência automatizada para um lead
        """
        lead = Lead.query.get(lead_id)
        if not lead:
            return

        # Definir sequência baseada no score e fonte
        if sequence_name == 'default':
            if lead.score >= 70:
                sequence_name = 'high_value'
            elif lead.source == 'website':
                sequence_name = 'website_lead'
            elif lead.source == 'referral':
                sequence_name = 'referral_lead'
            else:
                sequence_name = 'cold_lead'

        # Carregar sequência
        sequence = SalesAutomation._load_sequence(sequence_name)
        if not sequence:
            logger.error(f"Sequência {sequence_name} não encontrada")
            return

        # Criar campanha para o lead
        campaign = EmailCampaign(
            lead_id=lead_id,
            sequence_name=sequence_name,
            status='active',
            current_step=0,
            total_steps=len(sequence['steps'])
        )
        db.session.add(campaign)
        db.session.commit()

        # Agendar primeiro email
        # Agendar primeiro email
        SalesAutomation._schedule_next_email(campaign.id, sequence['steps'][0])

    @staticmethod
    def _load_sequence(sequence_name: str) -> Dict:
        """
        Carrega sequência de emails do banco de dados
        """
        # Buscar templates da sequência
        templates = EmailTemplate.query.filter_by(
            sequence_name=sequence_name,
            active=True
        ).order_by('step_order').all()

        if not templates:
            # Criar sequência padrão
            templates = SalesAutomation._create_default_sequence(sequence_name)

        steps = []
        for template in templates:
            steps.append({
                'id': template.id,
                'order': template.step_order,
                'delay_days': template.delay_days,
                'delay_hours': template.delay_hours,
                'subject': template.subject,
                'content': template.content,
                'conditions': json.loads(template.conditions) if template.conditions else {}
            })

        return {
            'name': sequence_name,
            'steps': steps
        }

    @staticmethod
    def _create_default_sequence(sequence_name: str) -> List[EmailTemplate]:
        """
        Cria sequência padrão baseada no tipo
        """
        sequences = {
            'high_value': [
                {
                    'step_order': 1,
                    'delay_hours': 1,
                    'subject': '👋 Obrigado pelo seu interesse na Vexus IA!',
                    'content': 'Template de email de boas-vindas...'
                },
                {
                    'step_order': 2,
                    'delay_days': 1,
                    'subject': '📈 Como outras clínicas aumentaram em 40% seus agendamentos',
                    'content': 'Template com case de sucesso...'
                },
                {
                    'step_order': 3,
                    'delay_days': 3,
                    'subject': '🎁 Oferta especial para sua clínica',
                    'content': 'Template com oferta personalizada...'
                }
            ],
            'website_lead': [
                # Sequência para leads do website
            ],
            'referral_lead': [
                # Sequência para leads de indicação
            ]
        }

        sequence_data = sequences.get(sequence_name, sequences['high_value'])

        templates = []
        for step in sequence_data:
            template = EmailTemplate(
                name=f"{sequence_name}_step_{step['step_order']}",
                sequence_name=sequence_name,
                step_order=step['step_order'],
                delay_days=step.get('delay_days', 0),
                delay_hours=step.get('delay_hours', 0),
                subject=step['subject'],
                content=step['content'],
                active=True
            )
            templates.append(template)
            db.session.add(template)

        db.session.commit()
        return templates

    @staticmethod
    def _schedule_next_email(campaign_id: str, step: Dict):
        """
        Agenda próximo email da sequência
        """
        from app.tasks import send_automated_email

        # Calcular data de envio
        send_time = datetime.utcnow() + timedelta(
            days=step.get('delay_days', 0),
            hours=step.get('delay_hours', 0)
        )

        # Agendar tarefa
        send_automated_email.apply_async(
            args=[campaign_id, step['id']],
            eta=send_time
        )

        logger.info(f"Email agendado para {send_time}")