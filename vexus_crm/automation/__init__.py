"""
Builder de fluxos de automação visual (drag-and-drop)
Inspirado em Botconversa e Pipefy
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class BlockType(Enum):
    """Tipos de blocos disponíveis"""
    START = "start"
    MESSAGE = "message"
    QUESTION = "question"
    CONDITION = "condition"
    WAIT = "wait"
    ACTION = "action"
    ASSIGN = "assign"
    WEBHOOK = "webhook"
    AI_ANALYSIS = "ai_analysis"
    SCORING = "scoring"


@dataclass
class Block:
    """Bloco individual no fluxo"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: BlockType = BlockType.START
    position: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0})
    config: Dict[str, Any] = field(default_factory=dict)
    next_blocks: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "position": self.position,
            "config": self.config,
            "next_blocks": self.next_blocks
        }


@dataclass
class Connection:
    """Conexão entre blocos"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_block_id: str = ""
    target_block_id: str = ""
    condition: Optional[str] = None


class FlowBuilder:
    """Construtor de fluxos de automação"""
    
    def __init__(self):
        self.blocks: Dict[str, Block] = {}
        self.connections: List[Connection] = []
        self.start_block_id: Optional[str] = None
    
    def create_block(self, block_type: BlockType, **kwargs) -> Block:
        """Cria um novo bloco"""
        block = Block(
            type=block_type,
            position=kwargs.get('position', {"x": 0, "y": 0}),
            config=kwargs.get('config', {})
        )
        
        self.blocks[block.id] = block
        
        # Se for o primeiro bloco, definir como início
        if not self.start_block_id:
            self.start_block_id = block.id
        
        return block
    
    def connect(self, source_block: Block, target_block: Block, condition: Optional[str] = None):
        """Conecta dois blocos"""
        connection = Connection(
            source_block_id=source_block.id,
            target_block_id=target_block.id,
            condition=condition
        )
        
        self.connections.append(connection)
        source_block.next_blocks.append(target_block.id)
    
    def create_whatsapp_flow(self, flow_name: str) -> Dict:
        """Cria fluxo típico de WhatsApp como no Botconversa"""
        
        # Bloco inicial
        start = self.create_block(
            BlockType.START,
            config={
                "trigger": "whatsapp_message",
                "welcome_message": "Olá! 👋 Como posso ajudar você hoje?"
            }
        )
        
        # Menu de opções
        menu = self.create_block(
            BlockType.QUESTION,
            position={"x": 200, "y": 0},
            config={
                "question": "O que você está buscando?",
                "options": [
                    {"label": "🗓️ Agendar consulta", "value": "schedule"},
                    {"label": "💰 Conhecer preços", "value": "prices"},
                    {"label": "👥 Falar com atendente", "value": "human"},
                    {"label": "📚 Ver mais informações", "value": "info"}
                ],
                "variable_name": "user_interest"
            }
        )
        
        # Conectar início ao menu
        self.connect(start, menu)
        
        # AI Analysis
        ai_analysis = self.create_block(
            BlockType.AI_ANALYSIS,
            position={"x": 600, "y": 0},
            config={
                "analyze_intent": True,
                "analyze_sentiment": True,
                "extract_entities": True
            }
        )
        
        # Connect menu to AI
        self.connect(menu, ai_analysis)
        
        # Bloco de scoring
        scoring = self.create_block(
            BlockType.SCORING,
            position={"x": 800, "y": 0},
            config={
                "model": "lead_scoring_v1",
                "min_score_for_human": 70,
                "auto_assign": True
            }
        )
        self.connect(ai_analysis, scoring)
        
        return self.to_dict()
    
    def to_dict(self) -> Dict:
        """Exporta fluxo para dicionário"""
        return {
            "id": str(uuid.uuid4()),
            "name": "WhatsApp Automation Flow",
            "created_at": datetime.now().isoformat(),
            "blocks": [block.to_dict() for block in self.blocks.values()],
            "connections": [
                {
                    "id": conn.id,
                    "source": conn.source_block_id,
                    "target": conn.target_block_id,
                    "condition": conn.condition
                }
                for conn in self.connections
            ],
            "start_block": self.start_block_id,
            "metadata": {
                "version": "1.0",
                "block_count": len(self.blocks),
                "has_ai": any(b.type == BlockType.AI_ANALYSIS for b in self.blocks.values())
            }
        }
    
    def execute(self, contact_data: Dict) -> Dict:
        """Executa o fluxo para um contato"""
        execution_id = str(uuid.uuid4())
        current_block_id = self.start_block_id
        execution_path = []
        collected_data = {}
        
        iterations = 0
        max_iterations = 20  # Evitar loops infinitos
        
        while current_block_id and iterations < max_iterations:
            iterations += 1
            block = self.blocks.get(current_block_id)
            if not block:
                break
            
            # Executar bloco
            result = self._execute_block(block, contact_data, collected_data)
            
            # Registrar execução
            execution_path.append({
                "block_id": block.id,
                "block_type": block.type.value,
                "timestamp": datetime.now().isoformat(),
                "result": result
            })
            
            # Coletar dados
            if result.get("data"):
                collected_data.update(result["data"])
            
            # Determinar próximo bloco
            next_block_id = self._get_next_block(block, result)
            current_block_id = next_block_id
        
        return {
            "execution_id": execution_id,
            "contact_id": contact_data.get("id"),
            "execution_path": execution_path,
            "collected_data": collected_data,
            "final_score": collected_data.get("lead_score"),
            "completed_at": datetime.now().isoformat()
        }
    
    def _execute_block(self, block: Block, contact_data: Dict, collected_data: Dict) -> Dict:
        """Executa um bloco individual"""
        
        if block.type == BlockType.MESSAGE:
            return {"status": "message_sent", "content": block.config.get("message", "")}
        
        elif block.type == BlockType.QUESTION:
            return {"status": "question_asked", "question": block.config.get("question", "")}
        
        elif block.type == BlockType.AI_ANALYSIS:
            return self._execute_ai_analysis_block(block, contact_data, collected_data)
        
        elif block.type == BlockType.SCORING:
            return self._execute_scoring_block(block, contact_data, collected_data)
        
        return {"status": "executed", "block_type": block.type.value}
    
    def _execute_ai_analysis_block(self, block: Block, contact_data: Dict, collected_data: Dict) -> Dict:
        """Executa análise de IA"""
        
        result = {
            "intent_detected": "schedule_appointment",
            "sentiment_score": 0.8,
            "urgency_level": "high",
            "key_entities": ["consulta médica", "urgente"],
            "ai_confidence": 0.92
        }
        
        return {
            "status": "analyzed",
            "data": {"ai_analysis": result},
            "next_action": "continue"
        }
    
    def _execute_scoring_block(self, block: Block, contact_data: Dict, collected_data: Dict) -> Dict:
        """Executa cálculo de score"""
        
        # Calcular score
        base_score = 50
        
        ai_analysis = collected_data.get("ai_analysis", {})
        
        if ai_analysis.get("urgency_level") == "high":
            base_score += 20
        
        if ai_analysis.get("sentiment_score", 0) > 0.7:
            base_score += 15
        
        final_score = min(100, max(0, base_score))
        
        return {
            "status": "scored",
            "data": {
                "lead_score": final_score,
                "qualification": "hot" if final_score >= 70 else "warm" if final_score >= 40 else "cold"
            },
            "next_action": "assign_to_sales" if final_score >= 70 else "nurture_sequence"
        }
    
    def _get_next_block(self, block: Block, execution_result: Dict) -> Optional[str]:
        """Determina próximo bloco baseado no resultado"""
        if not block.next_blocks:
            return None
        
        if len(block.next_blocks) == 1:
            return block.next_blocks[0]
        
        return block.next_blocks[0] if block.next_blocks else None


__all__ = ['BlockType', 'Block', 'Connection', 'FlowBuilder']
