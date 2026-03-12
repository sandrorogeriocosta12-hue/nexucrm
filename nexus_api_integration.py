"""
nexus_api_integration.py

Endpoints FastAPI para integração do motor de aprendizado Fuzzy.
Expõe a API do NexusLearningEngine para o dashboard e webhooks de IA.

Rotas:
  POST   /learning/predict         - Predição de lead
  POST   /learning/feedback         - Feedback de venda e aprendizado
  GET    /learning/metrics          - Métricas de performance
  GET    /learning/weights          - Estado dos pesos
  GET    /learning/status           - Status geral do engine
  POST   /learning/export-weights   - Exporta pesos em JSON
  POST   /learning/reset-weights    - Reset para pesos aleatórios
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import logging
from datetime import datetime
import json

from nexus_learning_engine import NexusLearningEngine

logger = logging.getLogger(__name__)

# Instância global do engine (seria melhor em dependency injection)
_engine: Optional[NexusLearningEngine] = None


def get_learning_engine() -> NexusLearningEngine:
    """Dependency para obter a instância do learning engine."""
    global _engine
    if _engine is None:
        raise HTTPException(status_code=500, detail="Learning engine não inicializado")
    return _engine


def initialize_learning_engine(redis_client=None):
    """Inicializa o engine na startup da aplicação."""
    global _engine
    try:
        _engine = NexusLearningEngine(redis_client=redis_client)
        logger.info("✅ NexusLearningEngine inicializado com sucesso")
    except Exception as e:
        logger.error(f"❌ Falha ao inicializar NexusLearningEngine: {e}")
        raise


# ============== MODELOS PYDANTIC ==============


class LeadFeaturesRequest(BaseModel):
    """Request para predição de um lead."""

    engagement: float = Field(..., ge=0.0, le=1.0, description="EMA de engajamento")
    intention: float = Field(..., ge=0.0, le=1.0, description="Score de intenção")
    ai_confidence: float = Field(..., ge=0.0, le=1.0, description="Confiança do bot")
    niche: str = Field(default="default", description="Segmento de mercado")
    lead_id: Optional[str] = Field(None, description="ID do lead para rastreamento")


class PredictionResponse(BaseModel):
    """Response da predição."""

    predicted_score: float
    closure_probability: float
    temperature: str  # cold, warm, hot
    recommendation: str  # ignore_or_nurture, nurture, close
    rule_activations: List[float]
    niche: str
    timestamp: str


class SalesOutcomeRequest(BaseModel):
    """Request para feedback de venda."""

    engagement: float = Field(..., ge=0.0, le=1.0)
    intention: float = Field(..., ge=0.0, le=1.0)
    ai_confidence: float = Field(..., ge=0.0, le=1.0)
    actual_outcome: float = Field(
        ..., ge=0.0, le=1.0, description="0=perdida, 0.5=em_andamento, 1=fechada"
    )
    was_converted: bool = Field(False, description="Venda foi realmente fechada?")
    feedback: Optional[str] = Field(
        None, description="Feedback qualitativo do vendedor"
    )
    niche: str = Field(default="default")
    lead_id: Optional[str] = None
    sale_amount: Optional[float] = Field(None, ge=0.0, description="Valor da venda")


class LearningResponse(BaseModel):
    """Response do aprendizado."""

    weight_updates: int
    learning_metrics: Dict[str, float]
    timestamp: str


class MetricsResponse(BaseModel):
    """Métricas de performance."""

    accuracy: float
    precision: float
    recall: float
    f1_score: float
    updates_count: int
    history_size: int
    avg_training_error: float


class StatusResponse(BaseModel):
    """Status completo do engine."""

    status: str
    version: str
    predictions_total: int
    weight_updates: int
    last_update: Optional[str]
    performance: MetricsResponse
    niches_tracked: int
    learning_rate: float


# ============== ROUTER ==============

router = APIRouter(
    prefix="/api/v1/learning",
    tags=["Fuzzy Learning Engine"],
    responses={500: {"description": "Learning engine error"}},
)


@router.post("/predict", response_model=PredictionResponse)
async def predict_lead(
    request: LeadFeaturesRequest,
    engine: NexusLearningEngine = Depends(get_learning_engine),
) -> Dict:
    """
    Faz uma predição para um novo lead.

    **Descrição:**
    - Recebe features de um lead (engagement, intention, AI confidence)
    - Executa inferência fuzzy no motor C (μs)
    - Retorna score, probabilidade de fechamento e recomendação

    **Exemplo:**
    ```json
    {
        "engagement": 0.85,
        "intention": 0.72,
        "ai_confidence": 0.91,
        "niche": "B2B SaaS"
    }
    ```
    """
    try:
        result = engine.predict(
            engagement=request.engagement,
            intention=request.intention,
            ai_confidence=request.ai_confidence,
            niche=request.niche,
        )
        return result
    except Exception as e:
        logger.error(f"Erro em predict: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback", response_model=LearningResponse)
async def learn_from_feedback(
    request: SalesOutcomeRequest,
    background_tasks: BackgroundTasks,
    engine: NexusLearningEngine = Depends(get_learning_engine),
) -> Dict:
    """
    Processa feedback de venda e atualiza pesos automaticamente.

    **Descrição:**
    - Compara predição anterior com resultado real
    - Calcula erro: error = real - predito
    - Ajusta pesos das regras fuzzy: w_i := w_i - η * error * μ_i
    - Armazena histórico para validação

    **Fluxo:**
    1. Sistema prediz lead como "hot" (score 0.85)
    2. Vendedor marca venda como "perdida" (outcome 0.0)
    3. Engine calcula erro: -0.85
    4. Reduz pesos que ativaram nessa predição
    5. Aprende que aquele padrão prefere resultados piores

    **Exemplo:**
    ```json
    {
        "engagement": 0.85,
        "intention": 0.72,
        "ai_confidence": 0.91,
        "actual_outcome": 0.0,
        "was_converted": false,
        "feedback": "Cliente perdido para concorrente",
        "niche": "B2B SaaS",
        "sale_amount": 0.0
    }
    ```
    """
    try:
        result = engine.learn(
            engagement=request.engagement,
            intention=request.intention,
            ai_confidence=request.ai_confidence,
            actual_outcome=request.actual_outcome,
            was_converted=request.was_converted,
            feedback=request.feedback or "",
            niche=request.niche,
        )

        # Persiste em background (não bloqueia resposta)
        if request.lead_id:
            background_tasks.add_task(
                _log_feedback,
                request.lead_id,
                request.actual_outcome,
                request.sale_amount,
            )

        return result

    except Exception as e:
        logger.error(f"Erro em learn: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    engine: NexusLearningEngine = Depends(get_learning_engine),
) -> Dict:
    """
    Retorna métricas atuais de performance do motor.

    **Métricas:**
    - **Accuracy:** % de predições dentro de 0.15 do resultado real
    - **Precision:** % de true positives entre leads preditos como "hot"
    - **Recall:** % de leads hot reais que foram preditos como hot
    - **F1:** Média harmônica de precision e recall

    **Interpretação:**
    - F1 > 0.8: Motor está bem calibrado
    - F1 < 0.5: Precisa mais dados de treinamento
    """
    try:
        metrics = engine.get_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Erro em get_metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=StatusResponse)
async def get_status(
    engine: NexusLearningEngine = Depends(get_learning_engine),
) -> Dict:
    """
    Retorna status completo do learning engine.

    Informações:
    - Versão do motor Cython
    - Total de predições e atualizações de peso
    - Performance agregada
    - Niches sendo rastreados
    - Taxa de aprendizado atual
    """
    try:
        status = engine.get_status()
        return status
    except Exception as e:
        logger.error(f"Erro em get_status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weights")
async def get_weights(
    engine: NexusLearningEngine = Depends(get_learning_engine),
) -> Dict:
    """
    Retorna os 12 pesos atuais das regras fuzzy.

    **Interpretação:**
    - Pesos próximos de 1.0: Regra com influência neutra
    - Pesos > 1.0: Regra reforçada (leva a leads mais quentes)
    - Pesos < 1.0: Regra suprimida (leva a leads mais frios)
    """
    try:
        weights = engine.get_weights()
        return {"weights": weights, "timestamp": datetime.utcnow().isoformat() + "Z"}
    except Exception as e:
        logger.error(f"Erro em get_weights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export-weights")
async def export_weights(
    filename: str = "nexus_weights_export.json",
    engine: NexusLearningEngine = Depends(get_learning_engine),
) -> Dict:
    """
    Exporta os pesos em JSON para análise, backup ou A/B testing.
    """
    try:
        success = engine.export_weights_json(filename)
        if success:
            return {
                "success": True,
                "filename": filename,
                "message": f"Pesos exportados para {filename}",
            }
        else:
            raise HTTPException(status_code=500, detail="Falha ao exportar pesos")
    except Exception as e:
        logger.error(f"Erro em export_weights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/report")
async def get_performance_report(
    engine: NexusLearningEngine = Depends(get_learning_engine),
) -> Dict:
    """
    Retorna relatório de performance formatado em texto.
    """
    try:
        report = engine.get_report()
        return {"report": report, "timestamp": datetime.utcnow().isoformat() + "Z"}
    except Exception as e:
        logger.error(f"Erro em get_report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== BACKGROUND TASKS ==============


async def _log_feedback(lead_id: str, outcome: float, sale_amount: Optional[float]):
    """Registra feedback em background para analytics."""
    try:
        logger.info(f"📊 Lead {lead_id}: outcome={outcome}, amount=${sale_amount}")
        # TODO: Enviar para analytics/BI
    except Exception as e:
        logger.error(f"Erro ao registrar feedback: {e}")


# ============== INCLUSÃO NO MAIN APP ==============


def setup_learning_api(app, redis_client=None):
    """
    Configura o API de aprendizado na aplicação FastAPI.

    Uso em main.py:
        from fastapi import FastAPI
        from nexus_api_integration import setup_learning_api

        app = FastAPI()
        redis_client = redis.asyncio.from_url("redis://localhost")

        @app.on_event("startup")
        async def startup():
            setup_learning_api(app, redis_client)

        app.include_router(router)
    """
    initialize_learning_engine(redis_client)
    logger.info("✅ Learning API inicializada")


# ============== EXEMPLO ISOLADO ==============

if __name__ == "__main__":
    """Teste local sem FastAPI."""
    import asyncio

    print("\n" + "=" * 70)
    print("🚀 NEXUS API INTEGRATION - TEST")
    print("=" * 70 + "\n")

    # Inicializa
    initialize_learning_engine()
    engine = _engine

    # Request exemplo
    req = LeadFeaturesRequest(
        engagement=0.85, intention=0.72, ai_confidence=0.91, niche="B2B SaaS"
    )

    # Predição
    pred = engine.predict(
        engagement=req.engagement,
        intention=req.intention,
        ai_confidence=req.ai_confidence,
        niche=req.niche,
    )
    print(f"📊 Predição: {json.dumps(pred, indent=2)}")

    # Feedback
    outcome_req = SalesOutcomeRequest(
        engagement=req.engagement,
        intention=req.intention,
        ai_confidence=req.ai_confidence,
        actual_outcome=1.0,  # Venda fechada!
        was_converted=True,
        feedback="Cliente muito satisfeito",
        niche=req.niche,
    )

    learning = engine.learn(
        engagement=outcome_req.engagement,
        intention=outcome_req.intention,
        ai_confidence=outcome_req.ai_confidence,
        actual_outcome=outcome_req.actual_outcome,
        was_converted=outcome_req.was_converted,
        feedback=outcome_req.feedback,
        niche=outcome_req.niche,
    )
    print(f"\n🧠 Aprendizado: {json.dumps(learning, indent=2)}")

    # Status
    status = engine.get_status()
    print(f"\n📈 Status: {json.dumps(status, indent=2)}")
