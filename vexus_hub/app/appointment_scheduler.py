import logging
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy import and_, or_, func
from flask import current_app

from app.models import db, Clinic, Professional, Service, Appointment, Patient

logger = logging.getLogger(__name__)

class AppointmentScheduler:
    """Classe para gerenciar agendamentos de consultas"""

    def __init__(self, clinic: Clinic = None):
        self.clinic = clinic

    def get_available_slots(self, professional: Professional, service: Service,
                           target_date: date, duration_minutes: int = None) -> List[time]:
        """
        Retorna horários disponíveis para um profissional em uma data específica

        Args:
            professional: Profissional
            service: Serviço
            target_date: Data desejada
            duration_minutes: Duração em minutos (opcional, usa duração do serviço)

        Returns:
            Lista de horários disponíveis (time objects)
        """
        if not duration_minutes:
            duration_minutes = service.duration_minutes

        # Obter horário de funcionamento da clínica
        working_hours = self._get_working_hours(professional, target_date)
        if not working_hours:
            return []

        # Obter agendamentos existentes
        existing_appointments = Appointment.query.filter(
            and_(
                Appointment.professional_id == professional.id,
                Appointment.scheduled_date == target_date,
                Appointment.status.in_(['scheduled', 'confirmed'])
            )
        ).all()

        # Calcular slots disponíveis
        available_slots = []
        slot_duration = timedelta(minutes=duration_minutes)

        for start_time, end_time in working_hours:
            current_time = start_time

            while current_time + slot_duration <= end_time:
                slot_end = current_time + slot_duration

                # Verificar se o slot está livre
                is_available = True
                for appointment in existing_appointments:
                    appt_start = appointment.scheduled_time
                    appt_end = appt_start + timedelta(minutes=appointment.service.duration_minutes)

                    # Verificar sobreposição
                    if (current_time < appt_end and slot_end > appt_start):
                        is_available = False
                        break

                if is_available:
                    available_slots.append(current_time)

                current_time = current_time + timedelta(minutes=30)  # Slots de 30 minutos

        return available_slots

    def find_available_professionals(self, service: Service, target_date: date,
                                   preferred_time: time = None) -> List[Dict]:
        """
        Encontra profissionais disponíveis para um serviço em uma data

        Args:
            service: Serviço desejado
            target_date: Data desejada
            preferred_time: Horário preferido (opcional)

        Returns:
            Lista de dicionários com profissional e slots disponíveis
        """
        # Encontrar profissionais que oferecem o serviço
        professionals = Professional.query.filter(
            Professional.services.any(id=service.id),
            Professional.is_active == True
        ).all()

        available_professionals = []

        for professional in professionals:
            slots = self.get_available_slots(professional, service, target_date)

            if slots:
                # Filtrar por horário preferido se especificado
                if preferred_time:
                    # Encontrar slot mais próximo do horário preferido
                    closest_slot = min(slots, key=lambda x: abs(
                        datetime.combine(target_date, x) -
                        datetime.combine(target_date, preferred_time)
                    ))
                    slots = [closest_slot]

                available_professionals.append({
                    'professional': professional,
                    'available_slots': slots
                })

        return available_professionals

    def create_appointment(self, patient: Patient, professional: Professional,
                          service: Service, scheduled_date: date,
                          scheduled_time: time, notes: str = None) -> Tuple[bool, str, Appointment]:
        """
        Cria um novo agendamento

        Args:
            patient: Paciente
            professional: Profissional
            service: Serviço
            scheduled_date: Data do agendamento
            scheduled_time: Horário do agendamento
            notes: Observações (opcional)

        Returns:
            Tuple (success, message, appointment)
        """
        try:
            # Verificar se o horário está disponível
            available_slots = self.get_available_slots(professional, service, scheduled_date)

            if scheduled_time not in available_slots:
                return False, "Horário não disponível", None

            # Verificar se não há conflito com outros agendamentos
            conflict = Appointment.query.filter(
                and_(
                    Appointment.professional_id == professional.id,
                    Appointment.scheduled_date == scheduled_date,
                    Appointment.scheduled_time == scheduled_time,
                    Appointment.status.in_(['scheduled', 'confirmed'])
                )
            ).first()

            if conflict:
                return False, "Horário já ocupado", None

            # Criar agendamento
            appointment = Appointment(
                clinic_id=patient.clinic_id,
                patient_id=patient.id,
                professional_id=professional.id,
                service_id=service.id,
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                duration_minutes=service.duration_minutes,
                status='scheduled',
                notes=notes,
                created_by='system'
            )

            db.session.add(appointment)
            db.session.commit()

            logger.info(f"Agendamento criado: {appointment.id} para {patient.name}")

            return True, "Agendamento criado com sucesso", appointment

        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao criar agendamento: {str(e)}")
            return False, f"Erro ao criar agendamento: {str(e)}", None

    def reschedule_appointment(self, appointment: Appointment, new_date: date,
                              new_time: time, notes: str = None) -> Tuple[bool, str]:
        """
        Reagenda um agendamento existente

        Args:
            appointment: Agendamento a ser reagendado
            new_date: Nova data
            new_time: Novo horário
            notes: Novas observações (opcional)

        Returns:
            Tuple (success, message)
        """
        try:
            # Verificar se o novo horário está disponível
            available_slots = self.get_available_slots(
                appointment.professional,
                appointment.service,
                new_date
            )

            if new_time not in available_slots:
                return False, "Novo horário não disponível"

            # Verificar se não há conflito (excluindo o próprio agendamento)
            conflict = Appointment.query.filter(
                and_(
                    Appointment.professional_id == appointment.professional_id,
                    Appointment.scheduled_date == new_date,
                    Appointment.scheduled_time == new_time,
                    Appointment.id != appointment.id,
                    Appointment.status.in_(['scheduled', 'confirmed'])
                )
            ).first()

            if conflict:
                return False, "Novo horário já ocupado"

            # Atualizar agendamento
            old_date = appointment.scheduled_date
            old_time = appointment.scheduled_time

            appointment.scheduled_date = new_date
            appointment.scheduled_time = new_time
            appointment.rescheduled_at = datetime.utcnow()
            appointment.rescheduled_count = (appointment.rescheduled_count or 0) + 1

            if notes:
                appointment.notes = notes

            db.session.commit()

            logger.info(f"Agendamento reagendado: {appointment.id} de {old_date} {old_time} para {new_date} {new_time}")

            return True, "Agendamento reagendado com sucesso"

        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao reagendar: {str(e)}")
            return False, f"Erro ao reagendar: {str(e)}"

    def cancel_appointment(self, appointment: Appointment, reason: str = None,
                          cancelled_by: str = 'system') -> Tuple[bool, str]:
        """
        Cancela um agendamento

        Args:
            appointment: Agendamento a ser cancelado
            reason: Motivo do cancelamento (opcional)
            cancelled_by: Quem cancelou (system, patient, professional)

        Returns:
            Tuple (success, message)
        """
        try:
            if appointment.status in ['cancelled', 'completed']:
                return False, "Agendamento já foi cancelado ou concluído"

            appointment.status = 'cancelled'
            appointment.cancelled_at = datetime.utcnow()
            appointment.cancelled_by = cancelled_by
            appointment.cancellation_reason = reason

            db.session.commit()

            logger.info(f"Agendamento cancelado: {appointment.id} por {cancelled_by}")

            return True, "Agendamento cancelado com sucesso"

        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao cancelar agendamento: {str(e)}")
            return False, f"Erro ao cancelar agendamento: {str(e)}"

    def get_upcoming_appointments(self, clinic: Clinic = None, days_ahead: int = 7) -> List[Appointment]:
        """
        Retorna agendamentos futuros

        Args:
            clinic: Clínica (opcional, usa self.clinic se não especificado)
            days_ahead: Quantos dias à frente buscar

        Returns:
            Lista de agendamentos futuros
        """
        target_clinic = clinic or self.clinic
        if not target_clinic:
            return []

        end_date = date.today() + timedelta(days=days_ahead)

        return Appointment.query.filter(
            and_(
                Appointment.clinic_id == target_clinic.id,
                Appointment.scheduled_date >= date.today(),
                Appointment.scheduled_date <= end_date,
                Appointment.status.in_(['scheduled', 'confirmed'])
            )
        ).order_by(Appointment.scheduled_date, Appointment.scheduled_time).all()

    def get_patient_appointments(self, patient: Patient, limit: int = 10) -> List[Appointment]:
        """
        Retorna agendamentos de um paciente

        Args:
            patient: Paciente
            limit: Número máximo de agendamentos a retornar

        Returns:
            Lista de agendamentos do paciente
        """
        return Appointment.query.filter(
            Appointment.patient_id == patient.id
        ).order_by(
            Appointment.scheduled_date.desc(),
            Appointment.scheduled_time.desc()
        ).limit(limit).all()

    def check_availability(self, professional: Professional, service: Service,
                          target_date: date, target_time: time) -> Tuple[bool, str]:
        """
        Verifica se um horário específico está disponível

        Args:
            professional: Profissional
            service: Serviço
            target_date: Data
            target_time: Horário

        Returns:
            Tuple (is_available, message)
        """
        # Verificar se está dentro do horário de funcionamento
        working_hours = self._get_working_hours(professional, target_date)
        slot_end = target_time + timedelta(minutes=service.duration_minutes)

        is_within_hours = False
        for start_time, end_time in working_hours:
            if target_time >= start_time and slot_end <= end_time:
                is_within_hours = True
                break

        if not is_within_hours:
            return False, "Fora do horário de funcionamento"

        # Verificar conflitos com agendamentos existentes
        existing_appointments = Appointment.query.filter(
            and_(
                Appointment.professional_id == professional.id,
                Appointment.scheduled_date == target_date,
                Appointment.status.in_(['scheduled', 'confirmed'])
            )
        ).all()

        for appointment in existing_appointments:
            appt_start = appointment.scheduled_time
            appt_end = appt_start + timedelta(minutes=appointment.service.duration_minutes)

            # Verificar sobreposição
            if target_time < appt_end and slot_end > appt_start:
                return False, "Horário ocupado"

        return True, "Horário disponível"

    def _get_working_hours(self, professional: Professional, target_date: date) -> List[Tuple[time, time]]:
        """
        Retorna horários de funcionamento para um profissional em uma data específica

        Args:
            professional: Profissional
            target_date: Data

        Returns:
            Lista de tuplas (hora_inicio, hora_fim)
        """
        # Determinar o dia da semana (0=segunda, 6=domingo)
        weekday = target_date.weekday()

        # Obter configuração de horário do profissional
        if professional.working_hours and str(weekday) in professional.working_hours:
            hours_config = professional.working_hours[str(weekday)]
            if hours_config.get('enabled', False):
                start_time = datetime.strptime(hours_config['start'], '%H:%M').time()
                end_time = datetime.strptime(hours_config['end'], '%H:%M').time()
                return [(start_time, end_time)]

        # Se não há configuração específica, usar horário padrão da clínica
        clinic = professional.clinic
        if clinic and clinic.working_hours and str(weekday) in clinic.working_hours:
            hours_config = clinic.working_hours[str(weekday)]
            if hours_config.get('enabled', False):
                start_time = datetime.strptime(hours_config['start'], '%H:%M').time()
                end_time = datetime.strptime(hours_config['end'], '%H:%M').time()
                return [(start_time, end_time)]

        # Horário padrão: 8h às 18h de segunda a sexta
        if weekday < 5:  # Segunda a sexta
            return [(time(8, 0), time(18, 0))]
        else:  # Sábado e domingo
            return [(time(8, 0), time(12, 0))]

    def get_daily_schedule(self, professional: Professional, target_date: date) -> Dict:
        """
        Retorna o cronograma diário de um profissional

        Args:
            professional: Profissional
            target_date: Data

        Returns:
            Dicionário com informações do dia
        """
        appointments = Appointment.query.filter(
            and_(
                Appointment.professional_id == professional.id,
                Appointment.scheduled_date == target_date,
                Appointment.status.in_(['scheduled', 'confirmed'])
            )
        ).order_by(Appointment.scheduled_time).all()

        working_hours = self._get_working_hours(professional, target_date)

        return {
            'date': target_date,
            'working_hours': working_hours,
            'appointments': [{
                'id': appt.id,
                'time': appt.scheduled_time.strftime('%H:%M'),
                'duration': appt.service.duration_minutes,
                'service': appt.service.name,
                'patient': appt.patient.name,
                'status': appt.status
            } for appt in appointments]
        }

    def suggest_alternative_slots(self, professional: Professional, service: Service,
                                target_date: date, preferred_time: time,
                                days_ahead: int = 7) -> List[Dict]:
        """
        Sugere horários alternativos quando o preferido não está disponível

        Args:
            professional: Profissional
            service: Serviço
            target_date: Data preferida
            preferred_time: Horário preferido
            days_ahead: Quantos dias à frente buscar alternativas

        Returns:
            Lista de sugestões alternativas
        """
        suggestions = []

        # Buscar nos próximos dias
        for days in range(days_ahead + 1):
            check_date = target_date + timedelta(days=days)

            available_slots = self.get_available_slots(professional, service, check_date)

            if available_slots:
                # Ordenar por proximidade do horário preferido
                sorted_slots = sorted(available_slots, key=lambda x: abs(
                    datetime.combine(check_date, x) -
                    datetime.combine(target_date, preferred_time)
                ))

                for slot in sorted_slots[:3]:  # Máximo 3 sugestões por dia
                    suggestions.append({
                        'date': check_date,
                        'time': slot,
                        'datetime': datetime.combine(check_date, slot),
                        'professional': professional.name
                    })

        # Ordenar todas as sugestões por proximidade
        suggestions.sort(key=lambda x: x['datetime'])

        return suggestions[:10]  # Retornar as 10 melhores sugestões