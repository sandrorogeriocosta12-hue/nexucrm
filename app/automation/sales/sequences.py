    """
    Sistema completo de automação de vendas com sequências de email.
    """

    from typing import Dict, List, Optional, Any
    from datetime import datetime, timedelta
    from enum import Enum
    import asyncio
    import json
    from dataclasses import dataclass
    from pydantic import BaseModel, Field, validator
    from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import relationship

    from app.core.database import Base
    from app.core.email import EmailService
    from app.core.templates import TemplateEngine
    from app.core.analytics import AnalyticsService

class SequenceTrigger(Enum):
    """Triggers para iniciar sequências de email."""
    LEAD_CREATED = "lead_created"
    LEAD_STATUS_CHANGED = "lead_status_changed"
    DEAL_CREATED = "deal_created"
    DEAL_STAGE_CHANGED = "deal_stage_changed"
    USER_ACTION = "user_action"
    SCHEDULED = "scheduled"
    API_CALL = "api_call"


class EmailSequenceStatus(Enum):
    """Status da sequência de email."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    COMPLETED = "completed"


class EmailStep(BaseModel):
    """Passo individual em uma sequência de email."""
    step_id: int = Field(..., description="ID do passo")
    name: str = Field(..., description="Nome do passo")
    subject: str = Field(..., description="Assunto do email")
    template_name: str = Field(..., description="Nome do template")
    delay_hours: int = Field(default=24, description="Delay após passo anterior")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Condições para execução")
    actions: List[str] = Field(default_factory=list, description="Ações após envio")
    is_active: bool = Field(default=True, description="Passo ativo")

@validator('delay_hours')
def validate_delay(cls, v):
        if v < 0:
            raise ValueError("Delay não pode ser negativo")
        if v > 720:  # 30 dias
            raise ValueError("Delay máximo é 720 horas (30 dias)")
        return v


class EmailSequence(Base):
    """Modelo de sequência de email."""
    __tablename__ = "email_sequences"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    trigger = Column(String(50), nullable=False)
    trigger_conditions = Column(JSON, default=dict)
    steps = Column(JSON, default=list)  # Lista de EmailStep como JSON
    status = Column(String(20), default="draft")
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    stats = Column(JSON, default=dict)

# Relacionamentos
    campaigns = relationship("Campaign", back_populates="sequence")
    executions = relationship("SequenceExecution", back_populates="sequence")


class SequenceExecution(Base):
    """Execução de sequência para um lead específico."""
    __tablename__ = "sequence_executions"

    id = Column(Integer, primary_key=True, index=True)
    sequence_id = Column(Integer, nullable=False)
    lead_id = Column(Integer, nullable=False)
    current_step = Column(Integer, default=0)
    status = Column(String(20), default="active")
    started_at = Column(DateTime, default=datetime.utcnow)
    last_step_at = Column(DateTime)
    completed_at = Column(DateTime)
    steps_completed = Column(JSON, default=list)
    steps_pending = Column(JSON, default=list)
    execution_metadata = Column(JSON, default=dict)

# Relacionamentos
    sequence = relationship("EmailSequence", back_populates="executions")
    logs = relationship("SequenceLog", back_populates="execution")


class SequenceLog(Base):
    """Log de execução da sequência."""
    __tablename__ = "sequence_logs"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, nullable=False)
    step_id = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False)  # sent, opened, clicked, replied, bounced
    status = Column(String(20), nullable=False)  # success, failed, pending
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

# Relacionamentos
    execution = relationship("SequenceExecution", back_populates="logs")


class SequenceBuilder:
    """Construtor de sequências de email."""

def __init__(self, name: str, trigger: SequenceTrigger):
        self.name = name
        self.trigger = trigger
        self.steps = []
        self.conditions = {}

def add_step(self, step: EmailStep) -> 'SequenceBuilder':
        """Adiciona passo à sequência."""
        self.steps.append(step.dict())
        return self

def add_condition(self, field: str, operator: str, value: Any) -> 'SequenceBuilder':
        """Adiciona condição ao trigger."""
        if field not in self.conditions:
            self.conditions[field] = []
        self.conditions[field].append({
            "operator": operator,
            "value": value
        })
        return self

def build(self, created_by: int) -> Dict[str, Any]:
        """Constrói a sequência final."""
        return {
    "name": self.name,
    "trigger": self.trigger.value,
    "trigger_conditions": self.conditions,
    "steps": self.steps,
    "created_by": created_by,
    "status": "draft",
    "stats": {
    "total_sent": 0,
    "total_opened": 0,
    "total_clicked": 0,
    "total_replied": 0,
    "conversion_rate": 0.0
    }
    }

class SalesAutomationService:
    """Serviço principal de automação de vendas."""

def __init__(self, db_session, email_service: EmailService):
        self.db = db_session
        self.email_service = email_service
        self.template_engine = TemplateEngine()
        self.analytics = AnalyticsService()

async def create_sequence(self, sequence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria nova sequência de email."""
        try:
            sequence = EmailSequence(**sequence_data)
            self.db.add(sequence)
            self.db.commit()
            self.db.refresh(sequence)

            await self.analytics.track_event(
                "sequence_created",
                {
                    "sequence_id": sequence.id,
                    "name": sequence.name,
                    "trigger": sequence.trigger,
                    "steps_count": len(sequence.steps)
                }
            )

            return {
                "success": True,
                "sequence_id": sequence.id,
                "message": "Sequência criada com sucesso"
            }

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erro ao criar sequência: {str(e)}")

async def start_sequence_for_lead(self, sequence_id: int, lead_id: int) -> Dict[str, Any]:
        """Inicia sequência para um lead específico."""
        try:
            sequence = self.db.query(EmailSequence).filter(
                EmailSequence.id == sequence_id,
                EmailSequence.status == "active"
            ).first()

            if not sequence:
                return {
                    "success": False,
                    "message": "Sequência não encontrada ou inativa"
                }

# Verifica se já existe execução ativa
            existing = self.db.query(SequenceExecution).filter(
                SequenceExecution.sequence_id == sequence_id,
                SequenceExecution.lead_id == lead_id,
                SequenceExecution.status.in_(["active", "paused"])
            ).first()

            if existing:
                return {
                    "success": False,
                    "message": "Sequência já está em execução para este lead"
                }

# Cria nova execução
            execution = SequenceExecution(
                sequence_id=sequence_id,
                lead_id=lead_id,
                current_step=0,
                status="active",
                steps_pending=sequence.steps,
                metadata={"started_by": "system"}
            )

            self.db.add(execution)
            self.db.commit()
            self.db.refresh(execution)

# Agenda primeiro email
            await self.schedule_next_step(execution.id)

            return {
                "success": True,
                "execution_id": execution.id,
                "message": "Sequência iniciada para o lead"
            }

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erro ao iniciar sequência: {str(e)}")

async def schedule_next_step(self, execution_id: int) -> None:
        """Agenda próximo passo da sequência."""
        execution = self.db.query(SequenceExecution).get(execution_id)
        if not execution or execution.status != "active":
            return

        sequence = self.db.query(EmailSequence).get(execution.sequence_id)
        if not sequence:
            return

        if execution.current_step >= len(sequence.steps):
# Sequência completa
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            self.db.commit()
            return

        current_step_data = sequence.steps[execution.current_step]
        step = EmailStep(**current_step_data)

# Calcula delay
        delay_hours = step.delay_hours
        execute_at = datetime.utcnow() + timedelta(hours=delay_hours)

# Cria task assíncrona
        asyncio.create_task(
            self.execute_step(
                execution_id=execution_id,
                step=step,
                execute_at=execute_at
            )
        )

# Log
        log = SequenceLog(
            execution_id=execution_id,
            step_id=step.step_id,
            action="scheduled",
            status="pending",
            details={
                "execute_at": execute_at.isoformat(),
                "delay_hours": delay_hours
            }
        )
        self.db.add(log)
        self.db.commit()

async def execute_step(self, execution_id: int, step: EmailStep, execute_at: datetime) -> None:
        """Executa passo específico da sequência."""
        try:
# Aguarda até o horário agendado
            now = datetime.utcnow()
            if execute_at > now:
                wait_seconds = (execute_at - now).total_seconds()
                await asyncio.sleep(wait_seconds)

            execution = self.db.query(SequenceExecution).get(execution_id)
            if not execution or execution.status != "active":
                return

# Busca lead
            lead = self.db.query(Lead).get(execution.lead_id)
            if not lead:
                return

# Prepara contexto para template
            context = {
                "lead": {
                    "name": lead.name,
                    "email": lead.email,
                    "company": lead.company,
                    "phone": lead.phone
                },
                "step": step.dict(),
                "execution": {
                    "id": execution.id,
                    "current_step": execution.current_step
                }
            }

            html_content = await self.template_engine.render(
                template_name=step.template_name,
                context=context
            )

# Envia email
            email_result = await self.email_service.send_email(
                to_email=lead.email,
                subject=step.subject,
                html_content=html_content,
                metadata={
                    "sequence_id": execution.sequence_id,
                    "execution_id": execution.id,
                    "step_id": step.step_id,
                    "lead_id": lead.id
                }
            )

# Atualiza execução
            execution.current_step += 1
            execution.last_step_at = datetime.utcnow()

            steps_completed = execution.steps_completed or []
            steps_completed.append({
                "step_id": step.step_id,
                "sent_at": datetime.utcnow().isoformat(),
                "email_id": email_result.get("email_id")
            })
            execution.steps_completed = steps_completed

# Log
            log = SequenceLog(
                execution_id=execution_id,
                step_id=step.step_id,
                action="sent",
                status="success" if email_result["success"] else "failed",
                details={
                    "email_result": email_result,
                    "context": context
                }
            )
            self.db.add(log)

# Atualiza estatísticas
            sequence = self.db.query(EmailSequence).get(execution.sequence_id)
            if sequence:
                stats = sequence.stats or {}
                stats["total_sent"] = stats.get("total_sent", 0) + 1
                sequence.stats = stats

            self.db.commit()

# Agenda próximo passo
            await self.schedule_next_step(execution_id)

# Executa ações pós-envio
            await self.execute_post_actions(execution_id, step)

        except Exception as e:
# Log de erro
            log = SequenceLog(
                execution_id=execution_id,
                step_id=step.step_id,
                action="error",
    status="failed",
                details={"error": str(e)}
            )
            self.db.add(log)
            self.db.commit()

async def execute_post_actions(self, execution_id: int, step: EmailStep) -> None:
        """Executa ações configuradas após envio do email."""
        execution = self.db.query(SequenceExecution).get(execution_id)
        if not execution:
            return

        for action in step.actions:
            try:
                if action == "update_lead_status":
                    lead = self.db.query(Lead).get(execution.lead_id)
                    if lead:
                        lead.status = "contacted"
                        lead.last_contacted = datetime.utcnow()

                elif action == "create_task":
                    task = Task(
                        title=f"Follow-up: {step.name}",
                        description=f"Follow-up do email: {step.subject}",
                        assigned_to=execution.metadata.get("owner_id"),
                        due_date=datetime.utcnow() + timedelta(days=2),
                        priority="medium"
                    )
                    self.db.add(task)

                elif action == "trigger_webhook":
                    webhook_url = step.conditions.get("webhook_url")
                    if webhook_url:
                        payload = {
                            "event": "email_sent",
                            "execution_id": execution_id,
                            "step_id": step.step_id,
                            "lead_id": execution.lead_id,
                            "timestamp": datetime.utcnow().isoformat()
                        }
# Em produção, usar httpx async
# await self.http_client.post(webhook_url, json=payload)

                self.db.commit()

            except Exception as e:
# Log erro na ação
                continue

async def pause_sequence(self, execution_id: int) -> Dict[str, Any]:
        """Pausa execução da sequência."""
        execution = self.db.query(SequenceExecution).get(execution_id)
        if not execution:
            return {"success": False, "message": "Execução não encontrada"}

        execution.status = "paused"
        self.db.commit()

        return {"success": True, "message": "Sequência pausada"}

async def resume_sequence(self, execution_id: int) -> Dict[str, Any]:
        """Retoma sequência pausada."""
        execution = self.db.query(SequenceExecution).get(execution_id)
        if not execution:
            return {"success": False, "message": "Execução não encontrada"}

        execution.status = "active"
        self.db.commit()

        await self.schedule_next_step(execution_id)

        return {"success": True, "message": "Sequência retomada"}

async def get_sequence_stats(self, sequence_id: int) -> Dict[str, Any]:
        """Obtém estatísticas da sequência."""
        sequence = self.db.query(EmailSequence).get(sequence_id)
        if not sequence:
            return {"success": False, "message": "Sequência não encontrada"}

        executions = self.db.query(SequenceExecution).filter(
            SequenceExecution.sequence_id == sequence_id
        ).all()

        stats = {
            "sequence": {
                "id": sequence.id,
                "name": sequence.name,
                "status": sequence.status,
                "steps_count": len(sequence.steps)
            },
            "executions": {
                "total": len(executions),
                "active": len([e for e in executions if e.status == "active"]),
                "completed": len([e for e in executions if e.status == "completed"]),
                "paused": len([e for e in executions if e.status == "paused"])
            },
            "performance": sequence.stats or {}
        }

        return {"success": True, "stats": stats}

def get_sequence_performance_report(self, sequence_id: int) -> Dict[str, Any]:
        """Gera relatório de performance da sequência."""
        sequence = self.db.query(EmailSequence).get(sequence_id)
        if not sequence:
            return {"success": False, "message": "Sequência não encontrada"}

        executions = self.db.query(SequenceExecution).filter(
            SequenceExecution.sequence_id == sequence_id
        ).all()

        logs = self.db.query(SequenceLog).filter(
            SequenceLog.execution_id.in_([e.id for e in executions])
        ).all()

# Análise simples
        total_sent = len(logs)
        total_opened = len([l for l in logs if l.action == "opened"])
        total_clicked = len([l for l in logs if l.action == "clicked"])

        report = {
            "sequence_info": {
                "id": sequence.id,
                "name": sequence.name,
                "trigger": sequence.trigger,
                "status": sequence.status
            },
            "summary": {
                "total_executions": len(executions),
                "total_emails_sent": total_sent,
                "total_opened": total_opened,
                "total_clicked": total_clicked,
                "open_rate": (total_opened / total_sent * 100) if total_sent > 0 else 0,
                "click_rate": (total_clicked / total_sent * 100) if total_sent > 0 else 0
            },
            "step_analysis": {},
            "timeline": {},
            "recommendations": self.generate_recommendations(sequence, {})
        }

        return {"success": True, "report": report}
        if len(sequence.steps) > 10:
            recommendations.append(
                f"Sequência muito longa ({len(sequence.steps)} passos). "
                "Considere dividir em múltiplas sequências mais curtas."
            )

        return recommendations


class SequenceAPI:
    """API para gerenciamento de sequências."""

def __init__(self, automation_service: SalesAutomationService):
        self.service = automation_service

async def create_sequence_endpoint(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint para criar nova sequência."""
        required_fields = ["name", "trigger", "steps", "created_by"]
        for field in required_fields:
            if field not in request_data:
                return {
                    "success": False,
                    "message": f"Campo obrigatório ausente: {field}"
                }

        return await self.service.create_sequence(request_data)

async def start_sequence_endpoint(self, sequence_id: int, lead_id: int) -> Dict[str, Any]:
        """Endpoint para iniciar sequência para um lead."""
        return await self.service.start_sequence_for_lead(sequence_id, lead_id)

async def get_stats_endpoint(self, sequence_id: int) -> Dict[str, Any]:
        """Endpoint para obter estatísticas da sequência."""
        return await self.service.get_sequence_stats(sequence_id)

async def get_report_endpoint(self, sequence_id: int) -> Dict[str, Any]:
        """Endpoint para obter relatório de performance."""
        return await self.service.get_sequence_performance_report(sequence_id)

async def pause_sequence_endpoint(self, execution_id: int) -> Dict[str, Any]:
        """Endpoint para pausar execução."""
        return await self.service.pause_sequence(execution_id)

async def resume_sequence_endpoint(self, execution_id: int) -> Dict[str, Any]:
        """Endpoint para retomar execução."""
        return await self.service.resume_sequence(execution_id)

# Template de exemplo para sequência de onboarding
    ONBOARDING_SEQUENCE_TEMPLATE = {
    "name": "Onboarding de Cliente - 7 Dias",
    "trigger": "deal_stage_changed",
    "trigger_conditions": {
    "new_stage": ["won", "closed_won"]
    },
    "steps": [
    {
    "step_id": 1,
    "name": "Boas-vindas",
    "subject": "🎉 Bem-vindo(a) ao Vexus Service, ${lead_name}!",
    "template_name": "onboarding_welcome",
    "delay_hours": 0,
    "actions": ["update_lead_status", "create_task"]
    },
    {
    "step_id": 2,
    "name": "Configuração Inicial",
    "subject": "Configuração Inicial do Vexus - Primeiros Passos",
    "template_name": "onboarding_setup",
    "delay_hours": 24,
    "actions": []
    },
    {
    "step_id": 3,
    "name": "Treinamento 1",
    "subject": "Como usar o dashboard do Vexus",
    "template_name": "onboarding_training_1",
    "delay_hours": 48,
    "actions": ["create_task"]
    },
    {
    "step_id": 4,
    "name": "Check-in",
    "subject": "Como está indo com o Vexus?",
    "template_name": "onboarding_checkin",
    "delay_hours": 72,
    "actions": []
    },
    {
    "step_id": 5,
    "name": "Treinamento 2",
    "subject": "Funcionalidades avançadas do Vexus",
    "template_name": "onboarding_training_2",
    "delay_hours": 96,
    "actions": ["create_task"]
    },
    {
    "step_id": 6,
    "name": "Solicitação de Feedback",
    "subject": "O que você acha do Vexus até agora?",
    "template_name": "onboarding_feedback",
    "delay_hours": 120,
    "actions": []
    },
    {
    "step_id": 7,
    "name": "Próximos Passos",
    "subject": "Continue sua jornada com o Vexus",
    "template_name": "onboarding_next_steps",
    "delay_hours": 144,
    "actions": ["trigger_webhook"]
    }
    ]
    }

# Template de exemplo para sequência de nurturing
    NURTURING_SEQUENCE_TEMPLATE = {
    "name": "Nurturing de Leads - 14 Dias",
    "trigger": "lead_created",
    "trigger_conditions": {
    "lead_score": [{"operator": "gte", "value": 50}]
    },
    "steps": [
    {
    "step_id": 1,
    "name": "Introdução",
    "subject": "${lead_name}, conheça o Vexus - Automação Inteligente de Vendas",
    "template_name": "nurturing_intro",
    "delay_hours": 0,
    "actions": []
    },
    {
    "step_id": 2,
    "name": "Benefícios",
    "subject": "Como o Vexus pode ajudar seu negócio",
    "template_name": "nurturing_benefits",
    "delay_hours": 24,
    "actions": []
    },
    {
    "step_id": 3,
    "name": "Estudo de Caso",
    "subject": "Como a Empresa X aumentou vendas em 300%",
    "template_name": "nurturing_case_study",
    "delay_hours": 48,
    "actions": []
    },
    {
    "step_id": 4,
    "name": "Demo",
    "subject": "Agende uma demonstração gratuita",
    "template_name": "nurturing_demo",
    "delay_hours": 72,
    "actions": ["create_task"]
    },
    {
    "step_id": 5,
    "name": "Follow-up",
    "subject": "Ainda tem dúvidas sobre o Vexus?",
    "template_name": "nurturing_followup",
    "delay_hours": 96,
    "actions": []
    },
    {
    "step_id": 6,
    "name": "Oferta Especial",
    "subject": "Oferta exclusiva para novos clientes",
    "template_name": "nurturing_offer",
    "delay_hours": 120,
    "actions": ["update_lead_status"]
    },
    {
    "step_id": 7,
    "name": "Última Chance",
    "subject": "Últimos dias da oferta especial",
    "template_name": "nurturing_last_chance",
    "delay_hours": 144,
    "actions": ["trigger_webhook"]
    }
    ]
    }

# Factory para criar sequências pré-configuradas
class SequenceFactory:
    """Factory para criar sequências padrão."""

@staticmethod
def create_onboarding_sequence(created_by: int) -> Dict[str, Any]:
        """Cria sequência de onboarding padrão."""
        sequence = ONBOARDING_SEQUENCE_TEMPLATE.copy()
        sequence["created_by"] = created_by
        return sequence

@staticmethod
def create_nurturing_sequence(created_by: int) -> Dict[str, Any]:
        """Cria sequência de nurturing padrão."""
        sequence = NURTURING_SEQUENCE_TEMPLATE.copy()
        sequence["created_by"] = created_by
        return sequence

@staticmethod
def create_reengagement_sequence(created_by: int) -> Dict[str, Any]:
        """Cria sequência de reengajamento."""
        return {
    "name": "Reengajamento de Clientes Inativos",
    "trigger": "user_action",
    "trigger_conditions": {
    "last_activity": [{"operator": "lt", "value": "30d"}]
    },
    "steps": [
    {
    "step_id": 1,
    "name": "Sentimos sua falta",
    "subject": "${lead_name}, sentimos sua falta no Vexus! 🥺",
    "template_name": "reengagement_miss_you",
    "delay_hours": 0,
    "actions": []
    },
    {
    "step_id": 2,
    "name": "Novidades",
    "subject": "O que há de novo no Vexus?",
    "template_name": "reengagement_whats_new",
    "delay_hours": 48,
    "actions": []
    },
    {
    "step_id": 3,
    "name": "Oferta de Retorno",
    "subject": "Presente para seu retorno",
    "template_name": "reengagement_welcome_back",
    "delay_hours": 96,
    "actions": ["update_lead_status"]
    }
    ],
    "created_by": created_by
    }

# Monitor de performance em tempo real
class SequenceMonitor:
    """Monitor de sequências em tempo real."""

def __init__(self, automation_service: SalesAutomationService):
        self.service = automation_service
        self.metrics = {
            "active_sequences": 0,
            "active_executions": 0,
            "emails_sent_today": 0,
            "avg_open_rate": 0.0,
            "avg_click_rate": 0.0,
    "top_performing_sequences": []
    }

async def start_monitoring(self):
        """Inicia monitoramento em tempo real."""
        while True:
            await self.update_metrics()
            await asyncio.sleep(60)  # Atualiza a cada minuto

async def update_metrics(self):
        """Atualiza métricas do monitor."""
# Busca sequências ativas
        active_sequences = self.service.db.query(EmailSequence).filter(
            EmailSequence.status == "active"
        ).count()

# Busca execuções ativas
        active_executions = self.service.db.query(SequenceExecution).filter(
            SequenceExecution.status == "active"
        ).count()

# Emails enviados hoje
        today = datetime.utcnow().date()
        emails_today = self.service.db.query(SequenceLog).filter(
            SequenceLog.action == "sent",
            SequenceLog.created_at >= datetime.combine(today, datetime.min.time())
        ).count()

# Calcula taxas médias
        logs_today = self.service.db.query(SequenceLog).filter(
            SequenceLog.created_at >= datetime.combine(today, datetime.min.time())
        ).all()

        sent_emails = [l for l in logs_today if l.action == "sent"]
        opened_emails = [l for l in logs_today if l.action == "opened"]
        clicked_emails = [l for l in logs_today if l.action == "clicked"]

        open_rate = (len(opened_emails) / len(sent_emails) * 100) if sent_emails else 0
        click_rate = (len(clicked_emails) / len(sent_emails) * 100) if sent_emails else 0

# Top sequências
        top_sequences = []
