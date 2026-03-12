import json
import logging
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional
from flask import current_app

from app import db
# fuzzy integration helper
from c_modules.ctypes_example import FuzzySystem
from app.models import Clinic, Patient, MarketingCampaign, MarketingMessage

logger = logging.getLogger(__name__)

class MarketingSegment(Enum):
    """Segmentos de pacientes para marketing"""
    NEW_PATIENTS = "new_patients"  # Primeira consulta nos últimos 30 dias
    ACTIVE_PATIENTS = "active_patients"  # 2+ consultas nos últimos 90 dias
    INACTIVE_PATIENTS = "inactive_patients"  # Sem consulta há 90+ dias
    HIGH_VALUE = "high_value"  # Gasto total > R$ 1000
    BIRTHDAY = "birthday"  # Aniversariantes do mês
    NO_SHOW = "no_show"  # Pacientes que faltaram
    CANCELLED = "cancelled"  # Pacientes que cancelaram
    SERVICE_SPECIFIC = "service_specific"  # Por tipo de serviço

class MarketingChannel(Enum):
    """Canais de marketing disponíveis"""
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    INSTAGRAM = "instagram"
    GOOGLE_ADS = "google_ads"
    FACEBOOK_ADS = "facebook_ads"

class MarketingAutomationEngine:
    """Motor de automação de marketing multicanal"""

    def __init__(self, clinic_id: str):
        self.clinic_id = clinic_id
        self.clinic = Clinic.query.get(clinic_id)

    def segment_patients(self, segment: MarketingSegment, filters: Dict = None) -> List[Patient]:
        """
        Segmenta pacientes baseado em critérios
        """
        query = Patient.query.filter_by(clinic_id=self.clinic_id)
        today = datetime.utcnow().date()

        if segment == MarketingSegment.NEW_PATIENTS:
            # Pacientes com primeira consulta nos últimos 30 dias
            cutoff_date = today - timedelta(days=30)
            query = query.filter(
                Patient.first_appointment_date >= cutoff_date,
                Patient.total_appointments == 1
            )
        elif segment == MarketingSegment.ACTIVE_PATIENTS:
            # Pacientes com 2+ consultas nos últimos 90 dias
            cutoff_date = today - timedelta(days=90)
            query = query.filter(
                Patient.last_appointment_date >= cutoff_date,
                Patient.total_appointments >= 2
            )
        elif segment == MarketingSegment.HIGH_VALUE:
            # Gasto total > R$ 1000
            query = query.filter(Patient.total_spent >= 1000)

        patients = query.all()
        # optionally reorder patients by fuzzy priority using available features
        if patients:
            fs = FuzzySystem(os.path.join(os.getcwd(), 'c_modules', 'fuzzy', 'rules.json'))
            # sample inputs: engagement derived from past opens/clicks, likelihood maybe based on recency
            scored = []
            for p in patients:
                eng = p.total_appointments or 0
                like = 100 if p.last_appointment_date and (datetime.utcnow().date() - p.last_appointment_date).days < 30 else 50
                score = fs.evaluate('score', [float(eng), float(like), 1.0])
                scored.append((score, p))
            scored.sort(key=lambda tup: tup[0], reverse=True)
            return [p for _, p in scored]
        return patients

    def create_campaign(self, name: str, segment: MarketingSegment,
                        channels: List[MarketingChannel], message_templates: Dict,
                        schedule: Dict, filters: Dict = None) -> MarketingCampaign:
        """
        Cria uma nova campanha de marketing
        """
        campaign = MarketingCampaign(
            clinic_id=self.clinic_id,
            name=name,
            segment=segment.value,
            channels=json.dumps([c.value for c in channels]),
            message_templates=json.dumps(message_templates),
            schedule=json.dumps(schedule),
            filters=json.dumps(filters) if filters else None
        )

        db.session.add(campaign)
        db.session.commit()

        logger.info(f"Campanha criada: {name} para clínica {self.clinic_id}")
        return campaign

    def execute_campaign(self, campaign_id: str) -> Dict:
        """
        Executa uma campanha de marketing
        """
        campaign = MarketingCampaign.query.filter_by(
            id=campaign_id,
            clinic_id=self.clinic_id
        ).first()

        if not campaign:
            return {"error": "Campanha não encontrada"}

        # Segmentar pacientes
        segment = MarketingSegment(campaign.segment)
        patients = self.segment_patients(segment)

        # Executar campanha por canal
        results = {"total_sent": 0, "channels": {}}

        channels = json.loads(campaign.channels)
        for channel in channels:
            channel_results = self._send_channel_messages(
                patients, channel, campaign.message_templates
            )
            results["channels"][channel] = channel_results
            results["total_sent"] += channel_results["sent"]

        # Atualizar status da campanha
        campaign.status = "completed"
        db.session.commit()

        return results

    def _send_channel_messages(self, patients: List[Patient], channel: str, templates: Dict) -> Dict:
        """
        Envia mensagens por um canal específico
        """
        sent = 0
        failed = 0

        for patient in patients:
            try:
                # Aqui seria integrada com os serviços de mensageria
                # (WhatsApp Business API, SendGrid, etc.)
                message = MarketingMessage(
                    clinic_id=self.clinic_id,
                    campaign_id=None,  # Seria definido na campanha real
                    patient_id=patient.id,
                    channel=channel,
                    content=templates.get(channel, "Mensagem padrão"),
                    status="sent"
                )
                db.session.add(message)
                sent += 1
            except Exception as e:
                logger.error(f"Erro ao enviar mensagem: {str(e)}")
                failed += 1

        db.session.commit()
        return {"sent": sent, "failed": failed}

    def get_campaign_analytics(self, campaign_id: str) -> Dict:
        """
        Retorna analytics de uma campanha
        """
        campaign = MarketingCampaign.query.get(campaign_id)
        if not campaign:
            return {"error": "Campanha não encontrada"}

        messages = MarketingMessage.query.filter_by(campaign_id=campaign_id).all()

        analytics = {
            "campaign_name": campaign.name,
            "total_messages": len(messages),
            "sent": sum(1 for m in messages if m.status == "sent"),
            "delivered": sum(1 for m in messages if m.status == "delivered"),
            "read": sum(1 for m in messages if m.status == "read"),
            "failed": sum(1 for m in messages if m.status == "failed"),
            "channels": {}
        }

        # Analytics por canal
        for message in messages:
            if message.channel not in analytics["channels"]:
                analytics["channels"][message.channel] = {
                    "sent": 0, "delivered": 0, "read": 0, "failed": 0
                }
            analytics["channels"][message.channel][message.status] += 1

        return analytics