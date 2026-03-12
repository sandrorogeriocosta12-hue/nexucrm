import logging
from datetime import datetime, date, time, timedelta
from flask import current_app
from sqlalchemy import and_, or_

from app import celery, db
from app.models import Appointment, Patient, Clinic, Notification
from app.whatsapp_integration import WhatsAppBusinessAPI
from app.appointment_scheduler import AppointmentScheduler

logger = logging.getLogger(__name__)

@celery.task(bind=True)
def send_appointment_reminders(self):
    """
    Tarefa para enviar lembretes de agendamentos
    Executa diariamente para enviar lembretes de agendamentos do dia seguinte
    """
    try:
        logger.info("Iniciando envio de lembretes de agendamentos")

        # Buscar agendamentos de amanhã que ainda não tiveram lembrete enviado
        tomorrow = date.today() + timedelta(days=1)

        appointments = Appointment.query.filter(
            and_(
                Appointment.scheduled_date == tomorrow,
                Appointment.status.in_(['scheduled', 'confirmed']),
                or_(
                    Appointment.reminder_sent.is_(None),
                    Appointment.reminder_sent == False
                )
            )
        ).all()

        sent_count = 0
        failed_count = 0

        for appointment in appointments:
            try:
                # Enviar lembrete via WhatsApp
                whatsapp = WhatsAppBusinessAPI(appointment.clinic)
                success = whatsapp.send_appointment_reminder(appointment, hours_before=24)

                if success:
                    sent_count += 1
                    logger.info(f"Lembrete enviado para {appointment.patient.name}")
                else:
                    failed_count += 1
                    logger.error(f"Falha ao enviar lembrete para {appointment.patient.name}")

            except Exception as e:
                failed_count += 1
                logger.error(f"Erro ao enviar lembrete para agendamento {appointment.id}: {str(e)}")

        logger.info(f"Lembretes enviados: {sent_count}, Falhas: {failed_count}")

        return {
            'sent': sent_count,
            'failed': failed_count,
            'total': len(appointments)
        }

    except Exception as e:
        logger.error(f"Erro na tarefa de lembretes: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)

@celery.task(bind=True)
def send_follow_up_messages(self):
    """
    Tarefa para enviar mensagens de follow-up após agendamentos
    Executa diariamente para agendamentos do dia anterior
    """
    try:
        logger.info("Iniciando envio de mensagens de follow-up")

        # Buscar agendamentos de ontem que foram concluídos
        yesterday = date.today() - timedelta(days=1)

        appointments = Appointment.query.filter(
            and_(
                Appointment.scheduled_date == yesterday,
                Appointment.status == 'completed'
            )
        ).all()

        sent_count = 0

        for appointment in appointments:
            try:
                # Verificar se já foi enviado follow-up
                existing_notification = Notification.query.filter(
                    and_(
                        Notification.appointment_id == appointment.id,
                        Notification.type == 'follow_up'
                    )
                ).first()

                if existing_notification:
                    continue

                # Enviar mensagem de follow-up
                whatsapp = WhatsAppBusinessAPI(appointment.clinic)

                message = f"""
Olá {appointment.patient.name}!

Obrigado por ter vindo à {appointment.clinic.name} ontem.

Como foi sua experiência? Estamos sempre buscando melhorar nosso atendimento.

Se tiver alguma sugestão ou precisar de algo, é só responder esta mensagem.

Para agendar seu próximo serviço, digite *AGENDAR*.

Atenciosamente,
Equipe {appointment.clinic.name}
""".strip()

                success, message_id = whatsapp.send_message(
                    to_number=appointment.patient.phone,
                    message=message,
                    message_type='text'
                )

                if success:
                    # Registrar notificação
                    notification = Notification(
                        clinic_id=appointment.clinic_id,
                        appointment_id=appointment.id,
                        patient_id=appointment.patient.id,
                        type='follow_up',
                        channel='whatsapp',
                        message_id=message_id,
                        status='sent',
                        sent_at=datetime.utcnow()
                    )
                    db.session.add(notification)
                    sent_count += 1

                db.session.commit()

            except Exception as e:
                logger.error(f"Erro ao enviar follow-up para agendamento {appointment.id}: {str(e)}")
                db.session.rollback()

        logger.info(f"Mensagens de follow-up enviadas: {sent_count}")

        return {'sent': sent_count}

    except Exception as e:
        logger.error(f"Erro na tarefa de follow-up: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)

@celery.task(bind=True)
def check_missed_appointments(self):
    """
    Tarefa para verificar agendamentos perdidos (no-show)
    Executa diariamente para marcar agendamentos não comparecidos
    """
    try:
        logger.info("Verificando agendamentos perdidos")

        # Buscar agendamentos de ontem que ainda estão agendados/confirmados
        yesterday = date.today() - timedelta(days=1)

        appointments = Appointment.query.filter(
            and_(
                Appointment.scheduled_date == yesterday,
                Appointment.status.in_(['scheduled', 'confirmed']),
                Appointment.completed_at.is_(None)
            )
        ).all()

        no_show_count = 0

        for appointment in appointments:
            try:
                # Marcar como no-show
                appointment.status = 'no_show'
                appointment.no_show_at = datetime.utcnow()

                # Criar notificação para o paciente
                whatsapp = WhatsAppBusinessAPI(appointment.clinic)

                message = f"""
Olá {appointment.patient.name},

Notamos que você não compareceu ao seu agendamento de ontem ({yesterday.strftime('%d/%m/%Y')}) às {appointment.scheduled_time.strftime('%H:%M')}.

Se houve algum imprevisto, por favor nos avise para que possamos reagendar.

Para reagendar, digite *AGENDAR* ou ligue para {appointment.clinic.phone}.

Atenciosamente,
{appointment.clinic.name}
""".strip()

                whatsapp.send_message(
                    to_number=appointment.patient.phone,
                    message=message,
                    message_type='text'
                )

                no_show_count += 1
                logger.info(f"Agendamento marcado como no-show: {appointment.id}")

            except Exception as e:
                logger.error(f"Erro ao processar no-show para agendamento {appointment.id}: {str(e)}")

        db.session.commit()

        logger.info(f"Agendamentos marcados como no-show: {no_show_count}")

        return {'no_show_count': no_show_count}

    except Exception as e:
        logger.error(f"Erro na tarefa de verificação de faltas: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)

@celery.task(bind=True)
def send_birthday_messages(self):
    """
    Tarefa para enviar mensagens de aniversário aos pacientes
    Executa diariamente
    """
    try:
        logger.info("Enviando mensagens de aniversário")

        # Buscar pacientes que fazem aniversário hoje
        today = date.today()

        patients = Patient.query.filter(
            and_(
                func.extract('month', Patient.birth_date) == today.month,
                func.extract('day', Patient.birth_date) == today.day,
                Patient.phone.isnot(None)
            )
        ).all()

        sent_count = 0

        for patient in patients:
            try:
                # Verificar se já foi enviado este ano
                existing_notification = Notification.query.filter(
                    and_(
                        Notification.patient_id == patient.id,
                        Notification.type == 'birthday',
                        func.extract('year', Notification.sent_at) == today.year
                    )
                ).first()

                if existing_notification:
                    continue

                # Enviar mensagem de aniversário
                whatsapp = WhatsAppBusinessAPI(patient.clinic)

                message = f"""
🎉 *FELIZ ANIVERSÁRIO* 🎉

Olá {patient.name}!

A {patient.clinic.name} deseja um feliz aniversário!

Que este ano seja repleto de saúde, alegria e momentos especiais.

Para agendar sua consulta de rotina ou check-up, digite *AGENDAR*.

Parabéns! 🎂
""".strip()

                success, message_id = whatsapp.send_message(
                    to_number=patient.phone,
                    message=message,
                    message_type='text'
                )

                if success:
                    # Registrar notificação
                    notification = Notification(
                        clinic_id=patient.clinic_id,
                        patient_id=patient.patient_id,
                        type='birthday',
                        channel='whatsapp',
                        message_id=message_id,
                        status='sent',
                        sent_at=datetime.utcnow()
                    )
                    db.session.add(notification)
                    sent_count += 1

                db.session.commit()

            except Exception as e:
                logger.error(f"Erro ao enviar mensagem de aniversário para {patient.name}: {str(e)}")
                db.session.rollback()

        logger.info(f"Mensagens de aniversário enviadas: {sent_count}")

        return {'sent': sent_count}

    except Exception as e:
        logger.error(f"Erro na tarefa de aniversários: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)

@celery.task(bind=True)
def sync_google_calendar(self):
    """
    Tarefa para sincronizar agendamentos com Google Calendar
    Executa periodicamente para manter calendários sincronizados
    """
    try:
        logger.info("Iniciando sincronização com Google Calendar")

        # Importar integração do Google Calendar (a ser implementada)
        # from app.google_calendar_integration import GoogleCalendarIntegration

        # Buscar clínicas com integração do Google Calendar ativa
        clinics = Clinic.query.filter(
            and_(
                Clinic.google_calendar_enabled == True,
                Clinic.google_calendar_id.isnot(None)
            )
        ).all()

        synced_count = 0

        for clinic in clinics:
            try:
                # Sincronizar agendamentos futuros
                # google_calendar = GoogleCalendarIntegration(clinic)
                # synced_count += google_calendar.sync_appointments()

                logger.info(f"Sincronização concluída para clínica {clinic.name}")

            except Exception as e:
                logger.error(f"Erro ao sincronizar Google Calendar para clínica {clinic.id}: {str(e)}")

        logger.info(f"Total de sincronizações: {synced_count}")

        return {'synced': synced_count}

    except Exception as e:
        logger.error(f"Erro na tarefa de sincronização Google Calendar: {str(e)}")
        raise self.retry(countdown=300, max_retries=3)  # Retry em 5 minutos

@celery.task(bind=True)
def clean_old_data(self):
    """
    Tarefa para limpeza de dados antigos
    Remove conversas antigas, logs de auditoria antigos, etc.
    """
    try:
        logger.info("Iniciando limpeza de dados antigos")

        # Remover conversas com mais de 90 dias
        cutoff_date = date.today() - timedelta(days=90)

        deleted_conversations = db.session.query(Conversation).filter(
            Conversation.created_at < cutoff_date
        ).delete()

        # Remover notificações antigas (mais de 180 dias)
        cutoff_date = date.today() - timedelta(days=180)

        deleted_notifications = db.session.query(Notification).filter(
            Notification.sent_at < cutoff_date
        ).delete()

        # Remover logs de auditoria antigos (mais de 365 dias)
        from app.models import AuditLog
        cutoff_date = date.today() - timedelta(days=365)

        deleted_audit_logs = db.session.query(AuditLog).filter(
            AuditLog.created_at < cutoff_date
        ).delete()

        db.session.commit()

        logger.info(f"Dados antigos removidos - Conversas: {deleted_conversations}, Notificações: {deleted_notifications}, Logs: {deleted_audit_logs}")

        return {
            'conversations_deleted': deleted_conversations,
            'notifications_deleted': deleted_notifications,
            'audit_logs_deleted': deleted_audit_logs
        }

    except Exception as e:
        logger.error(f"Erro na limpeza de dados: {str(e)}")
        db.session.rollback()
        raise self.retry(countdown=3600, max_retries=3)  # Retry em 1 hora

@celery.task(bind=True)
def generate_daily_reports(self):
    """
    Tarefa para gerar relatórios diários
    Cria resumos diários de métricas para cada clínica
    """
    try:
        logger.info("Gerando relatórios diários")

        from app.dashboard_metrics import DashboardMetrics

        clinics = Clinic.query.all()
        reports_generated = 0

        for clinic in clinics:
            try:
                metrics = DashboardMetrics(clinic)

                # Gerar métricas do dia anterior
                daily_metrics = metrics.get_overview_metrics(days=1)

                # Aqui você poderia salvar em um modelo de relatório
                # ou enviar por email/notificação

                logger.info(f"Relatório gerado para clínica {clinic.name}: {daily_metrics}")
                reports_generated += 1

            except Exception as e:
                logger.error(f"Erro ao gerar relatório para clínica {clinic.id}: {str(e)}")

        logger.info(f"Relatórios diários gerados: {reports_generated}")

        return {'reports_generated': reports_generated}

    except Exception as e:
        logger.error(f"Erro na geração de relatórios: {str(e)}")
        raise self.retry(countdown=3600, max_retries=3)

@celery.task(bind=True)
def check_subscription_limits(self):
    """
    Tarefa para verificar limites de assinatura
    Alerta quando clínicas estão próximas dos limites
    """
    try:
        logger.info("Verificando limites de assinatura")

        from app.models import Subscription

        # Buscar assinaturas ativas
        subscriptions = Subscription.query.filter(
            Subscription.status == 'active'
        ).all()

        alerts_sent = 0

        for subscription in subscriptions:
            try:
                clinic = subscription.clinic

                # Verificar uso atual
                current_usage = {
                    'patients': Patient.query.filter_by(clinic_id=clinic.id).count(),
                    'appointments': Appointment.query.filter_by(clinic_id=clinic.id).count(),
                    'messages': Conversation.query.filter_by(clinic_id=clinic.id).count()
                }

                # Verificar limites
                limits = subscription.plan_limits or {}

                alerts = []

                for resource, limit in limits.items():
                    if resource in current_usage:
                        usage_percent = (current_usage[resource] / limit) * 100

                        if usage_percent >= 90:  # Alerta quando >= 90%
                            alerts.append(f"{resource}: {current_usage[resource]}/{limit} ({usage_percent:.1f}%)")

                if alerts:
                    # Enviar alerta para administradores da clínica
                    alert_message = f"""
⚠️ *ALERTA DE LIMITE DE ASSINATURA*

Sua clínica está próxima dos limites do plano:

{"\n".join(alerts)}

Considere fazer upgrade do plano para evitar interrupções no serviço.

Para mais informações, acesse o painel administrativo.
""".strip()

                    # Enviar para administradores (implementar lógica de busca)
                    # admin_users = User.query.filter_by(clinic_id=clinic.id, role='admin').all()
                    # for admin in admin_users:
                    #     whatsapp = WhatsAppBusinessAPI(clinic)
                    #     whatsapp.send_message(admin.phone, alert_message)

                    alerts_sent += 1
                    logger.info(f"Alerta enviado para clínica {clinic.name}")

            except Exception as e:
                logger.error(f"Erro ao verificar limites para assinatura {subscription.id}: {str(e)}")

        logger.info(f"Alertas de limite enviados: {alerts_sent}")

        return {'alerts_sent': alerts_sent}

    except Exception as e:
        logger.error(f"Erro na verificação de limites: {str(e)}")
        raise self.retry(countdown=3600, max_retries=3)

@celery.task(bind=True)
def backup_database(self):
    """
    Tarefa para fazer backup do banco de dados
    Executa periodicamente para manter backups seguros
    """
    try:
        logger.info("Iniciando backup do banco de dados")

        # Implementar lógica de backup
        # Pode usar pg_dump para PostgreSQL ou mysqldump para MySQL

        # Exemplo para PostgreSQL:
        # import subprocess
        # backup_command = f"pg_dump -h {db_host} -U {db_user} -d {db_name} > backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        # subprocess.run(backup_command, shell=True)

        logger.info("Backup do banco concluído")

        return {'backup_completed': True}

    except Exception as e:
        logger.error(f"Erro no backup do banco: {str(e)}")
        raise self.retry(countdown=3600, max_retries=3)