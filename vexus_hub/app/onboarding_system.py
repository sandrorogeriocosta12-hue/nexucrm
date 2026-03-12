import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional
from app.models import db, Clinic, OnboardingTask, OnboardingStep, User


class OnboardingStepType(Enum):
    FORM = "form"
    VIDEO = "video"
    TASK = "task"
    INTEGRATION = "integration"
    APPROVAL = "approval"
    TRAINING = "training"


class OnboardingManager:
    """Sistema de onboarding automatizado por plano"""

    ONBOARDING_TEMPLATES = {'bronze': {'name': 'Onboarding Autônomo',
                                       'estimated_duration': '1 dia',
                                       'steps': [{'order': 1,
                                                  'type': OnboardingStepType.FORM.value,
                                                  'title': 'Informações da Clínica',
                                                  'description': 'Preencha os dados básicos da sua clínica',
                                                  'estimated_time': 10,
                                                  'required': True,
                                                  'form_fields': ['name',
                                                                  'phone',
                                                                  'address',
                                                                  'specialties']},
                                                 {'order': 2,
                                                  'type': OnboardingStepType.VIDEO.value,
                                                  'title': 'Tour pela Plataforma',
                                                  'description': 'Assista ao vídeo de introdução',
                                                  'estimated_time': 15,
                                                  'required': True,
                                                  'video_url': '/videos/tour-bronze.mp4'},
                                                 {'order': 3,
                                                  'type': OnboardingStepType.INTEGRATION.value,
                                                  'title': 'Configurar WhatsApp',
                                                  'description': 'Conecte sua conta do WhatsApp Business',
                                                  'estimated_time': 20,
                                                  'required': True,
                                                  'integration_type': 'whatsapp'},
                                                 {'order': 4,
                                                  'type': OnboardingStepType.TASK.value,
                                                  'title': 'Configurar Serviços',
                                                  'description': 'Adicione os serviços que sua clínica oferece',
                                                  'estimated_time': 30,
                                                  'required': True,
                                                  'task_type': 'configure_services'},
                                                 {'order': 5,
                                                  'type': OnboardingStepType.TRAINING.value,
                                                  'title': 'Treinamento de Chatbot',
                                                  'description': 'Aprenda a configurar respostas automáticas',
                                                  'estimated_time': 25,
                                                  'required': False,
                                                  'training_url': '/training/chatbot-basics'}]},
                            'silver': {'name': 'Onboarding Gerenciado',
                                       'estimated_duration': '3-5 dias',
                                       'steps': [{'order': 1,
                                                  'type': OnboardingStepType.FORM.value,
                                                  'title': 'Briefing Completo',
                                                  'description': 'Forneça informações detalhadas sobre sua clínica',
                                                  'estimated_time': 30,
                                                  'required': True,
                                                  'form_fields': ['brand_info',
                                                                  'target_audience',
                                                                  'current_marketing',
                                                                  'goals']},
                                                 {'order': 2,
                                                  'type': OnboardingStepType.APPROVAL.value,
                                                  'title': 'Reunião de Alinhamento',
                                                  'description': 'Agende uma reunião com nosso especialista',
                                                  'estimated_time': 60,
                                                  'required': True,
                                                  'approval_type': 'meeting'},
                                                 {'order': 3,
                                                  'type': OnboardingStepType.INTEGRATION.value,
                                                  'title': 'Configurações Avançadas',
                                                  'description': 'Configurar todas as integrações',
                                                  'estimated_time': 120,
                                                  'required': True,
                                                  'integrations': ['whatsapp',
                                                                   'google_calendar',
                                                                   'google_my_business']},
                                                 {'order': 4,
                                                  'type': OnboardingStepType.TASK.value,
                                                  'title': 'Configuração de Marketing',
                                                  'description': 'Nosso time configurará suas redes sociais',
                                                  'estimated_time': 180,
                                                  'required': True,
                                                  'task_type': 'marketing_setup'},
                                                 {'order': 5,
                                                  'type': OnboardingStepType.TRAINING.value,
                                                  'title': 'Treinamento Personalizado',
                                                  'description': 'Sessão de treinamento 1:1',
                                                  'estimated_time': 60,
                                                  'required': True,
                                                  'training_type': 'personal'}]},
                            'gold': {'name': 'Onboarding Premium',
                                     'estimated_duration': '7-10 dias',
                                     'steps': [{'order': 1,
                                                'type': OnboardingStepType.APPROVAL.value,
                                                'title': 'Workshop Estratégico',
                                                'description': 'Reunião com equipe multidisciplinar',
                                                'estimated_time': 120,
                                                'required': True,
                                                'participants': ['ceo',
                                                                 'marketing',
                                                                 'accounting',
                                                                 'operations']},
                                               {'order': 2,
                                                'type': OnboardingStepType.FORM.value,
                                                'title': 'Diagnóstico Completo',
                                                'description': 'Análise detalhada de processos atuais',
                                                'estimated_time': 60,
                                                'required': True,
                                                'form_fields': ['current_processes',
                                                                'pain_points',
                                                                'systems_in_use',
                                                                'kpis']},
                                               {'order': 3,
                                                'type': OnboardingStepType.INTEGRATION.value,
                                                'title': 'Integrações Personalizadas',
                                                'description': 'Desenvolvimento de integrações customizadas',
                                                'estimated_time': 480,
                                                'required': True,
                                                'integrations': ['whatsapp',
                                                                 'google_calendar',
                                                                 'erp_system',
                                                                 'crm_existing']},
                                               {'order': 4,
                                                'type': OnboardingStepType.TASK.value,
                                                'title': 'Implementação de Processos',
                                                'description': 'Nossa equipe implementa processos otimizados',
                                                'estimated_time': 720,
                                                'required': True,
                                                'task_type': 'process_implementation'},
                                               {'order': 5,
                                                'type': OnboardingStepType.TRAINING.value,
                                                'title': 'Treinamento em Grupo',
                                                'description': 'Treinamento para toda a equipe da clínica',
                                                'estimated_time': 120,
                                                'required': True,
                                                'training_type': 'group'},
                                               {'order': 6,
                                                'type': OnboardingStepType.APPROVAL.value,
                                                'title': 'Entrega e Go-Live',
                                                'description': 'Reunião final de entrega do projeto',
                                                'estimated_time': 60,
                                                'required': True,
                                                'approval_type': 'final_delivery'}]}}

    @staticmethod
    def start_onboarding(clinic_id: str, plan: str) -> bool:
        """
        Inicia processo de onboarding para uma clínica
        """
        try:
            clinic = Clinic.query.get(clinic_id)
            if not clinic:
                return False

            template = OnboardingManager.ONBOARDING_TEMPLATES.get(plan)
            if not template:
                return False

            # Criar steps do onboarding
            for step_data in template['steps']:
                step = OnboardingStep(
                    clinic_id=clinic_id,
                    order=step_data['order'],
                    type=step_data['type'],
                    title=step_data['title'],
                    description=step_data['description'],
                    estimated_time=step_data['estimated_time'],
                    required=step_data['required'],
                    config=json.dumps({k: v for k, v in step_data.items()
                                       if k not in ['order', 'type', 'title', 'description',
                                                    'estimated_time', 'required']}),
                    status='pending'
                )
                db.session.add(step)

            # Atualizar status da clínica
            clinic.onboarding_step = 1
            clinic.onboarding_started_at = datetime.utcnow()
            clinic.onboarding_plan = plan

            # Se for plano Prata ou Ouro, atribuir responsável
            if plan in ['silver', 'gold']:
                clinic.onboarding_manager_id = OnboardingManager._assign_onboarding_manager(
                    plan)

            # Se for Ouro, agendar workshop
            if plan == 'gold':
                OnboardingManager._schedule_strategy_workshop(clinic_id)

            db.session.commit()

            # Enviar email de início de onboarding
            OnboardingManager._send_onboarding_start_email(clinic, plan)

            return True

        except Exception as e:
            logger.error(f"Erro ao iniciar onboarding: {str(e)}")
            db.session.rollback()
            return False


@staticmethod
def complete_step(
        clinic_id: str,
        step_id: str,
        completed_by: str,
        notes: str = None) -> bool:
    """
    Completa um step do onboarding
    """
    try:
        step = OnboardingStep.query.get(step_id)
        if not step or step.clinic_id != clinic_id:
            return False

        # Marcar como completo
        step.status = 'completed'
        step.completed_by = completed_by
        step.completed_at = datetime.utcnow()
        step.notes = notes

        # Atualizar progresso da clínica
        clinic = Clinic.query.get(clinic_id)
        next_steps = OnboardingStep.query.filter_by(
            clinic_id=clinic_id,
            status='pending'
        ).order_by(OnboardingStep.order).all()

        if next_steps:
            clinic.onboarding_step = next_steps[0].order

        # Verificar se completou todos os steps
        pending_steps = OnboardingStep.query.filter_by(
            clinic_id=clinic_id,
            status='pending'
        ).count()

        if pending_steps == 0:
            OnboardingManager._complete_onboarding(clinic_id)

        db.session.commit()

        # Se for step importante, notificar responsável
        if step.required:
            OnboardingManager._notify_step_completion(step, clinic)

        return True

    except Exception as e:
        logger.error(f"Erro ao completar step: {str(e)}")
        db.session.rollback()
        return False


@staticmethod
def _complete_onboarding(clinic_id: str):
    """
    Finaliza o processo de onboarding
    """
    clinic = Clinic.query.get(clinic_id)

    clinic.onboarding_completed_at = datetime.utcnow()
    clinic.status = 'active'

    # Criar tarefa de follow-up
    follow_up_task = OnboardingTask(
        clinic_id=clinic_id,
        type='follow_up',
        title='Follow-up pós-onboarding',
        description='Agendar reunião de follow-up 7 dias após ativação',
        due_date=datetime.utcnow() + timedelta(days=7),
        priority='medium',
        assigned_to=clinic.onboarding_manager_id
    )
    db.session.add(follow_up_task)

    # Enviar email de boas-vindas final
    OnboardingManager._send_onboarding_complete_email(clinic)

    @staticmethod
    def _assign_onboarding_manager(plan: str) -> Optional[str]:
        """
        Atribui um gerente de onboarding baseado no plano
        """
        # Buscar gerentes disponíveis
        managers = User.query.filter_by(
            role='onboarding_manager',
            status='active'
        ).all()

        if not managers:
            return None

        # Atribuir baseado na carga de trabalho
        manager_loads = []
        for manager in managers:
            active_onboardings = Clinic.query.filter(
                Clinic.onboarding_manager_id == manager.id,
                Clinic.onboarding_completed_at.is_(None)
            ).count()

            manager_loads.append((manager.id, active_onboardings))

        return min(manager_loads, key=lambda x: x[1])[0]

    @staticmethod
    def _schedule_strategy_workshop(clinic_id: str):
        """Agenda workshop estratégico para plano Ouro"""
        clinic = Clinic.query.get(clinic_id)

        # Criar tarefa de workshop
        workshop_task = OnboardingTask(
            clinic_id=clinic_id,
            type='workshop',
            title='Workshop Estratégico',
            description='Reunião com equipe multidisciplinar para definir estratégia',
    due_date=datetime.utcnow() + timedelta(days=2),
    priority='high',
    assigned_to=clinic.onboarding_manager_id
        )
        db.session.add(workshop_task)

        # Enviar convites
        OnboardingManager._send_workshop_invites(clinic, workshop_task)

    @staticmethod
    def _send_onboarding_start_email(clinic: Clinic, plan: str):
        """Envia email de início de onboarding"""
        # Implementar integração com serviço de email
        pass
    def _send_onboarding_complete_email(clinic: Clinic):
        """Envia email de conclusão de onboarding"""
        pass


    @staticmethod
    def _notify_step_completion(step: OnboardingStep, clinic: Clinic):
        """Notifica responsável sobre conclusão de step"""
        pass


    @staticmethod
    def _send_workshop_invites(clinic: Clinic, workshop_task: OnboardingTask):
        """Envia convites para workshop"""
        pass


    @staticmethod
    def get_onboarding_progress(clinic_id: str) -> Dict:
        """
        Retorna progresso do onboarding
        """
        clinic = Clinic.query.get(clinic_id)
        if not clinic:
            return {}

        steps = OnboardingStep.query.filter_by(
            clinic_id=clinic_id
        ).order_by(OnboardingStep.order).all()

        total_steps = len(steps)
        completed_steps = sum(1 for s in steps if s.status == 'completed')
        progress = (completed_steps / total_steps * 100) if total_steps > 0 else 0

        steps_data = []
        for step in steps:
            steps_data.append({
                'id': step.id,
                'order': step.order,
                'title': step.title,
                'description': step.description,
                'type': step.type,
                'status': step.status,
                'completed_at': step.completed_at.strftime('%d/%m/%Y %H:%M') if step.completed_at else None,
                'estimated_time': step.estimated_time
            })

        # Próximas tarefas
        pending_tasks = OnboardingTask.query.filter_by(
            clinic_id=clinic_id,
            completed=False
        ).order_by(OnboardingTask.due_date).limit(5).all()

        tasks_data = []
        for task in pending_tasks:
            tasks_data.append({
                'id': task.id,
                'title': task.title,
                'due_date': task.due_date.strftime('%d/%m/%Y') if task.due_date else None,
                'priority': task.priority,
                'assigned_to': User.query.get(task.assigned_to).name if task.assigned_to else 'Não atribuído'
            })

        return {
            'clinic': {
                'name': clinic.name,
                'plan': clinic.onboarding_plan,
                'started_at': clinic.onboarding_started_at.strftime('%d/%m/%Y'),
                'current_step': clinic.onboarding_step,
                'manager': User.query.get(
                    clinic.onboarding_manager_id).name if clinic.onboarding_manager_id else None},
            'progress': {
                'percentage': round(
                    progress,
                    1),
                'completed_steps': completed_steps,
                'total_steps': total_steps,
                'estimated_time_remaining': OnboardingManager._estimate_time_remaining(steps)},
            'steps': steps_data,
            'pending_tasks': tasks_data}


    @staticmethod
    def _estimate_time_remaining(steps: List[OnboardingStep]) -> str:
        """Estima tempo restante do onboarding"""
        pending_steps = [s for s in steps if s.status == 'pending']

        if not pending_steps:
            return "0 horas"

        total_minutes = sum(s.estimated_time for s in pending_steps)

        if total_minutes < 60:
            return f"{total_minutes} minutos"
        elif total_minutes < 480:  # 8 horas
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours}h{minutes}min"
        else:
            days = total_minutes // 480
            hours = (total_minutes % 480) // 60
            return f"{days} dias e {hours} horas"
