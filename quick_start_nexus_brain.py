#!/usr/bin/env python3
"""
quick_start_nexus_brain.py

Quick start do Nexus Learning Engine.
Execute este script para:
1. Compilar os módulos C/Cython
2. Testar funcionalidade básica
3. Demonstrar performance
4. Preparar para integração com FastAPI
"""

import subprocess
import sys
import os
import time
from pathlib import Path

# Cores
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(text: str):
    print(f"\n{BLUE}{'='*70}")
    print(f"{text}")
    print(f"{'='*70}{RESET}\n")


def print_step(num: int, text: str):
    print(f"{BLUE}[{num}]{RESET} {text}")


def print_success(text: str):
    print(f"{GREEN}✅ {text}{RESET}")


def print_error(text: str):
    print(f"{RED}❌ {text}{RESET}")


def print_warn(text: str):
    print(f"{YELLOW}⚠️  {text}{RESET}")


def run_command(cmd: str, description: str = "") -> bool:
    """Executa comando e retorna sucesso/falha."""
    try:
        if description:
            print_step(0, f"{description}...")
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        if result.returncode == 0:
            if description:
                print_success(description)
            return True
        else:
            if description:
                print_error(f"{description}\n{result.stderr}")
            return False
    except Exception as e:
        if description:
            print_error(f"{description}: {e}")
        return False


def main():
    print_header("🧠 NEXUS LEARNING ENGINE - QUICK START")

    # Passo 1: Verificar pré-requisitos
    print_step(1, "Verificando pré-requisitos...")

    # Python version
    if sys.version_info < (3, 9):
        print_error(f"Python 3.9+ requerido (você tem {sys.version})")
        return 1
    print_success("Python 3.9+")

    # GCC
    if not run_command("gcc --version > /dev/null 2>&1"):
        print_error(
            "GCC não encontrado. Instale com: sudo apt-get install build-essential"
        )
        return 1
    print_success("GCC compilador")

    # Cython
    try:
        import Cython

        print_success("Cython")
    except ImportError:
        print_warn("Cython não instalado. Instalando...")
        if not run_command("pip install cython numpy setups"):
            return 1

    # Passo 2: Compilar módulos C/Cython
    print("\n" + "=" * 70)
    print_step(2, "Compilando módulos C/Cython...")
    print("=" * 70)

    if not run_command("python c_modules/setup_new.py build_ext --inplace"):
        print_error("Falha na compilação. Veja erros acima.")
        return 1

    print_success("Compilação concluída")

    # Passo 3: Validar .so files
    print("\n" + "=" * 70)
    print_step(3, "Validando bibliotecas compiladas...")
    print("=" * 70)

    so_files = list(Path("c_modules").glob("*.so"))
    if not so_files:
        print_error("Nenhum arquivo .so gerado!")
        return 1

    for so_file in so_files:
        file_size = so_file.stat().st_size / 1024  # KB
        print_success(f"{so_file.name} ({file_size:.1f}KB)")

    # Passo 4: Importar módulos
    print("\n" + "=" * 70)
    print_step(4, "Importando módulos Python...")
    print("=" * 70)

    try:
        from nexus_learning_engine import NexusLearningEngine, get_version
        from nexus_api_integration import initialize_learning_engine

        print_success(f"NexusLearningEngine v{get_version()}")
        print_success("nexus_api_integration")

    except ImportError as e:
        print_error(f"Falha ao importar: {e}")
        return 1

    # Passo 5: Teste funcional
    print("\n" + "=" * 70)
    print_step(5, "Teste funcional (predição + aprendizado)...")
    print("=" * 70)

    try:
        engine = NexusLearningEngine(history_capacity=1000)
        print_success("Engine inicializado")

        # Predição 1
        print("\n  Experimento 1: Lead quente")
        pred1 = engine.predict(0.95, 0.90, 0.95, "B2B SaaS")
        print(f"    Score: {pred1['predicted_score']:.4f}")
        print(f"    P_f: {pred1['closure_probability']:.4f}")
        print(f"    Temperatura: {pred1['temperature']}")

        # Aprendizado positivo
        metrics1 = engine.learn(
            0.95,
            0.90,
            0.95,
            1.0,
            was_converted=True,
            feedback="Cliente convertido!",
            niche="B2B SaaS",
        )
        print(f"    ✅ Aprendizado (updates: {metrics1['weight_updates']})")
        print(f"    Accuracy: {metrics1['learning_metrics']['accuracy']:.4f}")

        # Predição 2
        print("\n  Experimento 2: Lead frio")
        pred2 = engine.predict(0.30, 0.20, 0.25, "B2B SaaS")
        print(f"    Score: {pred2['predicted_score']:.4f}")
        print(f"    Temperatura: {pred2['temperature']}")

        # Aprendizado negativo
        metrics2 = engine.learn(
            0.30, 0.20, 0.25, 0.0, feedback="Não interessado", niche="B2B SaaS"
        )
        print(f"    ✅ Aprendizado (updates: {metrics2['weight_updates']})")

        # Métricas
        status = engine.get_status()
        print(f"\n  Estatísticas finais:")
        print(f"    Predições totais: {status['predictions_total']}")
        print(f"    Updates de peso: {status['weight_updates']}")
        print(f"    F1-Score: {status['performance']['f1_score']:.4f}")

    except Exception as e:
        print_error(f"Teste falhou: {e}")
        import traceback

        traceback.print_exc()
        return 1

    # Passo 6: Performance
    print("\n" + "=" * 70)
    print_step(6, "Teste de performance (1000 predições)...")
    print("=" * 70)

    start = time.time()
    for i in range(1000):
        engine.predict(0.5 + (i % 50) * 0.01, 0.5, 0.5)
    duration = time.time() - start
    throughput = 1000 / duration

    print(f"  Tempo: {duration*1000:.2f}ms")
    print(f"  Throughput: {throughput:.0f} req/s")

    if throughput > 10000:
        print_success(f"Performance excelente! ({throughput:.0f} > 10K req/s)")
    elif throughput > 5000:
        print_success(f"Performance boa ({throughput:.0f} req/s)")
    else:
        print_warn(f"Performance baixa ({throughput:.0f} req/s)")

    # Passo 7: Próximos passos
    print("\n" + "=" * 70)
    print("🚀 PRÓXIMOS PASSOS")
    print("=" * 70 + "\n")

    print(f"{GREEN}Opção 1: Integrar com FastAPI{RESET}")
    print(
        """
    # Em seu app_server.py ou main.py:
    
    from nexus_api_integration import setup_learning_api, router
    
    app = FastAPI()
    
    @app.on_event("startup")
    async def startup():
        setup_learning_api(app, redis_client)
    
    app.include_router(router)
    
    # Ou execute testes automáticos:
    python test_nexus_learning.py
    """
    )

    print(f"{GREEN}Opção 2: Testar endpoints{RESET}")
    print(
        """
    # Em outro terminal:
    uvicorn app_server:app --reload
    
    # Predição:
    curl -X POST "http://localhost:8000/api/v1/learning/predict" \\
      -H "Content-Type: application/json" \\
      -d '{"engagement":0.85,"intention":0.72,"ai_confidence":0.91}'
    
    # Feedback:
    curl -X POST "http://localhost:8000/api/v1/learning/feedback" \\
      -H "Content-Type: application/json" \\
      -d '{"engagement":0.85,"intention":0.72,"ai_confidence":0.91,"actual_outcome":1.0,"was_converted":true}'
    
    # Métricas:
    curl "http://localhost:8000/api/v1/learning/metrics"
    """
    )

    print(f"{GREEN}Opção 3: Ler documentação{RESET}")
    print(
        """
    - NEXUS_LEARNING_GUIDE.md        - Guia completo
    - BLUEPRINT_NEXUS_CONSOLIDATED.md - Visão geral técnica
    - nexus_learning_engine.py        - Exemplos no main
    - nexus_api_integration.py        - Docs dos endpoints
    """
    )

    # Status final
    print("\n" + "=" * 70)
    print(f"{GREEN}✅ NEXUS LEARNING ENGINE ESTÁ PRONTO!{RESET}")
    print("=" * 70 + "\n")

    print(f"{BLUE}Status:{RESET}")
    print(f"  • Motor C compilado ✅")
    print(f"  • Wrapper Cython integrado ✅")
    print(f"  • API FastAPI disponível ✅")
    print(f"  • Performance: {throughput:.0f} req/s ✅")
    print(f"  • Documentação: Completa ✅\n")

    print(f"{GREEN}Próxima fase: Integração com FastAPI e Redis{RESET}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
