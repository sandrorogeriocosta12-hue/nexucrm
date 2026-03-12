"""
Analytics e inteligência de negócio para CRM
"""

from typing import Dict, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PipelineAnalytics:
    """Analytics para pipeline visual"""
    
    def __init__(self, pipeline):
        self.pipeline = pipeline
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas do pipeline"""
        
        total_cards = len(self.pipeline.cards)
        
        # Contar por fase
        cards_by_phase = {}
        for phase in self.pipeline.phases:
            phase_cards = [c for c in self.pipeline.cards.values() if c.phase_id == phase.id]
            cards_by_phase[phase.name] = len(phase_cards)
        
        # Taxa de conversão
        won_phase = next((p for p in self.pipeline.phases if "✅" in p.name), None)
        won_cards = len([c for c in self.pipeline.cards.values() 
                        if c.phase_id == won_phase.id]) if won_phase else 0
        
        conversion_rate = (won_cards / total_cards * 100) if total_cards > 0 else 0
        
        # Score médio
        scores = [c.lead_score for c in self.pipeline.cards.values()]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        return {
            "total_cards": total_cards,
            "cards_by_phase": cards_by_phase,
            "conversion_rate": round(conversion_rate, 2),
            "average_score": round(avg_score, 2),
            "timestamp": datetime.now().isoformat()
        }


class LeadAnalytics:
    """Analytics para leads"""
    
    @staticmethod
    def calculate_lead_value(lead: Dict) -> float:
        """Calcula valor estimado de um lead"""
        
        base_value = 100  # Valor mínimo de qualquer lead
        
        # Ajustar baseado em critérios
        if lead.get('company_size') == 'enterprise':
            base_value *= 5
        elif lead.get('company_size') == 'medium':
            base_value *= 3
        
        if lead.get('budget_confirmed'):
            base_value *= 1.5
        
        return round(base_value, 2)
    
    @staticmethod
    def calculate_close_probability(lead_score: int) -> float:
        """Calcula probabilidade de fechar o deal"""
        
        # Fórmula simples
        probability = (lead_score / 100) * 0.9  # Máximo 90%
        
        return round(probability, 2)


__all__ = ['PipelineAnalytics', 'LeadAnalytics']
