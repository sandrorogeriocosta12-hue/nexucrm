"""
Agentes de IA inteligentes para automação do CRM
Cada agente é especializado em uma função específica
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import asyncio
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Tipos de agentes disponíveis"""
    LEAD_SCORING = "lead_scoring"
    PIPELINE_MANAGER = "pipeline_manager"
    CONVERSATION_ANALYZER = "conversation_analyzer"
    NEXT_BEST_ACTION = "next_best_action"
    PROPOSAL_GENERATOR = "proposal_generator"
    FOLLOWUP_SCHEDULER = "followup_scheduler"
    CHANNEL_OPTIMIZER = "channel_optimizer"


@dataclass
class AgentConfig:
    """Configuração de um agente"""
    agent_type: AgentType
    model: str = "gpt-4-turbo"
    temperature: float = 0.3
    max_tokens: int = 1000
    enabled: bool = True
    confidence_threshold: float = 0.7


class BaseAgent:
    """Classe base para todos os agentes"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.name = config.agent_type.value.replace("_", " ").title()
        
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa dados e retorna decisão"""
        raise NotImplementedError
    
    def _log_decision(self, decision: Dict[str, Any]):
        """Registra decisão do agente"""
        logger.info(f"Agent {self.name} made decision: {decision}")


class LeadScoringAgent(BaseAgent):
    """Agente para pontuação de leads com IA"""
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula score do lead baseado em múltiplos fatores"""
        
        lead_info = data.get('lead', {})
        
        # Simular scoring (em produção integrar com OpenAI)
        score = self._calculate_score(lead_info)
        
        result = {
            "score": score,
            "confidence": 0.92,
            "breakdown": {
                "product_fit": min(25, score * 0.3),
                "engagement": min(25, score * 0.25),
                "decision_power": min(20, score * 0.2),
                "urgency": min(15, score * 0.15),
                "budget": min(15, score * 0.1)
            },
            "key_indicators": self._extract_indicators(lead_info),
            "recommendations": self._generate_recommendations(score)
        }
        
        result.update({
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "lead_id": lead_info.get('id'),
            "model_used": self.config.model
        })
        
        self._log_decision(result)
        return result
    
    def _calculate_score(self, lead_info: Dict) -> int:
        """Calcula score do lead"""
        score = 50
        
        # Ajustes baseado em características
        if lead_info.get('company_size') == 'enterprise':
            score += 20
        elif lead_info.get('company_size') == 'medium':
            score += 15
        
        if lead_info.get('budget_confirmed'):
            score += 15
        
        if lead_info.get('decision_maker'):
            score += 10
        
        if lead_info.get('urgency') == 'high':
            score += 10
        
        return min(100, max(0, score))
    
    def _extract_indicators(self, lead_info: Dict) -> List[str]:
        """Extrai indicadores-chave"""
        indicators = []
        
        if lead_info.get('budget_confirmed'):
            indicators.append("Budget confirmado")
        if lead_info.get('decision_maker'):
            indicators.append("Tomador de decisão")
        if lead_info.get('urgency') == 'high':
            indicators.append("Urgência alta")
        
        return indicators
    
    def _generate_recommendations(self, score: int) -> List[str]:
        """Gera recomendações baseado no score"""
        if score >= 80:
            return [
                "Enviar proposta customizada",
                "Agendar reunião com executivo",
                "Prioritizar follow-up"
            ]
        elif score >= 60:
            return [
                "Enviar mais informações",
                "Agendar demo",
                "Incluir em nurture sequence"
            ]
        else:
            return [
                "Adicionar à newsletter",
                "Criar conteúdo educativo",
                "Follow-up em 2 semanas"
            ]


class PipelineManagerAgent(BaseAgent):
    """Agente que gerencia movimento no pipeline"""
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decide para qual etapa mover o lead"""
        lead_score = data.get('lead_score', 50)
        conversation_context = data.get('conversation_context', '')
        
        # Regras baseadas em score e contexto
        action = self._determine_action(lead_score, conversation_context)
        
        return {
            "action": action,
            "confidence": 0.8,
            "reason": f"Score: {lead_score}",
            "timestamp": datetime.now().isoformat()
        }
    
    def _determine_action(self, score: int, context: str) -> str:
        """Determina ação baseado em score e contexto"""
        context_lower = context.lower()
        
        if score >= 80 and "proposta" in context_lower:
            return "move_to_closing"
        elif score >= 70 and "dúvida" in context_lower:
            return "move_to_negotiation"
        elif score >= 50 and "informação" in context_lower:
            return "send_more_info"
        elif score < 30:
            return "move_to_cold"
        
        return "no_action"


class ConversationAnalyzerAgent(BaseAgent):
    """Analisa conversas para extrair intenções e sentimentos"""
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa conversa e extrai insights"""
        conversation = data.get('conversation', '')
        
        return {
            "intentions": self._analyze_intention(conversation),
            "sentiment": self._analyze_sentiment(conversation),
            "entities": self._extract_entities(conversation),
            "urgency_level": self._calculate_urgency(conversation),
            "keywords": self._extract_keywords(conversation)
        }
    
    def _analyze_intention(self, text: str) -> List[Dict]:
        """Analisa intenções na conversa"""
        text_lower = text.lower()
        intentions = []
        
        if any(word in text_lower for word in ['agendar', 'marcar', 'schedule']):
            intentions.append({"type": "schedule", "confidence": 0.9})
        elif any(word in text_lower for word in ['preço', 'custo', 'price', 'valor']):
            intentions.append({"type": "pricing", "confidence": 0.9})
        elif any(word in text_lower for word in ['dúvida', 'pergunta', 'question', 'doubt']):
            intentions.append({"type": "question", "confidence": 0.85})
        else:
            intentions.append({"type": "information", "confidence": 0.7})
        
        return intentions
    
    def _analyze_sentiment(self, text: str) -> Dict:
        """Analisa sentimento da conversa"""
        # Simples análise de sentimento
        positive_words = ['ótimo', 'perfeito', 'excelente', 'gostei', 'adorei']
        negative_words = ['ruim', 'péssimo', 'não gostei', 'decepção']
        
        score = 0.5  # Neutro por padrão
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in positive_words):
            score = 0.8
        elif any(word in text_lower for word in negative_words):
            score = 0.2
        
        return {
            "score": score,
            "label": "positive" if score > 0.6 else "negative" if score < 0.4 else "neutral"
        }
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extrai entidades importantes"""
        entities = []
        
        # Simples extração (em produção usar NER)
        if 'reunião' in text.lower():
            entities.append("meeting")
        if 'orçamento' in text.lower():
            entities.append("budget")
        if 'equipe' in text.lower():
            entities.append("team")
        
        return entities
    
    def _calculate_urgency(self, text: str) -> str:
        """Calcula nível de urgência"""
        urgent_words = ['urgente', 'rápido', 'hoje', 'agora', 'immediate', 'asap']
        
        if any(word in text.lower() for word in urgent_words):
            return "high"
        
        return "normal"
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrai palavras-chave"""
        # Simples extração (em produção usar TF-IDF)
        keywords = []
        
        important_words = ['serviço', 'produto', 'preço', 'suporte', 'integração']
        
        for word in important_words:
            if word in text.lower():
                keywords.append(word)
        
        return keywords


class AgentOrchestrator:
    """Orquestrador que gerencia múltiplos agentes"""
    
    def __init__(self):
        self.agents: Dict[AgentType, BaseAgent] = {}
        self._register_agents()
    
    def _register_agents(self):
        """Registra todos os agentes disponíveis"""
        agents_config = {
            AgentType.LEAD_SCORING: AgentConfig(AgentType.LEAD_SCORING),
            AgentType.PIPELINE_MANAGER: AgentConfig(AgentType.PIPELINE_MANAGER),
            AgentType.CONVERSATION_ANALYZER: AgentConfig(AgentType.CONVERSATION_ANALYZER),
        }
        
        agent_classes = {
            AgentType.LEAD_SCORING: LeadScoringAgent,
            AgentType.PIPELINE_MANAGER: PipelineManagerAgent,
            AgentType.CONVERSATION_ANALYZER: ConversationAnalyzerAgent,
        }
        
        for agent_type, config in agents_config.items():
            agent_class = agent_classes.get(agent_type)
            if agent_class:
                self.agents[agent_type] = agent_class(config)
    
    async def orchestrate(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Orquestra múltiplos agentes para processar um lead"""
        results = {}
        
        # Executar agentes em paralelo
        tasks = []
        for agent_type, agent in self.agents.items():
            if agent.config.enabled:
                tasks.append(self._run_agent(agent, lead_data, agent_type))
        
        # Aguardar todos os agentes
        agent_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Consolidar resultados
        for agent_type, result in zip(self.agents.keys(), agent_results):
            if not isinstance(result, Exception):
                results[agent_type.value] = result
        
        # Tomar decisão final
        final_decision = self._make_final_decision(results)
        
        return {
            "agent_decisions": results,
            "final_decision": final_decision,
            "timestamp": datetime.now().isoformat(),
            "lead_id": lead_data.get('lead', {}).get('id')
        }
    
    async def _run_agent(self, agent: BaseAgent, data: Dict, agent_type: AgentType):
        """Executa um agente individualmente"""
        try:
            return await agent.process(data)
        except Exception as e:
            logger.error(f"Agent {agent_type.value} failed: {e}")
            return {"error": str(e), "agent": agent_type.value}
    
    def _make_final_decision(self, agent_results: Dict) -> Dict:
        """Combina resultados de todos os agentes para decisão final"""
        
        lead_score = agent_results.get('lead_scoring', {}).get('score', 50)
        pipeline_action = agent_results.get('pipeline_manager', {}).get('action', 'no_action')
        conversation = agent_results.get('conversation_analyzer', {})
        
        return {
            "overall_score": lead_score,
            "recommended_phase": self._get_phase_from_score(lead_score),
            "next_action": pipeline_action,
            "urgency": conversation.get('urgency_level', 'normal'),
            "follow_up_required": lead_score >= 50,
            "confidence": 0.85
        }
    
    def _get_phase_from_score(self, score: int) -> str:
        """Retorna fase recomendada baseado no score"""
        if score >= 80:
            return "proposal"
        elif score >= 60:
            return "qualification"
        elif score >= 40:
            return "nurture"
        else:
            return "cold"


__all__ = [
    'AgentType',
    'AgentConfig',
    'BaseAgent',
    'LeadScoringAgent',
    'PipelineManagerAgent',
    'ConversationAnalyzerAgent',
    'AgentOrchestrator'
]
