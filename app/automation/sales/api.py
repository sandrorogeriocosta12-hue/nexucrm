    """
    API para automação de vendas.
    """

    from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
    from typing import List, Dict, Any, Optional
    from datetime import datetime, timedelta
    import json

    from app.automation.sales.sequences import (
    SalesAutomationService,
    SequenceBuilder,
    SequenceFactory,
    SequenceAPI,
    EmailSequence,
    SequenceExecution,
    SequenceLog
    )
    from app.automation.sales.email_templates import TemplateManager, TemplateFactory
    from app.core.database import get_db
    from app.core.auth import get_current_user
    from app.core.email import EmailService
    from app.schemas.automation import (
    SequenceCreate,
    SequenceUpdate,
    SequenceResponse,
    ExecutionResponse,
    StepResponse,
    PerformanceReport
    )

    router = APIRouter(prefix="/sales/automation", tags=["sales-automation"])

@router.get("/health")
async def health_check():
    """Health check da automação de vendas."""
    return {
    "status": "healthy",
    "service": "sales-automation",
    "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/sequences", response_model=SequenceResponse)
async def create_sequence(
    sequence_data: SequenceCreate,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    db = Depends(get_db)
    ):
    """Cria nova sequência de email."""
    try:
        email_service = EmailService()
        automation_service = SalesAutomationService(db, email_service)
        api = SequenceAPI(automation_service)

# Adiciona criador
        sequence_data_dict = sequence_data.dict()
        sequence_data_dict["created_by"] = current_user["id"]

        result = await api.create_sequence_endpoint(sequence_data_dict)

        if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

# Busca sequência criada
        sequence = db.query(EmailSequence).get(result["sequence_id"])

    return SequenceResponse(
    id=sequence.id,
    name=sequence.name,
    description=sequence.description,
    trigger=sequence.trigger,
    status=sequence.status,
    steps=sequence.steps,
    stats=sequence.stats,
    created_at=sequence.created_at,
    updated_at=sequence.updated_at
    )

    except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@router.get("/sequences", response_model=List[SequenceResponse])
async def list_sequences(
    status: Optional[str] = None,
    current_user: Dict = Depends(get_current_user),
    db = Depends(get_db)
    ):
    """Lista todas as sequências."""
    query = db.query(EmailSequence)

    if status:
        query = query.filter(EmailSequence.status == status)

# Filtra por usuário (apenas suas sequências ou compartilhadas)
        query = query.filter(
        (EmailSequence.created_by == current_user["id"]) |
        (EmailSequence.metadata.contains({"shared_with": current_user["id"]}))
        )

        sequences = query.order_by(EmailSequence.created_at.desc()).all()

    return [
    SequenceResponse(
    id=seq.id,
    name=seq.name,
    description=seq.description,
    trigger=seq.trigger,
    status=seq.status,
    steps=seq.steps,
    stats=seq.stats,
    created_at=seq.created_at,
    updated_at=seq.updated_at
    )
    for seq in sequences
    ]

@router.get("/sequences/{sequence_id}", response_model=SequenceResponse)
async def get_sequence(
    sequence_id: int,
    current_user: Dict = Depends(get_current_user),
    db = Depends(get_db)
    ):
        """Obtém detalhes de uma sequência."""
        sequence = db.query(EmailSequence).get(sequence_id)

        if not sequence:
        raise HTTPException(status_code=404, detail="Sequência não encontrada")

# Verifica permissão
        if (sequence.created_by != current_user["id"] and
        current_user["id"] not in sequence.metadata.get("shared_with", [])):
        raise HTTPException(status_code=403, detail="Sem permissão para acessar esta sequência")

    return SequenceResponse(
    id=sequence.id,
    name=sequence.name,
    description=sequence.description,
    trigger=sequence.trigger,
    status=sequence.status,
    steps=sequence.steps,
    stats=sequence.stats,
    created_at=sequence.created_at,
    updated_at=sequence.updated_at
    )

@router.put("/sequences/{sequence_id}", response_model=SequenceResponse)
async def update_sequence(
    sequence_id: int,
    update_data: SequenceUpdate,
    current_user: Dict = Depends(get_current_user),
    db = Depends(get_db)
    ):
        """Atualiza uma sequência."""
        sequence = db.query(EmailSequence).get(sequence_id)

        if not sequence:
        raise HTTPException(status_code=404, detail="Sequência não encontrada")

# Verifica permissão
        if sequence.created_by != current_user["id"]:
        raise HTTPException(status_code=403, detail="Somente o criador pode editar a sequência")

# Atualiza campos
        for field, value in update_data.dict(exclude_unset=True).items():
            if hasattr(sequence, field):
                setattr(sequence, field, value)

                sequence.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(sequence)

            return SequenceResponse(
            id=sequence.id,
            name=sequence.name,
            description=sequence.description,
            trigger=sequence.trigger,
            status=sequence.status,
            steps=sequence.steps,
            stats=sequence.stats,
            created_at=sequence.created_at,
            updated_at=sequence.updated_at
            )

@router.delete("/sequences/{sequence_id}")
async def delete_sequence(
            sequence_id: int,
            current_user: Dict = Depends(get_current_user),
            db = Depends(get_db)
            ):
                """Exclui uma sequência."""
                sequence = db.query(EmailSequence).get(sequence_id)

                if not sequence:
                raise HTTPException(status_code=404, detail="Sequência não encontrada")

# Verifica permissão
                if sequence.created_by != current_user["id"]:
                raise HTTPException(status_code=403, detail="Somente o criador pode excluir a sequência")

# Verifica se há execuções ativas
                active_executions = db.query(SequenceExecution).filter(
                SequenceExecution.sequence_id == sequence_id,
                SequenceExecution.status.in_(["active", "paused"])
                ).count()

                if active_executions > 0:
                raise HTTPException(
                status_code=400,
                detail=f"Não é possível excluir sequência com {active_executions} execuções ativas"
                )

                db.delete(sequence)
                db.commit()

            return {"message": "Sequência excluída com sucesso"}

@router.post("/sequences/{sequence_id}/activate")
async def activate_sequence(
            sequence_id: int,
            current_user: Dict = Depends(get_current_user),
            db = Depends(get_db)
            ):
                """Ativa uma sequência."""
                sequence = db.query(EmailSequence).get(sequence_id)

                if not sequence:
                raise HTTPException(status_code=404, detail="Sequência não encontrada")

                if sequence.created_by != current_user["id"]:
                raise HTTPException(status_code=403, detail="Sem permissão")

                sequence.status = "active"
                sequence.updated_at = datetime.utcnow()
                db.commit()

            return {"message": "Sequência ativada com sucesso"}

@router.post("/sequences/{sequence_id}/deactivate")
async def deactivate_sequence(
            sequence_id: int,
            current_user: Dict = Depends(get_current_user),
            db = Depends(get_db)
            ):
                """Desativa uma sequência."""
                sequence = db.query(EmailSequence).get(sequence_id)

                if not sequence:
                raise HTTPException(status_code=404, detail="Sequência não encontrada")

                if sequence.created_by != current_user["id"]:
                raise HTTPException(status_code=403, detail="Sem permissão")

                sequence.status = "paused"
                sequence.updated_at = datetime.utcnow()
                db.commit()

            return {"message": "Sequência desativada com sucesso"}

@router.post("/sequences/{sequence_id}/execute/{lead_id}")
async def execute_sequence(
            sequence_id: int,
            lead_id: int,
            background_tasks: BackgroundTasks,
            current_user: Dict = Depends(get_current_user),
            db = Depends(get_db)
            ):
                """Inicia execução de sequência para um lead."""
                email_service = EmailService()
                automation_service = SalesAutomationService(db, email_service)
                api = SequenceAPI(automation_service)

                result = await api.start_sequence_endpoint(sequence_id, lead_id)

                if not result["success"]:
                raise HTTPException(status_code=400, detail=result["message"])

            return {
            "message": result["message"],
            "execution_id": result["execution_id"]
            }

@router.get("/executions/{execution_id}")
async def get_execution(
            execution_id: int,
            current_user: Dict = Depends(get_current_user),
            db = Depends(get_db)
            ):
                """Obtém detalhes de uma execução."""
                execution = db.query(SequenceExecution).get(execution_id)

                if not execution:
                raise HTTPException(status_code=404, detail="Execução não encontrada")

# Verifica permissão através da sequência
                sequence = db.query(EmailSequence).get(execution.sequence_id)
                if not sequence:
                raise HTTPException(status_code=404, detail="Sequência não encontrada")

                if (sequence.created_by != current_user["id"] and
                current_user["id"] not in sequence.metadata.get("shared_with", [])):
                raise HTTPException(status_code=403, detail="Sem permissão")

                logs = db.query(SequenceLog).filter(
                SequenceLog.execution_id == execution_id
                ).order_by(SequenceLog.created_at.desc()).all()

            return ExecutionResponse(
            id=execution.id,
            sequence_id=execution.sequence_id,
            lead_id=execution.lead_id,
            current_step=execution.current_step,
            status=execution.status,
            steps_completed=execution.steps_completed,
            steps_pending=execution.steps_pending,
            started_at=execution.started_at,
            last_step_at=execution.last_step_at,
            completed_at=execution.completed_at,
            logs=[
            {
            "id": log.id,
            "step_id": log.step_id,
            "action": log.action,
            "status": log.status,
            "details": log.details,
            "created_at": log.created_at
            }
            for log in logs
            ]
            )

@router.get("/sequences/{sequence_id}/executions")
async def list_executions(
            sequence_id: int,
            status: Optional[str] = None,
            current_user: Dict = Depends(get_current_user),
            db = Depends(get_db)
            ):
                """Lista execuções de uma sequência."""
                sequence = db.query(EmailSequence).get(sequence_id)

                if not sequence:
                raise HTTPException(status_code=404, detail="Sequência não encontrada")

                if (sequence.created_by != current_user["id"] and
                current_user["id"] not in sequence.metadata.get("shared_with", [])):
                raise HTTPException(status_code=403, detail="Sem permissão")

                query = db.query(SequenceExecution).filter(
                SequenceExecution.sequence_id == sequence_id
                )

                if status:
                    query = query.filter(SequenceExecution.status == status)

                    executions = query.order_by(SequenceExecution.started_at.desc()).all()

                return [
                {
                "id": exec.id,
                "lead_id": exec.lead_id,
                "current_step": exec.current_step,
                "status": exec.status,
                "started_at": exec.started_at,
                "last_step_at": exec.last_step_at,
                "completed_at": exec.completed_at
                }
                for exec in executions
                ]

@router.post("/executions/{execution_id}/pause")
async def pause_execution(
                execution_id: int,
                current_user: Dict = Depends(get_current_user),
                db = Depends(get_db)
                ):
                    """Pausa uma execução."""
                    email_service = EmailService()
                    automation_service = SalesAutomationService(db, email_service)
                    api = SequenceAPI(automation_service)

                    result = await api.pause_sequence_endpoint(execution_id)

                    if not result["success"]:
                    raise HTTPException(status_code=400, detail=result["message"])

                return {"message": result["message"]}

@router.post("/executions/{execution_id}/resume")
async def resume_execution(
                execution_id: int,
                current_user: Dict = Depends(get_current_user),
                db = Depends(get_db)
                ):
                    """Retoma uma execução pausada."""
                    email_service = EmailService()
                    automation_service = SalesAutomationService(db, email_service)
                    api = SequenceAPI(automation_service)

                    result = await api.resume_sequence_endpoint(execution_id)

                    if not result["success"]:
                    raise HTTPException(status_code=400, detail=result["message"])

                return {"message": result["message"]}

@router.get("/sequences/{sequence_id}/stats")
async def get_sequence_stats(
                sequence_id: int,
                current_user: Dict = Depends(get_current_user),
                db = Depends(get_db)
                ):
                    """Obtém estatísticas de uma sequência."""
                    email_service = EmailService()
                    automation_service = SalesAutomationService(db, email_service)
                    api = SequenceAPI(automation_service)

                    result = await api.get_stats_endpoint(sequence_id)

                    if not result["success"]:
                    raise HTTPException(status_code=400, detail=result["message"])

                return result["stats"]

@router.get("/sequences/{sequence_id}/report")
async def get_sequence_report(
                sequence_id: int,
                current_user: Dict = Depends(get_current_user),
                db = Depends(get_db)
                ):
                    """Obtém relatório de performance de uma sequência."""
                    email_service = EmailService()
                    automation_service = SalesAutomationService(db, email_service)
                    api = SequenceAPI(automation_service)

                    result = await api.get_report_endpoint(sequence_id)

                    if not result["success"]:
                    raise HTTPException(status_code=400, detail=result["message"])

                return PerformanceReport(**result["report"])

@router.get("/templates")
async def list_templates(
                current_user: Dict = Depends(get_current_user)
                ):
                    """Lista todos os templates disponíveis."""
                    template_manager = TemplateManager()
                    templates = template_manager.list_templates()

                return {
                "templates": templates,
                "count": len(templates)
                }

@router.post("/templates/preview")
async def preview_template(
                template_data: Dict[str, Any],
                current_user: Dict = Depends(get_current_user)
                ):
                    """Preview de template com dados de exemplo."""
                    template_manager = TemplateManager()

                    try:
                        template_name = template_data["template_name"]
                        context = template_data.get("context", {})

# Adiciona dados padrão se não fornecidos
                        if "lead_name" not in context:
                            context["lead_name"] = "João Silva"
                            if "company_name" not in context:
                                context["company_name"] = "Empresa Exemplo"

                                result = template_manager.render_template(template_name, context)

                            return {
                            "subject": result["subject"],
                            "html": result["html"],
                            "text": result["text"]
                            }

                        except Exception as e:
                        raise HTTPException(status_code=400, detail=str(e))

@router.get("/dashboard")
async def get_dashboard(
                        current_user: Dict = Depends(get_current_user),
                        db = Depends(get_db)
                        ):
                            """Dashboard de automação de vendas."""

# Estatísticas gerais
                            total_sequences = db.query(EmailSequence).filter(
                            EmailSequence.created_by == current_user["id"]
                            ).count()

                            active_sequences = db.query(EmailSequence).filter(
                            EmailSequence.created_by == current_user["id"],
                            EmailSequence.status == "active"
                            ).count()

                            total_executions = db.query(SequenceExecution).join(EmailSequence).filter(
                            EmailSequence.created_by == current_user["id"]
                            ).count()

                            active_executions = db.query(SequenceExecution).filter(
                            SequenceExecution.status == "active"
                            ).join(EmailSequence).filter(
                            EmailSequence.created_by == current_user["id"]
                            ).count()

# Emails enviados hoje
                            today = datetime.utcnow().date()
                            emails_today = db.query(SequenceLog).filter(
                            SequenceLog.action == "sent",
                            SequenceLog.created_at >= datetime.combine(today, datetime.min.time())
                            ).join(SequenceExecution).join(EmailSequence).filter(
                            EmailSequence.created_by == current_user["id"]
                            ).count()

# Taxa de abertura (últimos 7 dias)
                            week_ago = datetime.utcnow() - timedelta(days=7)

                            sent_last_week = db.query(SequenceLog).filter(
                            SequenceLog.action == "sent",
                            SequenceLog.created_at >= week_ago
                            ).join(SequenceExecution).join(EmailSequence).filter(
                            EmailSequence.created_by == current_user["id"]
                            ).count()

                            opened_last_week = db.query(SequenceLog).filter(
                            SequenceLog.action == "opened",
                            SequenceLog.created_at >= week_ago
                            ).join(SequenceExecution).join(EmailSequence).filter(
                            EmailSequence.created_by == current_user["id"]
                            ).count()

                            open_rate = (opened_last_week / sent_last_week * 100) if sent_last_week > 0 else 0

# Sequências mais recentes
                            recent_sequences = db.query(EmailSequence).filter(
                            EmailSequence.created_by == current_user["id"]
                            ).order_by(EmailSequence.created_at.desc()).limit(5).all()

# Execuções recentes
                            recent_executions = db.query(SequenceExecution).join(EmailSequence).filter(
                            EmailSequence.created_by == current_user["id"]
                            ).order_by(SequenceExecution.started_at.desc()).limit(10).all()

                        return {
                        "overview": {
                        "total_sequences": total_sequences,
                        "active_sequences": active_sequences,
                        "total_executions": total_executions,
                        "active_executions": active_executions,
                        "emails_sent_today": emails_today,
                        "open_rate_last_week": round(open_rate, 2)
                        },
                        "recent_sequences": [
                        {
                        "id": seq.id,
                        "name": seq.name,
                        "status": seq.status,
                        "steps_count": len(seq.steps) if seq.steps else 0,
                        "created_at": seq.created_at
                        }
                        for seq in recent_sequences
                        ],
                        "recent_executions": [
                        {
                        "id": exec.id,
                        "sequence_id": exec.sequence_id,
                        "lead_id": exec.lead_id,
                        "status": exec.status,
                        "current_step": exec.current_step,
                        "started_at": exec.started_at
                        }
                        for exec in recent_executions
                        ]
                        }

@router.post("/sequences/templates/{template_name}")
async def create_from_template(
                        template_name: str,
                        custom_data: Dict[str, Any],
                        current_user: Dict = Depends(get_current_user),
                        db = Depends(get_db)
                        ):
                            """Cria sequência a partir de template."""

                            templates = {
                            "onboarding": SequenceFactory.create_onboarding_sequence,
                            "nurturing": SequenceFactory.create_nurturing_sequence,
                            "reengagement": SequenceFactory.create_reengagement_sequence
                            }

                            if template_name not in templates:
                            raise HTTPException(
                            status_code=400,
                            detail=f"Template '{template_name}' não encontrado. Templates disponíveis: {list(templates.keys())}"
                            )

                            template_func = templates[template_name]
                            sequence_data = template_func(current_user["id"])

# Aplica customizações
                            if custom_data:
                                for key, value in custom_data.items():
                                    if key in sequence_data:
                                        sequence_data[key] = value

# Cria sequência
                                        email_service = EmailService()
                                        automation_service = SalesAutomationService(db, email_service)
                                        api = SequenceAPI(automation_service)

                                        result = await api.create_sequence_endpoint(sequence_data)

                                        if not result["success"]:
                                        raise HTTPException(status_code=400, detail=result["message"])

                                    return {
                                    "message": f"Sequência criada a partir do template '{template_name}'",
                                    "sequence_id": result["sequence_id"]
                                    }

@router.post("/sequences/{sequence_id}/clone")
async def clone_sequence(
                                    sequence_id: int,
                                    new_name: str,
                                    current_user: Dict = Depends(get_current_user),
                                    db = Depends(get_db)
                                    ):
                                        """Clona uma sequência existente."""
                                        original = db.query(EmailSequence).get(sequence_id)

                                        if not original:
                                        raise HTTPException(status_code=404, detail="Sequência original não encontrada")

# Verifica permissão
                                        if (original.created_by != current_user["id"] and
                                        current_user["id"] not in original.metadata.get("shared_with", [])):
                                        raise HTTPException(status_code=403, detail="Sem permissão para clonar esta sequência")

# Cria cópia
                                        new_sequence = EmailSequence(
                                        name=new_name,
                                        description=f"Cópia de: {original.description}" if original.description else None,
                                        trigger=original.trigger,
                                        trigger_conditions=original.trigger_conditions,
                                        steps=original.steps,
                                        status="draft",
                                        created_by=current_user["id"],
                                        stats={"total_sent": 0, "total_opened": 0, "total_clicked": 0, "conversion_rate": 0.0}
                                        )

                                        db.add(new_sequence)
                                        db.commit()
                                        db.refresh(new_sequence)

                                    return {
                                    "message": "Sequência clonada com sucesso",
                                    "new_sequence_id": new_sequence.id,
                                    "new_sequence_name": new_sequence.name
                                    }

@router.get("/analytics/performance")
async def get_performance_analytics(
                                    days: int = 30,
                                    current_user: Dict = Depends(get_current_user),
                                    db = Depends(get_db)
                                    ):
                                        """Analytics de performance das sequências."""

                                        start_date = datetime.utcnow() - timedelta(days=days)

# Dados por dia
                                        daily_data = {}

# Busca logs agrupados por dia
                                        from sqlalchemy import func, Date

                                        daily_stats = db.query(
                                        func.date(SequenceLog.created_at).label('date'),
                                        func.count(SequenceLog.id).label('total'),
                                        func.sum(func.case([(SequenceLog.action == 'sent', 1)], else_=0)).label('sent'),
                                        func.sum(func.case([(SequenceLog.action == 'opened', 1)], else_=0)).label('opened'),
                                        func.sum(func.case([(SequenceLog.action == 'clicked', 1)], else_=0)).label('clicked'),
                                        func.sum(func.case([(SequenceLog.action == 'replied', 1)], else_=0)).label('replied')
                                        ).join(SequenceExecution).join(EmailSequence).filter(
                                        EmailSequence.created_by == current_user["id"],
                                        SequenceLog.created_at >= start_date
                                        ).group_by(func.date(SequenceLog.created_at)).order_by('date').all()

                                        for stat in daily_stats:
                                            date_str = stat.date.isoformat()
                                            daily_data[date_str] = {
                                            "sent": stat.sent or 0,
                                            "opened": stat.opened or 0,
                                            "clicked": stat.clicked or 0,
                                            "replied": stat.replied or 0,
                                            "open_rate": (stat.opened / stat.sent * 100) if stat.sent > 0 else 0,
                                            "click_rate": (stat.clicked / stat.sent * 100) if stat.sent > 0 else 0,
                                            "reply_rate": (stat.replied / stat.sent * 100) if stat.sent > 0 else 0
                                            }

# Sequências com melhor performance
                                            sequences = db.query(EmailSequence).filter(
                                            EmailSequence.created_by == current_user["id"],
                                            EmailSequence.status == "active"
                                            ).all()

                                            sequence_performance = []

                                            for seq in sequences:
                                                if seq.stats and seq.stats.get("total_sent", 0) > 0:
                                                    conversion_rate = seq.stats.get("conversion_rate", 0)
                                                    sequence_performance.append({
                                                    "id": seq.id,
                                                    "name": seq.name,
                                                    "total_sent": seq.stats.get("total_sent", 0),
                                                    "total_opened": seq.stats.get("total_opened", 0),
                                                    "total_clicked": seq.stats.get("total_clicked", 0),
                                                    "conversion_rate": conversion_rate,
                                                    "open_rate": (seq.stats.get("total_opened", 0) / seq.stats.get("total_sent", 0) * 100) if seq.stats.get("total_sent", 0) > 0 else 0
                                                    })

                                                    sequence_performance.sort(key=lambda x: x["conversion_rate"], reverse=True)

# Métricas gerais
                                                    total_sent = sum([d["sent"] for d in daily_data.values()])
                                                    total_opened = sum([d["opened"] for d in daily_data.values()])
                                                    total_clicked = sum([d["clicked"] for d in daily_data.values()])

                                                    overall_open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
                                                    overall_click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0

                                                return {
                                                "period": {
                                                "start_date": start_date.date().isoformat(),
                                                "end_date": datetime.utcnow().date().isoformat(),
                                                "days": days
                                                },
                                                "overall": {
                                                "total_sent": total_sent,
                                                "total_opened": total_opened,
                                                "total_clicked": total_clicked,
                                                "open_rate": round(overall_open_rate, 2),
                                                "click_rate": round(overall_click_rate, 2)
                                                },
                                                "daily_data": daily_data,
                                                "top_sequences": sequence_performance[:5],
                                                "worst_sequences": sequence_performance[-5:] if len(sequence_performance) >= 5 else []
                                                }

@router.post("/sequences/builder")
async def build_sequence_interactively(
                                                steps_data: List[Dict[str, Any]],
                                                current_user: Dict = Depends(get_current_user)
                                                ):
                                                    """Constrói sequência interativamente usando SequenceBuilder."""

                                                    if not steps_data:
                                                    raise HTTPException(status_code=400, detail="É necessário pelo menos um passo")

                                                    builder = SequenceBuilder(
                                                    name=steps_data[0].get("sequence_name", "Nova Sequência"),
                                                    trigger=steps_data[0].get("trigger", "lead_created")
                                                    )

                                                    for i, step_data in enumerate(steps_data):
                                                        step = {
                                                        "step_id": i + 1,
                                                        "name": step_data.get("name", f"Passo {i + 1}"),
                                                        "subject": step_data.get("subject", ""),
                                                        "template_name": step_data.get("template_name", "onboarding_welcome"),
                                                        "delay_hours": step_data.get("delay_hours", 24),
                                                        "conditions": step_data.get("conditions", {}),
                                                        "actions": step_data.get("actions", []),
                                                        "is_active": step_data.get("is_active", True)
                                                        }
                                                        builder.add_step(step)

# Adiciona condições se fornecidas
                                                        conditions = steps_data[0].get("trigger_conditions", {})
                                                        for field, condition_list in conditions.items():
                                                            for condition in condition_list:
                                                                builder.add_condition(field, condition["operator"], condition["value"])

                                                                sequence_data = builder.build(current_user["id"])

                                                            return {
                                                            "sequence_data": sequence_data,
                                                            "steps_count": len(sequence_data["steps"]),
                                                            "preview": {
                                                            "name": sequence_data["name"],
                                                            "trigger": sequence_data["trigger"],
                                                            "total_duration_hours": sum([step.get("delay_hours", 0) for step in sequence_data["steps"]])
                                                            }
                                                            }

# Webhooks para eventos externos
@router.post("/webhooks/email-events")
async def handle_email_webhook(
                                                            webhook_data: Dict[str, Any],
                                                            background_tasks: BackgroundTasks,
                                                            db = Depends(get_db)
                                                            ):
                                                                """Webhook para receber eventos de email (abertura, clique, etc.)."""

                                                                event_type = webhook_data.get("event")
                                                                metadata = webhook_data.get("metadata", {})

                                                                if not event_type or not metadata:
                                                                return {"status": "ignored", "reason": "Dados incompletos"}

# Extrai IDs do metadata
                                                                execution_id = metadata.get("execution_id")
                                                                step_id = metadata.get("step_id")
                                                                lead_id = metadata.get("lead_id")

                                                                if not execution_id or not step_id:
                                                                return {"status": "ignored", "reason": "IDs necessários não encontrados"}

# Busca execução
                                                                execution = db.query(SequenceExecution).get(execution_id)
                                                                if not execution:
                                                                return {"status": "ignored", "reason": "Execução não encontrada"}

# Cria log do evento
                                                                log = SequenceLog(
                                                                execution_id=execution_id,
                                                                step_id=step_id,
                                                                action=event_type, # opened, clicked, replied, bounced
                                                                status="success",
                                                                details={
                                                                "webhook_data": webhook_data,
                                                                "received_at": datetime.utcnow().isoformat()
                                                                }
                                                                )

                                                                db.add(log)

# Atualiza estatísticas da sequência
                                                                sequence = db.query(EmailSequence).get(execution.sequence_id)
                                                                if sequence:
                                                                    stats = sequence.stats or {}

                                                                    if event_type == "opened":
                                                                        stats["total_opened"] = stats.get("total_opened", 0) + 1
                                                                    elif event_type == "clicked":
                                                                        stats["total_clicked"] = stats.get("total_clicked", 0) + 1
                                                                    elif event_type == "replied":
                                                                        stats["total_replied"] = stats.get("total_replied", 0) + 1

                                                                        sequence.stats = stats

                                                                        db.commit()

                                                                    return {"status": "processed", "execution_id": execution_id, "event": event_type}