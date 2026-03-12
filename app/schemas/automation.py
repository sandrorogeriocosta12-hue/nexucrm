"""
Schemas para automação de vendas.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class SequenceCreate(BaseModel):
    """Schema para criação de sequência."""

    name: str = Field(..., description="Nome da sequência")
    description: Optional[str] = Field(None, description="Descrição da sequência")
    trigger: str = Field(..., description="Trigger da sequência")
    trigger_conditions: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Condições do trigger"
    )
    steps: List[Dict[str, Any]] = Field(..., description="Passos da sequência")
    created_by: Optional[int] = Field(None, description="ID do criador")


class SequenceUpdate(BaseModel):
    """Schema para atualização de sequência."""

    name: Optional[str] = Field(None, description="Nome da sequência")
    description: Optional[str] = Field(None, description="Descrição da sequência")
    trigger: Optional[str] = Field(None, description="Trigger da sequência")
    trigger_conditions: Optional[Dict[str, Any]] = Field(
        None, description="Condições do trigger"
    )
    steps: Optional[List[Dict[str, Any]]] = Field(
        None, description="Passos da sequência"
    )


class SequenceResponse(BaseModel):
    """Schema para resposta de sequência."""

    id: int
    name: str
    description: Optional[str]
    trigger: str
    status: str
    steps: List[Dict[str, Any]]
    stats: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class ExecutionResponse(BaseModel):
    """Schema para resposta de execução."""

    id: int
    sequence_id: int
    lead_id: int
    current_step: int
    status: str
    steps_completed: Optional[List[Dict[str, Any]]]
    steps_pending: Optional[List[Dict[str, Any]]]
    started_at: datetime
    last_step_at: Optional[datetime]
    completed_at: Optional[datetime]
    logs: List[Dict[str, Any]]


class StepResponse(BaseModel):
    """Schema para resposta de passo."""

    step_id: int
    name: str
    subject: str
    template_name: str
    delay_hours: int
    conditions: Dict[str, Any]
    actions: List[str]
    is_active: bool


class PerformanceReport(BaseModel):
    """Schema para relatório de performance."""

    sequence_info: Dict[str, Any]
    summary: Dict[str, Any]
    step_analysis: Dict[str, Any]
    timeline: Dict[str, Any]
    recommendations: List[str]
