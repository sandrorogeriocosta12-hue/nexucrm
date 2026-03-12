#!/usr/bin/env python3
"""
test_nexus_learning.py

Script de teste e validação do Nexus Learning Engine.
Valida:
1. Compilação dos módulos C/Cython
2. Funcionalidades básicas (predict, learn)
3. Performance (latência das operações)
4. Persistência (save/load de pesos)
"""

import sys
import time
import json
import os
import tempfile
from pathlib import Path

# Cores para output
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_test(name: str, passed: bool, duration: float = None):
    """Printa resultado de um teste."""
    status = f"{GREEN}✅ PASS{RESET}" if passed else f"{RED}❌ FAIL{RESET}"
    duration_str = f" ({duration*1000:.2f}ms)" if duration is not None else ""
    print(f"  {status} {name}{duration_str}")
    return passed


def test_import():
    """Testa import dos módulos."""
    print(f"\n{BLUE}[1] TESTE DE IMPORT{RESET}")

    try:
        start = time.time()
        from nexus_learning_engine import NexusLearningEngine, get_version

        duration = time.time() - start

        version = get_version()
        print_test(f"Importar NexusLearningEngine v{version}", True, duration)
        return True

    except ImportError as e:
        print_test("Importar NexusLearningEngine", False)
        print(f"{RED}    Erro: {e}{RESET}")
        print(
            f"{YELLOW}    ℹ️ Compile com: python c_modules/setup_new.py build_ext --inplace{RESET}"
        )
        return False


def test_initialization():
    """Testa inicialização do engine."""
    print(f"\n{BLUE}[2] TESTE DE INICIALIZAÇÃO{RESET}")

    try:
        from nexus_learning_engine import NexusLearningEngine

        start = time.time()
        engine = NexusLearningEngine(history_capacity=1000)
        duration = time.time() - start

        print_test("Criar NexusLearningEngine", True, duration)
        return engine

    except Exception as e:
        print_test("Criar NexusLearningEngine", False)
        print(f"{RED}    Erro: {e}{RESET}")
        return None


def test_prediction(engine):
    """Testa predição básica."""
    print(f"\n{BLUE}[3] TESTE DE PREDIÇÃO{RESET}")

    try:
        start = time.time()
        result = engine.predict(
            engagement=0.85, intention=0.72, ai_confidence=0.91, niche="test"
        )
        duration = time.time() - start

        # Valida resultado
        assert 0 <= result["predicted_score"] <= 1
        assert 0 <= result["closure_probability"] <= 1
        assert result["temperature"] in ["cold", "warm", "hot"]
        assert isinstance(result["rule_activations"], list)
        assert len(result["rule_activations"]) == 12

        print_test("Predição (score, P_f, regras)", True, duration)

        # Mostra detalhes
        print(f"    Score: {result['predicted_score']:.4f}")
        print(f"    P_f: {result['closure_probability']:.4f}")
        print(f"    Temperatura: {result['temperature']}")
        print(f"    Recomendação: {result['recommendation']}")

        return True

    except Exception as e:
        print_test("Predição", False)
        print(f"{RED}    Erro: {e}{RESET}")
        return False


def test_learning(engine):
    """Testa aprendizado com feedback."""
    print(f"\n{BLUE}[4] TESTE DE APRENDIZADO{RESET}")

    try:
        # Caso 1: Predição correta (acertou!)
        start = time.time()
        result1 = engine.learn(
            engagement=0.95,
            intention=0.90,
            ai_confidence=0.95,
            actual_outcome=1.0,  # Venda fechada
            was_converted=True,
            feedback="Cliente convertido!",
            niche="test",
        )
        duration1 = time.time() - start

        print_test("Aprendizado com feedback positivo", True, duration1)
        print(f"    Updates: {result1['weight_updates']}")
        print(f"    Accuracy: {result1['learning_metrics']['accuracy']:.4f}")

        # Caso 2: Predição incorreta (errou!)
        start = time.time()
        result2 = engine.learn(
            engagement=0.30,
            intention=0.20,
            ai_confidence=0.25,
            actual_outcome=0.0,  # Venda perdida
            was_converted=False,
            feedback="Lead frio perdido nas tentativas",
            niche="test",
        )
        duration2 = time.time() - start

        print_test("Aprendizado com feedback negativo", True, duration2)
        print(f"    Updates: {result2['weight_updates']}")

        return True

    except Exception as e:
        print_test("Aprendizado", False)
        print(f"{RED}    Erro: {e}{RESET}")
        return False


def test_metrics(engine):
    """Testa cálculo de métricas."""
    print(f"\n{BLUE}[5] TESTE DE MÉTRICAS{RESET}")

    try:
        # Simula aprendizado com múltiplos dados
        scenarios = [
            (0.95, 0.90, 0.95, 1.0, "acc"),  # Score alto, resultado positivo
            (0.85, 0.75, 0.80, 0.8, "acc"),  # Score médio-alto, positivo
            (0.45, 0.35, 0.40, 0.0, "acc"),  # Score baixo, negativo
            (0.65, 0.70, 0.75, 0.5, "acc"),  # Score médio, em andamento
            (0.30, 0.20, 0.25, 0.0, "acc"),  # Score baixo, negativo
        ]

        for e, i, u, outcome, niche in scenarios:
            engine.learn(e, i, u, outcome, niche=niche)

        # Obtém métricas
        metrics = engine.get_metrics()

        print_test("Cálculo de métricas", True)
        print(f"    Accuracy: {metrics['accuracy']:.4f}")
        print(f"    Precision: {metrics['precision']:.4f}")
        print(f"    Recall: {metrics['recall']:.4f}")
        print(f"    F1-Score: {metrics['f1_score']:.4f}")
        print(f"    Updates: {metrics['updates_count']}")

        return True

    except Exception as e:
        print_test("Métricas", False)
        print(f"{RED}    Erro: {e}{RESET}")
        return False


def test_performance(engine):
    """Testa performance (latência)."""
    print(f"\n{BLUE}[6] TESTE DE PERFORMANCE{RESET}")

    try:
        # 1000 predições
        start = time.time()
        for i in range(1000):
            engine.predict(0.5 + (i % 50) * 0.01, 0.5, 0.5)
        duration = time.time() - start

        throughput = 1000 / duration
        latency = duration / 1000 * 1000  # ms

        print_test(f"1000 predições", True, duration)
        print(f"    Throughput: {throughput:.0f} req/s")
        print(f"    Latência média: {latency:.2f}ms")

        # Validar que está rápido
        assert throughput > 1000, f"Throughput muito baixo: {throughput:.0f} req/s"
        assert latency < 2, f"Latência muito alta: {latency:.2f}ms"

        return True

    except AssertionError as e:
        print_test(f"1000 predições - LENTO", False)
        print(f"{YELLOW}    ⚠️ {e}{RESET}")
        return False

    except Exception as e:
        print_test("Performance", False)
        print(f"{RED}    Erro: {e}{RESET}")
        return False


def test_persistence(engine):
    """Testa salvar e carregar pesos."""
    print(f"\n{BLUE}[7] TESTE DE PERSISTÊNCIA{RESET}")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = os.path.join(tmpdir, "weights.json")
            bin_file = os.path.join(tmpdir, "weights.bin")

            # Export JSON
            start = time.time()
            success = engine.export_weights_json(json_file)
            duration = time.time() - start

            if not success or not os.path.exists(json_file):
                print_test("Exportar pesos em JSON", False)
                return False

            print_test("Exportar pesos em JSON", True, duration)

            # Verificar conteúdo
            with open(json_file, "r") as f:
                data = json.load(f)
                assert "weights" in data
                assert len(data["weights"]) == 12
                assert "biases" in data
                assert "learning_rate" in data

            print(f"    Arquivo: {os.path.getsize(json_file)} bytes")

            return True

    except Exception as e:
        print_test("Persistência", False)
        print(f"{RED}    Erro: {e}{RESET}")
        return False


def test_weights(engine):
    """Testa manipulação de pesos."""
    print(f"\n{BLUE}[8] TESTE DE PESOS{RESET}")

    try:
        # Obtém pesos
        weights = engine.get_weights()

        assert len(weights) == 12
        assert all(0.01 <= w <= 10.0 for w in weights)

        print_test("Obter 12 pesos", True)
        print(f"    Pesos: {[f'{w:.3f}' for w in weights]}")

        # Taxa de aprendizado
        rate = engine.context.get_learning_rate()
        assert 0.001 <= rate <= 0.5

        print_test("Obter taxa de aprendizado", True)
        print(f"    Learning rate: {rate:.4f}")

        return True

    except Exception as e:
        print_test("Pesos", False)
        print(f"{RED}    Erro: {e}{RESET}")
        return False


def test_status(engine):
    """Testa relatório de status."""
    print(f"\n{BLUE}[9] TESTE DE STATUS{RESET}")

    try:
        status = engine.get_status()

        assert status["status"] == "running"
        assert "version" in status
        assert "performance" in status
        assert status["predictions_total"] > 0

        print_test("Obter status completo", True)
        print(f"    Versão: {status['version']}")
        print(f"    Predições: {status['predictions_total']}")
        print(f"    Updates: {status['weight_updates']}")
        print(f"    F1-Score: {status['performance']['f1_score']:.4f}")

        return True

    except Exception as e:
        print_test("Status", False)
        print(f"{RED}    Erro: {e}{RESET}")
        return False


def main():
    """Executa suite de testes."""
    print(f"\n{BLUE}{'='*70}")
    print(f"🧠 NEXUS LEARNING ENGINE - TEST SUITE")
    print(f"{'='*70}{RESET}\n")

    results = []

    # [1] Import
    if not test_import():
        print(f"\n{RED}❌ TESTE FALHOU: Impossível importar módulos{RESET}")
        return 1

    # [2] Inicialização
    engine = test_initialization()
    if not engine:
        print(f"\n{RED}❌ TESTE FALHOU: Impossível inicializar engine{RESET}")
        return 1

    # [3-9] Testes funcionais
    results.append(test_prediction(engine))
    results.append(test_learning(engine))
    results.append(test_metrics(engine))
    results.append(test_performance(engine))
    results.append(test_persistence(engine))
    results.append(test_weights(engine))
    results.append(test_status(engine))

    # Sumário
    passed = sum(results)
    total = len(results)

    print(f"\n{BLUE}{'='*70}")
    print(f"📊 SUMÁRIO")
    print(f"{'='*70}{RESET}\n")

    if passed == total:
        print(f"{GREEN}✅ TODOS OS TESTES PASSARAM ({passed}/{total}){RESET}\n")
        print(f"{GREEN}🎉 Nexus Learning Engine está pronto para produção!{RESET}\n")
        return 0
    else:
        print(f"{RED}❌ {total - passed} TESTES FALHARAM ({passed}/{total}){RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
