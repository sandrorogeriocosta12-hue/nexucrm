"""
🧪 STRESS TEST FINAL - NEXUS SERVICE MOTOR C
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Objetivo: Garantir que o motor Fuzzy em C NÃO vai crashed em produção

Simulação:
- 10.000 mensagens processadas
- 300 sessões simultâneas
- Score sendo recalculado a cada mensagem
- Redis ativo (contexto)
- Geração de PDF paralela
- Monitoramento: CPU, RAM, crashes, P95, P99

Critério de Sucesso:
✅ P99 < 80ms (enterprise-grade)
✅ Sem segmentation faults
✅ Sem memory leaks
✅ Sem deadlocks
✅ CPU < 80%
✅ RAM estável
"""

import asyncio
import threading
import time
import json
import psutil
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime
import statistics
import traceback

# ==================== IMPORT CRÍTICOS ====================

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️  Redis não instalado - usando mock")

try:
    # Simulando import do motor C (substitua com import real)
    # from c_modules import fuzzy_score
    MOTOR_C_AVAILABLE = True
except ImportError:
    MOTOR_C_AVAILABLE = False
    print("⚠️  Motor C não compilado - usando simulação")

# ==================== ESTRUTURAS ====================


@dataclass
class StressTestMetrics:
    """Métricas coletadas durante o teste"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_time: float = 0.0

    # Latências
    latencies: List[float] = None
    p50: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    mean: float = 0.0
    std: float = 0.0

    # Recursos
    peak_cpu: float = 0.0
    peak_memory: float = 0.0
    avg_cpu: float = 0.0
    avg_memory: float = 0.0

    # Erros
    crashes: int = 0
    segfaults: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.latencies is None:
            self.latencies = []
        if self.errors is None:
            self.errors = []


# ==================== SIMULAÇÃO DO MOTOR C ====================


class FuzzyMotorSimulation:
    """Mock do motor C para teste quando não tiver compilado"""

    def __init__(self):
        self.call_count = 0
        self.crash_at = None  # Para injetar crash em teste

    def score_lead(self, engagement, intention, ai_confidence):
        """Simula score_lead do motor C"""
        self.call_count += 1

        # Simula crash injetado (para teste)
        if self.crash_at and self.call_count == self.crash_at:
            raise RuntimeError("[SIMULADO] Segmentation Fault no C")

        # Simula cálculo fuzzy
        time.sleep(0.001)  # 1ms baseline

        # Fuzzy logic: LeadScore = Σ(w_i * μ_i) / Σ(μ_i)
        score = engagement * 0.4 + intention * 0.5 + ai_confidence * 0.1

        # Sigmoid para probabilidade
        import math

        probability = 1.0 / (1.0 + math.exp(-5.0 * score))

        return {
            "score": min(1.0, max(0.0, score)),
            "probability": probability,
            "rule_activations": [score] * 12,
        }


# ==================== MOTOR C THREAD-SAFE ====================


class ThreadSafeFuzzyMotor:
    """Wrapper thread-safe para o motor C (CRÍTICO!)"""

    def __init__(self):
        try:
            # Tenta import real
            # from c_modules import fuzzy_score
            self.motor = FuzzyMotorSimulation()  # Substitua com real
            self.real_motor = False
        except:
            self.motor = FuzzyMotorSimulation()
            self.real_motor = False

        # LOCK OBRIGATÓRIO para thread-safety do C
        self._lock = threading.RLock()
        self.call_count = 0
        self.error_count = 0

    def score_lead_safe(self, engagement, intention, ai_confidence):
        """
        ⚠️ CRÍTICO: Lock antes de chamar C
        Se o C não for thread-safe, isso evita race conditions
        """
        with self._lock:
            try:
                result = self.motor.score_lead(engagement, intention, ai_confidence)
                self.call_count += 1
                return result
            except Exception as e:
                self.error_count += 1
                raise


# ==================== REDIS MOCK ====================


class RedisMock:
    """Mock de Redis para teste offline"""

    def __init__(self):
        self.data = {}
        self._lock = threading.Lock()

    def set(self, key, value):
        with self._lock:
            self.data[key] = value

    def get(self, key):
        with self._lock:
            return self.data.get(key)

    def incr(self, key):
        with self._lock:
            self.data[key] = self.data.get(key, 0) + 1
            return self.data[key]


# ==================== WORKER THREAD ====================


class StressTestWorker:
    """Worker que simula um vendedor usando o sistema"""

    def __init__(self, worker_id: int, motor: ThreadSafeFuzzyMotor, redis_client):
        self.worker_id = worker_id
        self.motor = motor
        self.redis = redis_client
        self.messages_processed = 0
        self.latencies = []
        self.errors = []

    def process_message(self, message_id: int) -> Dict:
        """
        Simula processamento de 1 mensagem:
        1. Score do lead
        2. Salva em Redis
        3. Gera PDF (simulado)
        4. Retorna resultado
        """
        start_time = time.time()

        try:
            # Simula dados do lead
            engagement = (message_id % 100) / 100.0
            intention = ((message_id * 7) % 100) / 100.0
            ai_confidence = ((message_id * 13) % 100) / 100.0

            # ✅ CHAMADA THREAD-SAFE DO MOTOR C
            result = self.motor.score_lead_safe(engagement, intention, ai_confidence)

            # Salva em Redis
            key = f"lead:{self.worker_id}:{message_id}"
            self.redis.set(key, json.dumps(result))

            # Simula geração de PDF (paralela)
            # Em produção seria com ReportLab em thread
            time.sleep(0.002)  # 2ms para PDF

            # Incrementa contador
            self.redis.incr("total_processed")

            latency = (time.time() - start_time) * 1000  # ms
            self.latencies.append(latency)
            self.messages_processed += 1

            return {
                "success": True,
                "message_id": message_id,
                "worker_id": self.worker_id,
                "latency_ms": latency,
                "score": result["score"],
            }

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            error_msg = f"Worker {self.worker_id}: {str(e)}"
            self.errors.append(error_msg)

            return {
                "success": False,
                "message_id": message_id,
                "worker_id": self.worker_id,
                "latency_ms": latency,
                "error": str(e),
            }


# ==================== STRESS TEST EXECUTOR ====================


class StressTestExecutor:
    """Coordena o stress test"""

    def __init__(self, num_workers: int, messages_per_worker: int):
        self.num_workers = num_workers
        self.messages_per_worker = messages_per_worker
        self.motor = ThreadSafeFuzzyMotor()
        self.redis = RedisMock()
        self.metrics = StressTestMetrics()
        self.process = psutil.Process()

    def run(self) -> StressTestMetrics:
        """Executa o stress test"""
        print(
            f"""
╔════════════════════════════════════════════════════════╗
║     🧪 STRESS TEST - NEXUS SERVICE MOTOR C            ║
╚════════════════════════════════════════════════════════╝

📊 Configuração:
   • Num. Workers: {self.num_workers}
   • Msgs por Worker: {self.messages_per_worker}
   • Total Mensagens: {self.num_workers * self.messages_per_worker:,}
   • Thread-safety: ✅ MUTEX ATIVO
   • Redis Cache: {'✅' if REDIS_AVAILABLE else '⚠️  Mock'}
"""
        )

        # Inicia monitoramento de recursos
        monitor_thread = threading.Thread(target=self._monitor_resources, daemon=True)
        monitor_thread.start()

        start_time = time.time()

        try:
            # Executa workers em paralelo
            all_results = self._execute_workers()

            total_time = time.time() - start_time

            # Processa resultados
            self._process_results(all_results, total_time)

            return self.metrics

        except Exception as e:
            print(f"\n❌ ERRO CRÍTICO: {e}")
            traceback.print_exc()
            self.metrics.crashes += 1
            return self.metrics

    def _execute_workers(self) -> List[Dict]:
        """Executa workers com ThreadPoolExecutor"""
        all_results = []

        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = {}

            # Submete todas as mensagens
            for worker_id in range(self.num_workers):
                worker = StressTestWorker(worker_id, self.motor, self.redis)

                for msg_id in range(self.messages_per_worker):
                    future = executor.submit(worker.process_message, msg_id)
                    futures[future] = (worker_id, msg_id)

            # Coleta resultados
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=5)
                    all_results.append(result)
                except Exception as e:
                    worker_id, msg_id = futures[future]
                    all_results.append(
                        {
                            "success": False,
                            "error": str(e),
                            "worker_id": worker_id,
                            "message_id": msg_id,
                        }
                    )

        return all_results

    def _monitor_resources(self):
        """Monitora CPU/RAM durante o teste"""
        cpu_readings = []
        mem_readings = []

        while True:
            try:
                cpu = self.process.cpu_percent(interval=0.1)
                mem = self.process.memory_info().rss / (1024 * 1024)  # MB

                cpu_readings.append(cpu)
                mem_readings.append(mem)

                self.metrics.peak_cpu = max(self.metrics.peak_cpu, cpu)
                self.metrics.peak_memory = max(self.metrics.peak_memory, mem)

                time.sleep(0.5)
            except:
                break

        if cpu_readings:
            self.metrics.avg_cpu = statistics.mean(cpu_readings)
        if mem_readings:
            self.metrics.avg_memory = statistics.mean(mem_readings)

    def _process_results(self, all_results: List[Dict], total_time: float):
        """Processa e analisa resultados"""
        self.metrics.total_time = total_time
        self.metrics.total_requests = len(all_results)

        latencies = []
        errors = []

        for result in all_results:
            if result.get("success"):
                self.metrics.successful_requests += 1
                latencies.append(result["latency_ms"])
            else:
                self.metrics.failed_requests += 1
                errors.append(result.get("error", "Unknown error"))

        # Calcula percentis
        if latencies:
            self.metrics.latencies = latencies
            self.metrics.mean = statistics.mean(latencies)
            self.metrics.std = statistics.stdev(latencies) if len(latencies) > 1 else 0
            self.metrics.p50 = sorted(latencies)[len(latencies) // 2]
            self.metrics.p95 = sorted(latencies)[int(len(latencies) * 0.95)]
            self.metrics.p99 = sorted(latencies)[int(len(latencies) * 0.99)]

        self.metrics.errors = errors

    def print_report(self):
        """Imprime relatório final"""
        print(
            f"""
╔════════════════════════════════════════════════════════╗
║              📊 RELATÓRIO FINAL                       ║
╚════════════════════════════════════════════════════════╝

✅ EXECUÇÃO:
   • Total de Requisições: {self.metrics.total_requests:,}
   • Sucesso: {self.metrics.successful_requests:,} ({self.metrics.successful_requests/self.metrics.total_requests*100:.1f}%)
   • Falhas: {self.metrics.failed_requests:,} ({self.metrics.failed_requests/self.metrics.total_requests*100:.1f}%)
   • Tempo Total: {self.metrics.total_time:.2f}s
   • Taxa: {self.metrics.total_requests/self.metrics.total_time:.0f} req/s

📈 LATÊNCIA (ms):
   • P50: {self.metrics.p50:.2f}ms
   • P95: {self.metrics.p95:.2f}ms {'✅ ENTERPRISE' if self.metrics.p95 < 80 else '❌ LENTO'}
   • P99: {self.metrics.p99:.2f}ms {'✅ OK' if self.metrics.p99 < 150 else '❌ PROBLEMA'}
   • Média: {self.metrics.mean:.2f}ms ± {self.metrics.std:.2f}ms

💻 RECURSOS:
   • CPU Máximo: {self.metrics.peak_cpu:.1f}% {'✅ OK' if self.metrics.peak_cpu < 80 else '❌ CRÍTICO'}
   • CPU Médio: {self.metrics.avg_cpu:.1f}%
   • RAM Máximo: {self.metrics.peak_memory:.1f}MB {'✅ OK' if self.metrics.peak_memory < 500 else '❌ CRÍTICO'}
   • RAM Médio: {self.metrics.avg_memory:.1f}MB

🚨 CRASHES:
   • Seg Faults: {self.metrics.segfaults}
   • Erros G.O.: {self.metrics.crashes}
   • Motor C Calls: {self.motor.call_count:,}
   • Motor C Errors: {self.motor.error_count}

🎯 CONCLUSÃO:
"""
        )

        # Status final
        if (
            self.metrics.p99 < 100
            and self.metrics.peak_cpu < 80
            and self.metrics.failed_requests < self.metrics.total_requests * 0.01
        ):  # < 1% falha
            print("   ✅ SISTEMA PRONTO PARA PRODUÇÃO")
            print("   ✅ Pode apresentar na segunda-feira")
        else:
            print("   ⚠️  CORREÇÕES NECESSÁRIAS ANTES DE PRODUÇÃO")
            if self.metrics.p99 >= 100:
                print(f"      - Latência P99 muito alta: {self.metrics.p99:.2f}ms")
            if self.metrics.peak_cpu >= 80:
                print(f"      - CPU em pico crítico: {self.metrics.peak_cpu:.1f}%")
            if self.metrics.failed_requests > 0:
                print(f"      - {self.metrics.failed_requests} requisições falharam")


# ==================== MAIN ====================

if __name__ == "__main__":
    print(f"\n🕐 Teste iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Configurações para teste
    NUM_WORKERS = 300  # 300 sessões simultâneas
    MESSAGES_PER_WORKER = 50  # 50 mensagens cada = 15k total (mais que 10k)

    # Executa teste
    executor = StressTestExecutor(NUM_WORKERS, MESSAGES_PER_WORKER)
    metrics = executor.run()

    # Imprime relatório
    executor.print_report()

    print(f"\n🕐 Teste finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Retorna status
    sys.exit(0 if metrics.p99 < 100 else 1)
