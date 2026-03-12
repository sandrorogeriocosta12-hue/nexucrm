import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from sqlalchemy import func, and_, or_, desc
from flask import current_app

from app.models import db, Clinic, Appointment, Patient, Service, Professional, Conversation

logger = logging.getLogger(__name__)

class DashboardMetrics:
    """Classe para calcular métricas do dashboard"""

    def __init__(self, clinic: Clinic = None):
        self.clinic = clinic

    def get_overview_metrics(self, days: int = 30) -> Dict:
        """
        Retorna métricas gerais do dashboard

        Args:
            days: Número de dias para análise

        Returns:
            Dicionário com métricas principais
        """
        start_date = date.today() - timedelta(days=days)

        # Filtros base
        base_filters = [Appointment.created_at >= start_date]
        if self.clinic:
            base_filters.append(Appointment.clinic_id == self.clinic.id)

        # Total de agendamentos
        total_appointments = db.session.query(func.count(Appointment.id)).filter(*base_filters).scalar()

        # Agendamentos confirmados
        confirmed_appointments = db.session.query(func.count(Appointment.id)).filter(
            *base_filters,
            Appointment.status == 'confirmed'
        ).scalar()

        # Taxa de confirmação
        confirmation_rate = (confirmed_appointments / total_appointments * 100) if total_appointments > 0 else 0

        # Novos pacientes
        new_patients = db.session.query(func.count(Patient.id)).filter(
            Patient.created_at >= start_date,
            Patient.clinic_id == self.clinic.id if self.clinic else True
        ).scalar()

        # Receita estimada (baseado em preços dos serviços)
        revenue_query = db.session.query(func.sum(Service.price)).join(Appointment).filter(
            *base_filters,
            Appointment.status.in_(['scheduled', 'confirmed', 'completed'])
        )
        estimated_revenue = revenue_query.scalar() or 0

        # Média de agendamentos por dia
        avg_appointments_per_day = total_appointments / days if days > 0 else 0

        return {
            'total_appointments': total_appointments,
            'confirmed_appointments': confirmed_appointments,
            'confirmation_rate': round(confirmation_rate, 1),
            'new_patients': new_patients,
            'estimated_revenue': float(estimated_revenue),
            'avg_appointments_per_day': round(avg_appointments_per_day, 1),
            'period_days': days
        }

    def get_appointments_by_status(self, days: int = 30) -> Dict[str, int]:
        """
        Retorna distribuição de agendamentos por status

        Args:
            days: Número de dias para análise

        Returns:
            Dicionário com contagem por status
        """
        start_date = date.today() - timedelta(days=days)

        base_filters = [Appointment.created_at >= start_date]
        if self.clinic:
            base_filters.append(Appointment.clinic_id == self.clinic.id)

        status_counts = db.session.query(
            Appointment.status,
            func.count(Appointment.id)
        ).filter(*base_filters).group_by(Appointment.status).all()

        return {status: count for status, count in status_counts}

    def get_appointments_by_service(self, days: int = 30, limit: int = 10) -> List[Dict]:
        """
        Retorna agendamentos por serviço

        Args:
            days: Número de dias para análise
            limit: Número máximo de serviços a retornar

        Returns:
            Lista de dicionários com serviço e contagem
        """
        start_date = date.today() - timedelta(days=days)

        base_filters = [Appointment.created_at >= start_date]
        if self.clinic:
            base_filters.append(Appointment.clinic_id == self.clinic.id)

        service_stats = db.session.query(
            Service.name,
            func.count(Appointment.id).label('count'),
            func.sum(Service.price).label('revenue')
        ).join(Appointment).filter(*base_filters).group_by(Service.id, Service.name).order_by(
            desc('count')
        ).limit(limit).all()

        return [{
            'service': name,
            'appointments': count,
            'revenue': float(revenue or 0)
        } for name, count, revenue in service_stats]

    def get_appointments_by_professional(self, days: int = 30, limit: int = 10) -> List[Dict]:
        """
        Retorna agendamentos por profissional

        Args:
            days: Número de dias para análise
            limit: Número máximo de profissionais a retornar

        Returns:
            Lista de dicionários com profissional e estatísticas
        """
        start_date = date.today() - timedelta(days=days)

        base_filters = [Appointment.created_at >= start_date]
        if self.clinic:
            base_filters.append(Appointment.clinic_id == self.clinic.id)

        prof_stats = db.session.query(
            Professional.name,
            func.count(Appointment.id).label('appointments'),
            func.avg(Appointment.service.has(Service.price)).label('avg_revenue')
        ).join(Appointment).filter(*base_filters).group_by(Professional.id, Professional.name).order_by(
            desc('appointments')
        ).limit(limit).all()

        return [{
            'professional': name,
            'appointments': appointments,
            'avg_revenue': float(avg_revenue or 0)
        } for name, appointments, avg_revenue in prof_stats]

    def get_revenue_trend(self, days: int = 30) -> List[Dict]:
        """
        Retorna tendência de receita ao longo do tempo

        Args:
            days: Número de dias para análise

        Returns:
            Lista de dicionários com data e receita
        """
        start_date = date.today() - timedelta(days=days)

        base_filters = [
            Appointment.created_at >= start_date,
            Appointment.status.in_(['scheduled', 'confirmed', 'completed'])
        ]
        if self.clinic:
            base_filters.append(Appointment.clinic_id == self.clinic.id)

        # Agrupar por data
        revenue_trend = db.session.query(
            func.date(Appointment.created_at).label('date'),
            func.sum(Service.price).label('revenue')
        ).join(Service).filter(*base_filters).group_by(
            func.date(Appointment.created_at)
        ).order_by('date').all()

        return [{
            'date': str(trend_date),
            'revenue': float(revenue or 0)
        } for trend_date, revenue in revenue_trend]

    def get_patient_demographics(self) -> Dict:
        """
        Retorna dados demográficos dos pacientes

        Returns:
            Dicionário com estatísticas demográficas
        """
        base_filters = []
        if self.clinic:
            base_filters.append(Patient.clinic_id == self.clinic.id)

        # Distribuição por gênero
        gender_stats = db.session.query(
            Patient.gender,
            func.count(Patient.id)
        ).filter(*base_filters).group_by(Patient.gender).all()

        # Distribuição por faixa etária
        age_stats = db.session.query(
            func.extract('year', func.age(Patient.birth_date)).label('age'),
            func.count(Patient.id)
        ).filter(
            *base_filters,
            Patient.birth_date.isnot(None)
        ).group_by(func.extract('year', func.age(Patient.birth_date))).all()

        # Faixas etárias
        age_groups = {
            '0-18': 0,
            '19-30': 0,
            '31-50': 0,
            '51-70': 0,
            '70+': 0
        }

        for age, count in age_stats:
            if age <= 18:
                age_groups['0-18'] += count
            elif age <= 30:
                age_groups['19-30'] += count
            elif age <= 50:
                age_groups['31-50'] += count
            elif age <= 70:
                age_groups['51-70'] += count
            else:
                age_groups['70+'] += count

        return {
            'gender_distribution': {gender or 'Não informado': count for gender, count in gender_stats},
            'age_groups': age_groups
        }

    def get_conversation_metrics(self, days: int = 7) -> Dict:
        """
        Retorna métricas de conversas do WhatsApp

        Args:
            days: Número de dias para análise

        Returns:
            Dicionário com métricas de conversas
        """
        start_date = date.today() - timedelta(days=days)

        base_filters = [Conversation.created_at >= start_date]
        if self.clinic:
            base_filters.append(Conversation.clinic_id == self.clinic.id)

        # Total de conversas
        total_conversations = db.session.query(func.count(Conversation.id)).filter(*base_filters).scalar()

        # Conversas por plataforma
        platform_stats = db.session.query(
            Conversation.platform,
            func.count(Conversation.id)
        ).filter(*base_filters).group_by(Conversation.platform).all()

        # Conversas por intenção
        intent_stats = db.session.query(
            Conversation.intent,
            func.count(Conversation.id)
        ).filter(
            *base_filters,
            Conversation.intent.isnot(None)
        ).group_by(Conversation.intent).all()

        # Taxa de processamento por IA
        ai_processed = db.session.query(func.count(Conversation.id)).filter(
            *base_filters,
            Conversation.processed_by_ai == True
        ).scalar()

        ai_rate = (ai_processed / total_conversations * 100) if total_conversations > 0 else 0

        return {
            'total_conversations': total_conversations,
            'platform_distribution': {platform: count for platform, count in platform_stats},
            'intent_distribution': {intent or 'Não identificado': count for intent, count in intent_stats},
            'ai_processing_rate': round(ai_rate, 1)
        }

    def get_upcoming_appointments(self, limit: int = 10) -> List[Dict]:
        """
        Retorna próximos agendamentos

        Args:
            limit: Número máximo de agendamentos a retornar

        Returns:
            Lista de próximos agendamentos
        """
        base_filters = [
            Appointment.scheduled_date >= date.today(),
            Appointment.status.in_(['scheduled', 'confirmed'])
        ]
        if self.clinic:
            base_filters.append(Appointment.clinic_id == self.clinic.id)

        upcoming = Appointment.query.filter(*base_filters).join(
            Patient, Service, Professional
        ).order_by(
            Appointment.scheduled_date,
            Appointment.scheduled_time
        ).limit(limit).all()

        return [{
            'id': appt.id,
            'date': appt.scheduled_date.isoformat(),
            'time': appt.scheduled_time.strftime('%H:%M'),
            'patient': appt.patient.name,
            'service': appt.service.name,
            'professional': appt.professional.name,
            'status': appt.status
        } for appt in upcoming]

    def get_cancellation_rate(self, days: int = 30) -> Dict:
        """
        Retorna taxa de cancelamento

        Args:
            days: Número de dias para análise

        Returns:
            Dicionário com métricas de cancelamento
        """
        start_date = date.today() - timedelta(days=days)

        base_filters = [Appointment.created_at >= start_date]
        if self.clinic:
            base_filters.append(Appointment.clinic_id == self.clinic.id)

        # Total de agendamentos criados
        total_created = db.session.query(func.count(Appointment.id)).filter(*base_filters).scalar()

        # Agendamentos cancelados
        cancelled = db.session.query(func.count(Appointment.id)).filter(
            *base_filters,
            Appointment.status == 'cancelled'
        ).scalar()

        # Taxa de cancelamento
        cancellation_rate = (cancelled / total_created * 100) if total_created > 0 else 0

        # Motivos de cancelamento
        cancellation_reasons = db.session.query(
            Appointment.cancellation_reason,
            func.count(Appointment.id)
        ).filter(
            *base_filters,
            Appointment.status == 'cancelled',
            Appointment.cancellation_reason.isnot(None)
        ).group_by(Appointment.cancellation_reason).all()

        return {
            'total_appointments': total_created,
            'cancelled_appointments': cancelled,
            'cancellation_rate': round(cancellation_rate, 1),
            'cancellation_reasons': {reason: count for reason, count in cancellation_reasons}
        }

    def get_no_show_rate(self, days: int = 30) -> float:
        """
        Retorna taxa de faltas (no-show)

        Args:
            days: Número de dias para análise

        Returns:
            Taxa de faltas em porcentagem
        """
        start_date = date.today() - timedelta(days=days)

        base_filters = [
            Appointment.scheduled_date >= start_date,
            Appointment.scheduled_date <= date.today()
        ]
        if self.clinic:
            base_filters.append(Appointment.clinic_id == self.clinic.id)

        # Agendamentos que deveriam ter acontecido
        total_scheduled = db.session.query(func.count(Appointment.id)).filter(
            *base_filters,
            Appointment.status.in_(['scheduled', 'confirmed'])
        ).scalar()

        # Agendamentos marcados como no-show
        no_shows = db.session.query(func.count(Appointment.id)).filter(
            *base_filters,
            Appointment.status == 'no_show'
        ).scalar()

        return round((no_shows / total_scheduled * 100), 1) if total_scheduled > 0 else 0

    def get_service_utilization(self, days: int = 30) -> List[Dict]:
        """
        Retorna utilização dos serviços

        Args:
            days: Número de dias para análise

        Returns:
            Lista de serviços com métricas de utilização
        """
        start_date = date.today() - timedelta(days=days)

        base_filters = [Appointment.created_at >= start_date]
        if self.clinic:
            base_filters.append(Appointment.clinic_id == self.clinic.id)

        utilization = db.session.query(
            Service.name,
            func.count(Appointment.id).label('total_appointments'),
            func.avg(Service.duration_minutes).label('avg_duration'),
            func.sum(Service.price).label('total_revenue')
        ).join(Appointment).filter(*base_filters).group_by(Service.id, Service.name).order_by(
            desc('total_appointments')
        ).all()

        return [{
            'service': name,
            'total_appointments': total_appointments,
            'avg_duration': float(avg_duration or 0),
            'total_revenue': float(total_revenue or 0)
        } for name, total_appointments, avg_duration, total_revenue in utilization]

    def get_professional_performance(self, days: int = 30) -> List[Dict]:
        """
        Retorna performance dos profissionais

        Args:
            days: Número de dias para análise

        Returns:
            Lista de profissionais com métricas de performance
        """
        start_date = date.today() - timedelta(days=days)

        base_filters = [Appointment.created_at >= start_date]
        if self.clinic:
            base_filters.append(Appointment.clinic_id == self.clinic.id)

        performance = db.session.query(
            Professional.name,
            func.count(Appointment.id).label('total_appointments'),
            func.count(func.case([(Appointment.status == 'completed', 1)])).label('completed'),
            func.count(func.case([(Appointment.status == 'no_show', 1)])).label('no_shows'),
            func.avg(func.extract('epoch', Appointment.completed_at - Appointment.scheduled_date) / 3600).label('avg_delay_hours')
        ).join(Appointment).filter(*base_filters).group_by(Professional.id, Professional.name).order_by(
            desc('total_appointments')
        ).all()

        result = []
        for name, total, completed, no_shows, avg_delay in performance:
            completion_rate = (completed / total * 100) if total > 0 else 0
            no_show_rate = (no_shows / total * 100) if total > 0 else 0

            result.append({
                'professional': name,
                'total_appointments': total,
                'completion_rate': round(completion_rate, 1),
                'no_show_rate': round(no_show_rate, 1),
                'avg_delay_hours': float(avg_delay or 0)
            })

        return result