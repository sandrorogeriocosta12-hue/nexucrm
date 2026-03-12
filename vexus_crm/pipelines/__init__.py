"""
Pipeline visual com automações inteligentes (estilo Pipefy)
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CardStatus(Enum):
    """Status dos cards no pipeline"""
    BACKLOG = "backlog"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"


@dataclass
class PipelineField:
    """Campo personalizado no pipeline"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: str = "text"
    required: bool = False
    options: List[str] = field(default_factory=list)
    position: int = 0


@dataclass
class PipelinePhase:
    """Fase do pipeline"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    color: str = "#4CAF50"
    position: int = 0
    automations: List[Dict] = field(default_factory=list)
    fields: List[PipelineField] = field(default_factory=list)


@dataclass
class PipelineCard:
    """Card no pipeline (representa um lead/deal)"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    phase_id: str = ""
    status: CardStatus = CardStatus.IN_PROGRESS
    fields: Dict[str, Any] = field(default_factory=dict)
    assigned_to: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    due_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    ai_insights: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def lead_score(self) -> int:
        """Score do lead baseado em IA"""
        return self.ai_insights.get('score', 50)
    
    @property
    def priority(self) -> str:
        """Prioridade calculada automaticamente"""
        score = self.lead_score
        if score >= 80:
            return "critical"
        elif score >= 60:
            return "high"
        elif score >= 40:
            return "medium"
        else:
            return "low"


class VisualPipeline:
    """Pipeline visual com automações inteligentes"""
    
    def __init__(self, name: str):
        self.id = str(uuid.uuid4())
        self.name = name
        self.phases: List[PipelinePhase] = []
        self.cards: Dict[str, PipelineCard] = {}
        self.automations: List[Dict] = []
        self.created_at = datetime.now()
        
        self._create_default_pipeline()
    
    def _create_default_pipeline(self):
        """Cria pipeline padrão de vendas"""
        phases = [
            PipelinePhase(
                name="📥 Leads",
                description="Novos leads capturados",
                color="#FF9800",
                position=0
            ),
            PipelinePhase(
                name="📞 Qualificação",
                description="Análise e pontuação por IA",
                color="#2196F3",
                position=1
            ),
            PipelinePhase(
                name="🤝 Proposta",
                description="Envio de propostas personalizadas",
                color="#9C27B0",
                position=2
            ),
            PipelinePhase(
                name="💼 Negociação",
                description="Negociação e ajustes",
                color="#FF5722",
                position=3
            ),
            PipelinePhase(
                name="✅ Fechado",
                description="Deal concluído",
                color="#4CAF50",
                position=4
            ),
            PipelinePhase(
                name="❌ Perdido",
                description="Deals perdidos",
                color="#F44336",
                position=5
            )
        ]
        
        self.phases = phases
    
    def add_card(self, title: str, phase_name: str = "Leads", **kwargs) -> PipelineCard:
        """Adiciona um novo card ao pipeline"""
        
        phase = next((p for p in self.phases if p.name == phase_name), None)
        if not phase:
            phase = self.phases[0] if self.phases else None
        
        card = PipelineCard(
            title=title,
            phase_id=phase.id if phase else "",
            fields=kwargs.get('fields', {}),
            tags=kwargs.get('tags', []),
            assigned_to=kwargs.get('assigned_to', []),
            due_date=kwargs.get('due_date')
        )
        
        self.cards[card.id] = card
        logger.info(f"Card created: {card.id} - {title}")
        
        return card
    
    def move_card(self, card_id: str, target_phase_name: str) -> bool:
        """Move card para outra fase"""
        
        card = self.cards.get(card_id)
        if not card:
            return False
        
        target_phase = next((p for p in self.phases if p.name == target_phase_name), None)
        
        if not target_phase:
            return False
        
        card.phase_id = target_phase.id
        card.updated_at = datetime.now()
        logger.info(f"Card moved: {card_id} -> {target_phase_name}")
        
        return True
    
    def get_dashboard_data(self) -> Dict:
        """Retorna dados para dashboard"""
        cards_by_phase = {}
        
        for phase in self.phases:
            phase_cards = [c for c in self.cards.values() if c.phase_id == phase.id]
            cards_by_phase[phase.name] = {
                "count": len(phase_cards),
                "cards": [
                    {
                        "id": card.id,
                        "title": card.title,
                        "score": card.lead_score,
                        "priority": card.priority,
                        "assigned_to": card.assigned_to
                    }
                    for card in phase_cards
                ]
            }
        
        total_cards = len(self.cards)
        won_phase = next((p for p in self.phases if p.name == "✅ Fechado"), None)
        won_cards = len([c for c in self.cards.values() if c.phase_id == won_phase.id]) if won_phase else 0
        
        conversion_rate = (won_cards / total_cards * 100) if total_cards > 0 else 0
        
        return {
            "pipeline_id": self.id,
            "pipeline_name": self.name,
            "total_cards": total_cards,
            "cards_by_phase": cards_by_phase,
            "conversion_rate": round(conversion_rate, 2),
            "average_lead_score": self._calculate_average_score()
        }
    
    def _calculate_average_score(self) -> float:
        """Calcula score médio dos leads"""
        scores = [card.lead_score for card in self.cards.values()]
        return sum(scores) / len(scores) if scores else 0


__all__ = ['CardStatus', 'PipelineField', 'PipelinePhase', 'PipelineCard', 'VisualPipeline']
