"""
nexus_learning_engine.py

Motor de aprendizado automático do Nexus Service.
Gerencia o lifecycle do aprendizado fuzzy, integrado com FastAPI/Redis.

Arquitetura:
- LearningEngine: Interface Python de alto nível
- NexusLearnContext (Cython): Motor C de inferência + aprendizado
- Redis: Persistência de pesos e histórico
- FastAPI: Endpoints para predição e feedback
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import hashlib
import pickle

try:
    from c_modules.weight_adjustment import NexusLearnContext, get_version

    CYTHON_AVAILABLE = True
except ImportError:
    CYTHON_AVAILABLE = False
    logging.warning(
        "Módulo Cython weight_adjustment não disponível. Usando fallback Python."
    )

logger = logging.getLogger(__name__)


class NexusLearningEngine:
    """
    Motor de aprendizado automático do Nexus Service.

    Características:
    - Inferência Fuzzy ultra-rápida (motor em C)
    - Ajuste de pesos automático por erro
    - Persistência em Redis
    - Histórico de predições para validação
    - Métricas de performance em tempo real

    Exemplo de uso:
        engine = NexusLearningEngine(redis_client=redis_client)

        # Predição
        result = engine.predict(
            engagement=0.85,
            intention=0.72,
            ai_confidence=0.91,
            niche="B2B SaaS"
        )

        # Feedback e aprendizado
        engine.learn(
            engagement=0.85,
            intention=0.72,
            ai_confidence=0.91,
            actual_outcome=1.0,  # Venda fechada!
            was_converted=True,
            feedback="Cliente muito satisfeito",
            niche="B2B SaaS"
        )
    """

    def __init__(
        self,
        redis_client=None,
        history_capacity: int = 10000,
        persist_dir: str = "./nexus_weights",
    ):
        """
        Inicializa o motor de aprendizado.

        Args:
            redis_client: Client Redis para persistência (opcional)
            history_capacity: Limite de histórico em memória
            persist_dir: Diretório para salvar pesos
        """
        self.redis = redis_client
        self.persist_dir = persist_dir
        self.cython_available = CYTHON_AVAILABLE

        if not self.cython_available:
            logger.error(
                "❌ Módulo Cython não disponível! Compile com: python c_modules/setup_new.py build_ext --inplace"
            )
            raise RuntimeError("Cython weight_adjustment não compilado. Veja logs.")

        # Inicializa o contexto de aprendizado (C)
        self.context = NexusLearnContext(history_capacity=history_capacity)
        self.history_capacity = history_capacity

        # Dicionário para cache de niches (histórico de conversão)
        self.niche_stats: Dict[str, Dict] = {}

        # Métricas agregadas
        self.predictions_total = 0
        self.predictions_correct = 0
        self.last_update_time = None

        logger.info(f"✅ NexusLearningEngine inicializado [Cython v{get_version()}]")

        # Tenta carregar pesos salvos
        self._load_or_init_weights()

    def _load_or_init_weights(self):
        """Tenta carregar pesos do Redis/disco. Se falhar, usa aleatórios."""
        if self.redis:
            try:
                weights_json = self.redis.get("nexus:weights:current")
                if weights_json:
                    weights_data = json.loads(weights_json)
                    self.context.set_weights(weights_data["weights"])
                    logger.info(
                        f"✅ Pesos carregados do Redis (atualização #{weights_data.get('update_count', 0)})"
                    )
                    return
            except Exception as e:
                logger.warning(f"⚠️ Falha ao carregar pesos do Redis: {e}")

        logger.info("ℹ️ Usando pesos aleatórios iniciais")

    def predict(
        self,
        engagement: float,
        intention: float,
        ai_confidence: float,
        niche: str = "default",
    ) -> Dict:
        """
        Faz uma predição para um novo lead.

        Args:
            engagement: EMA típica do WhatsApp/email (0-1)
            intention: Score baseado em palavras-chave de fechamento (0-1)
            ai_confidence: Score de confiança das respostas do bot (0-1)
            niche: Segmento de mercado para contexto

        Returns:
            {
                'predicted_score': float (0-1),
                'closure_probability': float (0-1),
                'rule_activations': [float x 12],
                'temperature': 'cold'|'warm'|'hot',
                'recommendation': 'ignore'|'nurture'|'close',
                'timestamp': ISO 8601
            }
        """
        try:
            # Clipa valores em [0, 1]
            e = max(0.0, min(1.0, engagement))
            i = max(0.0, min(1.0, intention))
            u = max(0.0, min(1.0, ai_confidence))

            # Obtém predição do motor C
            result = self.context.predict(e, i, u, niche)

            # Enriquece resultado com contexto
            score = result["predicted_score"]
            p_f = result["closure_probability"]

            # Classifica temperatura
            if score < 0.4:
                temperature = "cold"
                recommendation = "ignore_or_nurture"
            elif score < 0.65:
                temperature = "warm"
                recommendation = "nurture"
            else:
                temperature = "hot"
                recommendation = "close"

            # Integra histórico do nicho se disponível
            niche_factor = self._get_niche_conversion_rate(niche)
            adjusted_p_f = p_f * (0.7 + niche_factor * 0.3)  # Ajusta com histórico

            output = {
                "predicted_score": round(score, 4),
                "closure_probability": round(adjusted_p_f, 4),
                "temperature": temperature,
                "recommendation": recommendation,
                "rule_activations": [round(x, 4) for x in result["rule_activations"]],
                "niche": niche,
                "engagement_fuzzy": e,
                "intention_fuzzy": i,
                "confidence_fuzzy": u,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

            # Log para analytics
            if self.redis:
                try:
                    self.redis.lpush(
                        f"nexus:predictions:{niche}",
                        json.dumps(output),
                        **{"ex": 86400},  # TTL 24h
                    )
                except:
                    pass

            self.predictions_total += 1
            return output

        except Exception as e:
            logger.error(f"❌ Erro em predict(): {e}")
            raise

    def learn(
        self,
        engagement: float,
        intention: float,
        ai_confidence: float,
        actual_outcome: float,
        was_converted: bool = False,
        feedback: str = "",
        niche: str = "default",
    ) -> Dict:
        """
        Processa feedback de vendas e atualiza pesos.

        Args:
            engagement, intention, ai_confidence: mesmos de predict()
            actual_outcome: 0.0 (perdida), 0.5 (em andamento), 1.0 (fechada)
            was_converted: Booleano se vendedor confirmou fechamento
            feedback: Texto de feedback qualitativo
            niche: Segmento de mercado

        Returns:
            {
                'error': float,
                'weight_updates': int,
                'new_metrics': {accuracy, precision, recall, f1}
            }
        """
        try:
            # Clipa
            e = max(0.0, min(1.0, engagement))
            i = max(0.0, min(1.0, intention))
            u = max(0.0, min(1.0, ai_confidence))
            o = max(0.0, min(1.0, actual_outcome))

            # Aprendizado no motor C
            metrics = self.context.learn_from_outcome(
                e,
                i,
                u,
                o,
                was_converted=was_converted,
                feedback=feedback[:255],  # Limita feedback
                niche=niche,
            )

            # Atualiza stats do nicho
            self._update_niche_stats(niche, actual_outcome)

            # Persiste pesos no Redis periodicamente
            update_count = metrics["updates_count"]
            if update_count % 50 == 0:  # A cada 50 updates
                self._persist_weights()

            self.last_update_time = datetime.utcnow()

            output = {
                "weight_updates": update_count,
                "learning_metrics": {
                    "accuracy": round(metrics["accuracy"], 4),
                    "precision": round(metrics["precision"], 4),
                    "recall": round(metrics["recall"], 4),
                    "f1_score": round(metrics["f1_score"], 4),
                },
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

            return output

        except Exception as e:
            logger.error(f"❌ Erro em learn(): {e}")
            raise

    def _get_niche_conversion_rate(self, niche: str) -> float:
        """
        Retorna a taxa de conversão histórica do nicho.
        Ajusta P_f com base em padrões históricos.
        """
        if niche not in self.niche_stats:
            return 0.5  # Neutro

        stats = self.niche_stats[niche]
        total = stats.get("total", 1)
        converted = stats.get("converted", 0)

        return converted / max(1, total)

    def _update_niche_stats(self, niche: str, outcome: float):
        """Atualiza estatísticas histórias do nicho."""
        if niche not in self.niche_stats:
            self.niche_stats[niche] = {"total": 0, "converted": 0}

        self.niche_stats[niche]["total"] += 1
        if outcome > 0.8:  # Considera fechado se > 0.8
            self.niche_stats[niche]["converted"] += 1

    def _persist_weights(self):
        """Salva pesos no Redis e disco."""
        try:
            weights = self.context.get_weights()
            biases = self.context.get_biases()
            metrics = self.context.get_metrics()

            data = {
                "weights": weights,
                "biases": biases,
                "update_count": metrics["updates_count"],
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": {
                    "accuracy": metrics["accuracy"],
                    "precision": metrics["precision"],
                    "recall": metrics["recall"],
                    "f1_score": metrics["f1_score"],
                },
            }

            if self.redis:
                self.redis.set(
                    "nexus:weights:current",
                    json.dumps(data),
                    ex=7 * 24 * 3600,  # TTL 1 semana
                )
                logger.info(
                    f"💾 Pesos persisted no Redis (update #{metrics['updates_count']})"
                )

        except Exception as e:
            logger.warning(f"⚠️ Falha ao persistir pesos: {e}")

    def get_weights(self) -> List[float]:
        """Retorna os 12 pesos das regras fuzzy."""
        return self.context.get_weights()

    def get_metrics(self) -> Dict:
        """Retorna métricas de performance."""
        return self.context.get_metrics()

    def get_report(self) -> str:
        """Retorna relatório de performance em texto."""
        return self.context.get_performance_report()

    def export_weights_json(self, filename: str) -> bool:
        """Exporta pesos em JSON para análise/backup."""
        return self.context.export_to_json(filename)

    def get_status(self) -> Dict:
        """Retorna status atual do engine."""
        metrics = self.context.get_metrics()

        return {
            "cython_available": self.cython_available,
            "version": get_version(),
            "status": "running",
            "predictions_total": self.predictions_total,
            "weight_updates": metrics["updates_count"],
            "history_size": metrics["history_size"],
            "last_update": self.last_update_time.isoformat()
            if self.last_update_time
            else None,
            "performance": {
                "accuracy": round(metrics["accuracy"], 4),
                "precision": round(metrics["precision"], 4),
                "recall": round(metrics["recall"], 4),
                "f1_score": round(metrics["f1_score"], 4),
            },
            "niches_tracked": len(self.niche_stats),
            "learning_rate": self.context.get_learning_rate(),
        }


# ============== EXEMPLO DE USO ==============

if __name__ == "__main__":
    import time

    print("\n" + "=" * 70)
    print("🧠 NEXUS LEARNING ENGINE - DEMO")
    print("=" * 70 + "\n")

    # Inicializa engine
    engine = NexusLearningEngine(history_capacity=1000)

    # Simula 50 leads com predicões e feedback
    print("Simulando 50 leads com aprendizado automático...\n")

    scenarios = [
        # (engagement, intention, confidence, true_outcome, niche)
        (0.95, 0.90, 0.95, 1.0, "B2B SaaS"),  # Lead perfeito
        (0.85, 0.75, 0.80, 0.8, "B2B SaaS"),  # Bom lead
        (0.45, 0.35, 0.40, 0.0, "B2B SaaS"),  # Lead frio
        (0.65, 0.70, 0.75, 0.5, "E-commerce"),  # Em andamento
        (0.30, 0.20, 0.25, 0.0, "E-commerce"),  # Lead perdido
    ]

    for i in range(50):
        scenario = scenarios[i % len(scenarios)]
        e, i_score, conf, outcome, niche = scenario

        # Predição
        pred = engine.predict(e, i_score, conf, niche)
        print(
            f"Lead #{i+1:2d} | {niche:15s} | Score: {pred['predicted_score']:.3f} | "
            f"Temp: {pred['temperature']:5s} | Actual: {outcome:.1f}"
        )

        # Feedback
        engine.learn(e, i_score, conf, outcome, niche=niche)

    # Status final
    print("\n" + "=" * 70)
    print("PERFORMANCE FINAL")
    print("=" * 70)
    print(engine.get_report())

    status = engine.get_status()
    print(f"\n📊 Status: {status}")
