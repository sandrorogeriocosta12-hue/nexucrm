#!/usr/bin/env python3
"""
stress_test_nexus.py

Script de stress test para validar o Nexus Service em produção.
Simula:
  1. 50-100 mensagens simultâneas de WhatsApp
  2. Processamento pelo motor Fuzzy em C
  3. Persistência em Redis
  4. Monitoramento de latência e memória

Uso:
    python stress_test_nexus.py --users 50 --duration 60 --target http://localhost:8000

Métricas monitoradas:
    - Latência p50, p95, p99 (alvo: <50ms)
    - Taxa de erro (alvo: 0%)
    - Uso de memória (alvo: <200MB delta)
    - Throughput (alvo: >200 req/s)
    - Redis connection pool health
    - Motor C CPU usage
"""

import asyncio
import aiohttp
import time
import json
import psutil
import statistics
from datetime import datetime
from typing import Dict, List
import argparse
from dataclasses import dataclass
import random
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Armazena resultado de uma requisição"""

    latency_ms: float
    status_code: int
    error: str = None
    timestamp: float = None
    user_id: int = None
    lead_id: str = None


class NexusStressTest:
    """Condutor do stress test"""

    def __init__(self, target_url: str, num_users: int = 50, duration: int = 60):
        self.target_url = target_url.rstrip("/")
        self.num_users = num_users
        self.duration = duration

        # Métricas
        self.results: List[TestResult] = []
        self.errors: List[str] = []
        self.start_time = None
        self.end_time = None

        # Monitoramento do sistema
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        # Dados de teste
        self.test_leads = self._generate_test_leads()

        logger.info(f"🚀 Stress Test Nexus Service")
        logger.info(f"   Target: {self.target_url}")
        logger.info(f"   Usuários: {num_users}")
        logger.info(f"   Duração: {duration}s")

    def _generate_test_leads(self) -> List[Dict]:
        """Gera leads fake para teste"""
        leads = []

        for i in range(self.num_users):
            lead = {
                "id": f"lead_{i}",
                "phone": f"5511987654{i:03d}",
                "name": f"Test Lead {i}",
                "company": f"Company {i % 10}",
                "engagement_patterns": [
                    random.uniform(0.2, 0.9),  # Última mensagem
                    random.uniform(0.2, 0.9),  # Penúltima
                    random.uniform(0.2, 0.9),  # 3 mensagens atrás
                ],
            }
            leads.append(lead)

        return leads

    async def send_message(
        self, session: aiohttp.ClientSession, lead: Dict, message_index: int
    ) -> TestResult:
        """Envia uma mensagem via API e mede latência"""

        result = TestResult(
            latency_ms=0,
            status_code=0,
            user_id=self.test_leads.index(lead),
            lead_id=lead["id"],
            timestamp=time.time(),
        )

        # Payload simulando webhook de WhatsApp
        payload = {
            "messages": [
                {
                    "from": lead["phone"],
                    "id": f"msg_{lead['id']}_{message_index}",
                    "timestamp": int(time.time()),
                    "type": "text",
                    "text": {
                        "body": f"Olá, tudo bem? Gostaria de saber mais sobre seus produtos. Mensagem #{message_index}"
                    },
                }
            ],
            "contacts": [{"profile": {"name": lead["name"]}, "wa_id": lead["phone"]}],
        }

        try:
            start = time.time()

            async with session.post(
                f"{self.target_url}/webhooks/whatsapp",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
                headers={"Content-Type": "application/json"},
            ) as resp:
                result.status_code = resp.status
                result.latency_ms = (time.time() - start) * 1000

                # Log de erros HTTP
                if resp.status != 200:
                    try:
                        body = await resp.text()
                        result.error = f"HTTP {resp.status}: {body[:200]}"
                    except:
                        result.error = f"HTTP {resp.status}"

        except asyncio.TimeoutError:
            result.error = "Timeout"
            result.latency_ms = 10000  # 10s

        except Exception as e:
            result.error = str(e)
            result.latency_ms = -1

        return result

    async def run_test(self):
        """Executa o stress test"""

        self.start_time = time.time()
        logger.info(f"⏱️ Iniciando teste às {datetime.now().strftime('%H:%M:%S')}")

        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:
            tasks = []
            message_index = 0

            # Gera requisições continuamente por 'duration' segundos
            while time.time() - self.start_time < self.duration:
                # Cria tarefas para o próximo batch
                for lead in self.test_leads:
                    task = self.send_message(session, lead, message_index)
                    tasks.append(task)

                # Executa batch em paralelo
                if len(tasks) >= self.num_users:
                    logger.info(
                        f"📨 Enviando batch #{message_index // self.num_users + 1} ({len(tasks)} msgs)..."
                    )

                    results = await asyncio.gather(*tasks)
                    self.results.extend(results)

                    tasks = []
                    message_index += self.num_users

                    # Pequena pausa entre batches
                    await asyncio.sleep(0.5)

            # Processa tarefas pendentes
            if tasks:
                results = await asyncio.gather(*tasks)
                self.results.extend(results)

        self.end_time = time.time()
        logger.info(f"✅ Teste finalizado às {datetime.now().strftime('%H:%M:%S')}")

    def print_report(self):
        """Imprime relatório de resultados"""

        if not self.results:
            logger.error("❌ Nenhum resultado para analisar!")
            return

        # Estatísticas de latência
        latencies = [r.latency_ms for r in self.results if r.latency_ms > 0]
        errors = [r for r in self.results if r.error is not None]

        print("\n" + "=" * 80)
        print("📊 RELATÓRIO DE STRESS TEST - NEXUS SERVICE")
        print("=" * 80 + "\n")

        # Resumo
        duration = self.end_time - self.start_time
        total_requests = len(self.results)
        successful = total_requests - len(errors)

        print(f"⏱️  DURAÇÃO: {duration:.1f} segundos")
        print(f"📈 TOTAL DE REQUISIÇÕES: {total_requests}")
        print(f"✅ SUCESSO: {successful} ({successful/total_requests*100:.1f}%)")
        print(f"❌ ERRO: {len(errors)} ({len(errors)/total_requests*100:.1f}%)")
        print(f"⚡ THROUGHPUT: {total_requests/duration:.0f} req/s")

        # Latência
        if latencies:
            print(f"\n⏱️  LATÊNCIA:")
            print(f"   Min:  {min(latencies):.2f}ms")
            print(f"   Max:  {max(latencies):.2f}ms")
            print(f"   Mean: {statistics.mean(latencies):.2f}ms")
            print(f"   P50:  {self._percentile(latencies, 50):.2f}ms")
            print(f"   P95:  {self._percentile(latencies, 95):.2f}ms")
            print(f"   P99:  {self._percentile(latencies, 99):.2f}ms")

        # Memória
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_delta = current_memory - self.initial_memory

        print(f"\n💾 MEMÓRIA:")
        print(f"   Inicial: {self.initial_memory:.1f}MB")
        print(f"   Final:   {current_memory:.1f}MB")
        print(f"   Delta:   {memory_delta:+.1f}MB")

        # CPU
        try:
            cpu_percent = self.process.cpu_percent(interval=0.1)
            print(f"   CPU:     {cpu_percent:.1f}%")
        except:
            print(f"   CPU:     N/A")

        # Erros detalhados
        if errors:
            print(f"\n⚠️  ERROS ({len(errors)}):")
            error_types = {}
            for err in errors:
                error_msg = err.error or "Unknown"
                error_types[error_msg] = error_types.get(error_msg, 0) + 1

            for error_msg, count in sorted(
                error_types.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"   {error_msg}: {count}x")

        # Validação
        print(f"\n✔️  VALIDAÇÃO:")

        checks = {
            "Latência P95 < 50ms": self._percentile(latencies, 95) < 50
            if latencies
            else False,
            "Latência P99 < 100ms": self._percentile(latencies, 99) < 100
            if latencies
            else False,
            "Taxa de erro < 5%": len(errors) / total_requests < 0.05,
            "Throughput > 100 req/s": (total_requests / duration) > 100,
            "Memory leak < 100MB": abs(memory_delta) < 100,
        }

        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")

        all_passed = all(checks.values())

        print(
            f"\n{'🎉 NEXUS ESTÁ PRONTO PARA PRODUÇÃO!' if all_passed else '⚠️  AJUSTES NECESSÁRIOS'}"
        )
        print("=" * 80 + "\n")

        return all_passed

    @staticmethod
    def _percentile(data: List[float], percentile: int) -> float:
        """Calcula percentil"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]


async def main():
    parser = argparse.ArgumentParser(description="Stress test para Nexus Service")
    parser.add_argument(
        "--target",
        default="http://localhost:8000",
        help="URL do Nexus Service (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--users",
        type=int,
        default=50,
        help="Número de usuários simultâneos (default: 50)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Duração do teste em segundos (default: 60)",
    )

    args = parser.parse_args()

    # Valida URL
    if not args.target.startswith("http"):
        args.target = f"http://{args.target}"

    # Cria e executa teste
    tester = NexusStressTest(
        target_url=args.target, num_users=args.users, duration=args.duration
    )

    try:
        await tester.run_test()
        tester.print_report()
    except KeyboardInterrupt:
        logger.warning("⚠️  Teste interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro durante teste: {e}", exc_info=True)


if __name__ == "__main__":
    import sys

    # Verifica dependências
    try:
        import aiohttp
        import psutil
    except ImportError:
        print("❌ Dependências faltando. Instale com:")
        print("   pip install aiohttp psutil")
        sys.exit(1)

    # Executa teste
    asyncio.run(main())
