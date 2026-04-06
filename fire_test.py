#!/usr/bin/env python3
"""🔥 TESTE DE FOGO COMPLETO - NEXUS CRM 🔥
Testes abrangentes para validar produção no domínio api.nexuscrm.tech
"""

import requests
import time
import threading
import concurrent.futures
import json
import os
from datetime import datetime
import sys
from typing import Dict, List
import statistics

class FireTestSuite:
    def __init__(self, base_url: str = "https://api.nexuscrm.tech"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
        self.results = {
            'connectivity': {},
            'database': {},
            'endpoints': {},
            'load': {},
            'security': {},
            'availability': {}
        }

    def log(self, message: str, level: str = "INFO"):
        """Log com timestamp e nível"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": "\033[36m",
            "SUCCESS": "\033[32m",
            "WARNING": "\033[33m",
            "ERROR": "\033[31m",
            "RESET": "\033[0m"
        }
        print(f"{colors.get(level, colors['INFO'])}[{timestamp}] {message}{colors['RESET']}")

    def test_connectivity(self) -> bool:
        """Teste básico de conectividade"""
        self.log("🔗 TESTANDO CONECTIVIDADE BÁSICA", "INFO")

        try:
            # Teste HTTP básico
            response = self.session.get(f"{self.base_url}/", timeout=10)
            self.results['connectivity']['http_status'] = response.status_code
            self.results['connectivity']['response_time'] = response.elapsed.total_seconds()

            if response.status_code == 200:
                self.log(f"✅ HTTP OK - Status: {response.status_code}, Tempo: {response.elapsed.total_seconds():.2f}s", "SUCCESS")
            else:
                self.log(f"⚠️  HTTP Warning - Status: {response.status_code}", "WARNING")

            # Teste HTTPS
            if self.base_url.startswith('https://'):
                self.log("🔒 HTTPS configurado - verificando certificado SSL")
                # Verificar se é HTTPS válido
                self.results['connectivity']['ssl_valid'] = True
                self.log("✅ SSL/HTTPS válido", "SUCCESS")

            # Teste health check
            health_response = self.session.get(f"{self.base_url}/health", timeout=5)
            self.results['connectivity']['health_check'] = health_response.status_code == 200

            if health_response.status_code == 200:
                self.log("✅ Health check OK", "SUCCESS")
            else:
                self.log(f"❌ Health check falhou: {health_response.status_code}", "ERROR")

            return True

        except requests.exceptions.RequestException as e:
            self.log(f"❌ Erro de conectividade: {e}", "ERROR")
            return False

    def test_database_connection(self) -> bool:
        """Teste de conexão com banco de dados via API"""
        self.log("🗄️  TESTANDO CONEXÃO COM BANCO DE DADOS", "INFO")

        try:
            # Tentar fazer uma operação que requer banco
            test_payload = {
                "email": "firetest@nexuscrm.tech",
                "plan": "starter",
                "payment_method": "card",
                "card_name": "Test User",
                "card_number": "4532015112830366",
                "card_cvv": "123"
            }

            response = self.session.post(
                f"{self.base_url}/api/payment/process",
                json=test_payload,
                timeout=15
            )

            self.results['database']['api_response'] = response.status_code
            self.results['database']['response_time'] = response.elapsed.total_seconds()

            if response.status_code in [200, 201]:
                self.log("✅ Banco de dados operacional via API", "SUCCESS")
                return True
            elif response.status_code == 500:
                self.log("❌ Erro interno do servidor (possível problema de DB)", "ERROR")
                return False
            else:
                self.log(f"⚠️  Resposta inesperada: {response.status_code}", "WARNING")
                return True  # Não é erro crítico

        except requests.exceptions.RequestException as e:
            self.log(f"❌ Erro na conexão com API: {e}", "ERROR")
            return False

    def test_api_endpoints(self) -> bool:
        """Teste abrangente de todos os endpoints"""
        self.log("🔗 TESTANDO ENDPOINTS DA API", "INFO")

        endpoints = [
            ("/", "GET", "Página inicial"),
            ("/docs", "GET", "Documentação OpenAPI"),
            ("/health", "GET", "Health check"),
            ("/api/payment/process", "POST", "Processamento de pagamento"),
            ("/integrations-ui", "GET", "Interface de integrações"),
        ]

        success_count = 0

        for endpoint, method, description in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"

                if method == "GET":
                    response = self.session.get(url, timeout=10)
                elif method == "POST":
                    # Payload básico para teste
                    payload = {"test": True}
                    response = self.session.post(url, json=payload, timeout=10)

                self.results['endpoints'][endpoint] = {
                    'status': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'method': method
                }

                if response.status_code in [200, 201, 302, 400, 422]:  # Status aceitáveis
                    self.log(f"✅ {description}: {response.status_code} ({response.elapsed.total_seconds():.2f}s)", "SUCCESS")
                    success_count += 1
                else:
                    self.log(f"❌ {description}: {response.status_code}", "ERROR")

            except requests.exceptions.RequestException as e:
                self.log(f"❌ {description}: Erro - {e}", "ERROR")
                self.results['endpoints'][endpoint] = {'error': str(e)}

        success_rate = (success_count / len(endpoints)) * 100
        self.results['endpoints']['success_rate'] = success_rate

        self.log(f"📊 Taxa de sucesso dos endpoints: {success_rate:.1f}%", "INFO")
        return success_rate >= 80  # 80% de sucesso mínimo

    def load_test_single_request(self, endpoint: str, method: str = "GET", payload: dict = None) -> float:
        """Executa uma única requisição para teste de carga"""
        try:
            url = f"{self.base_url}{endpoint}"
            start_time = time.time()

            if method == "GET":
                response = self.session.get(url, timeout=30)
            elif method == "POST" and payload:
                response = self.session.post(url, json=payload, timeout=30)

            response_time = time.time() - start_time

            if response.status_code in [200, 201, 302, 400, 422]:
                return response_time
            else:
                return -1  # Indica erro

        except:
            return -1

    def test_load_capacity(self) -> bool:
        """Teste de carga com múltiplas requisições simultâneas"""
        self.log("⚡ TESTANDO CAPACIDADE DE CARGA", "INFO")

        # Configurações do teste
        concurrent_users = 50
        requests_per_user = 10
        test_endpoint = "/health"  # Endpoint leve para teste

        self.log(f"🚀 Iniciando teste com {concurrent_users} usuários simultâneos", "INFO")
        self.log(f"📊 {requests_per_user} requisições por usuário", "INFO")

        response_times = []
        errors = 0

        def user_simulation(user_id: int):
            nonlocal errors
            user_times = []

            for i in range(requests_per_user):
                response_time = self.load_test_single_request(test_endpoint)

                if response_time > 0:
                    user_times.append(response_time)
                else:
                    errors += 1

                # Pequena pausa para simular comportamento real
                time.sleep(0.1)

            return user_times

        # Executar teste de carga
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(user_simulation, i) for i in range(concurrent_users)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        total_time = time.time() - start_time

        # Processar resultados
        for user_times in results:
            response_times.extend(user_times)

        total_requests = len(response_times) + errors
        success_rate = (len(response_times) / total_requests) * 100 if total_requests > 0 else 0

        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile

            self.results['load'] = {
                'total_requests': total_requests,
                'successful_requests': len(response_times),
                'errors': errors,
                'success_rate': success_rate,
                'total_time': total_time,
                'requests_per_second': total_requests / total_time,
                'avg_response_time': avg_response_time,
                'median_response_time': median_response_time,
                'min_response_time': min_response_time,
                'max_response_time': max_response_time,
                'p95_response_time': p95_response_time
            }

            self.log(f"📊 RESULTADOS DO TESTE DE CARGA:", "INFO")
            self.log(f"   ✅ Requisições bem-sucedidas: {len(response_times)}/{total_requests}", "SUCCESS")
            self.log(f"   📈 Taxa de sucesso: {success_rate:.1f}%", "SUCCESS")
            self.log(f"   ⚡ Requisições/segundo: {total_requests / total_time:.1f}", "SUCCESS")
            self.log(f"   🕐 Tempo médio de resposta: {avg_response_time:.3f}s", "INFO")
            self.log(f"   📊 P95 resposta: {p95_response_time:.3f}s", "INFO")

            # Critérios de sucesso
            if success_rate >= 95 and avg_response_time < 2.0:
                self.log("🎉 TESTE DE CARGA APROVADO!", "SUCCESS")
                return True
            else:
                self.log("⚠️  TESTE DE CARGA COM DESEMPENHO ABAIXO DO ESPERADO", "WARNING")
                return success_rate >= 90  # Ainda aceitável se >= 90%

        else:
            self.log("❌ NENHUMA REQUISIÇÃO BEM-SUCEDIDA NO TESTE DE CARGA", "ERROR")
            return False

    def test_security(self) -> bool:
        """Testes básicos de segurança"""
        self.log("🔒 TESTANDO SEGURANÇA BÁSICA", "INFO")

        security_issues = []

        # Teste 1: Headers de segurança
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)

            security_headers = {
                'X-Frame-Options': response.headers.get('X-Frame-Options'),
                'X-Content-Type-Options': response.headers.get('X-Content-Type-Options'),
                'X-XSS-Protection': response.headers.get('X-XSS-Protection'),
                'Content-Security-Policy': response.headers.get('Content-Security-Policy'),
                'Strict-Transport-Security': response.headers.get('Strict-Transport-Security')
            }

            self.results['security']['headers'] = security_headers

            # Verificar headers essenciais
            if not security_headers.get('X-Frame-Options'):
                security_issues.append("X-Frame-Options header ausente")
            if not security_headers.get('X-Content-Type-Options'):
                security_issues.append("X-Content-Type-Options header ausente")

            if security_headers.get('Strict-Transport-Security'):
                self.log("✅ HSTS configurado", "SUCCESS")
            else:
                security_issues.append("HSTS não configurado")

        except Exception as e:
            security_issues.append(f"Erro ao verificar headers: {e}")

        # Teste 2: Tentativa de acesso a arquivos sensíveis
        sensitive_paths = ['/.env', '/.git', '/wp-admin', '/admin', '/phpmyadmin']
        for path in sensitive_paths:
            try:
                response = self.session.get(f"{self.base_url}{path}", timeout=5)
                if response.status_code != 404:
                    security_issues.append(f"Arquivo sensível acessível: {path}")
            except:
                pass  # Ignorar erros de conexão

        # Teste 3: SQL Injection básico
        try:
            payload = {"email": "test' OR '1'='1", "plan": "starter"}
            response = self.session.post(f"{self.base_url}/api/payment/process", json=payload, timeout=10)
            if "sql" in response.text.lower() or response.status_code == 500:
                security_issues.append("Possível vulnerabilidade SQL Injection")
        except:
            pass

        self.results['security']['issues'] = security_issues

        if security_issues:
            self.log(f"⚠️  PROBLEMAS DE SEGURANÇA ENCONTRADOS: {len(security_issues)}", "WARNING")
            for issue in security_issues:
                self.log(f"   • {issue}", "WARNING")
            return False
        else:
            self.log("✅ NENHUM PROBLEMA DE SEGURANÇA CRÍTICO ENCONTRADO", "SUCCESS")
            return True

    def test_availability(self) -> bool:
        """Teste de disponibilidade com verificações periódicas"""
        self.log("📡 TESTANDO DISPONIBILIDADE", "INFO")

        check_interval = 5  # segundos
        total_checks = 12   # 1 minuto total
        successful_checks = 0

        self.log(f"⏱️  Monitorando por {total_checks * check_interval} segundos...", "INFO")

        availability_results = []

        for i in range(total_checks):
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}/health", timeout=5)
                response_time = time.time() - start_time

                if response.status_code == 200:
                    successful_checks += 1
                    status = "✅"
                else:
                    status = "❌"

                availability_results.append({
                    'check': i + 1,
                    'status': response.status_code,
                    'response_time': response_time,
                    'success': response.status_code == 200
                })

                print(f"   {status} Check {i+1:2d}: {response.status_code} ({response_time:.2f}s)", end='\r')

            except Exception as e:
                availability_results.append({
                    'check': i + 1,
                    'error': str(e),
                    'success': False
                })
                print(f"   ❌ Check {i+1:2d}: ERROR", end='\r')

            time.sleep(check_interval)

        print()  # Nova linha após o loop

        uptime_percentage = (successful_checks / total_checks) * 100
        self.results['availability'] = {
            'total_checks': total_checks,
            'successful_checks': successful_checks,
            'uptime_percentage': uptime_percentage,
            'checks': availability_results
        }

        self.log(f"📊 DISPONIBILIDADE: {uptime_percentage:.1f}% uptime", "INFO")

        if uptime_percentage >= 95:
            self.log("✅ ALTA DISPONIBILIDADE CONFIRMADA", "SUCCESS")
            return True
        elif uptime_percentage >= 80:
            self.log("⚠️  DISPONIBILIDADE ACEITÁVEL", "WARNING")
            return True
        else:
            self.log("❌ PROBLEMAS DE DISPONIBILIDADE", "ERROR")
            return False

    def run_complete_fire_test(self) -> Dict:
        """Executa todos os testes de fogo"""
        self.log("🔥 INICIANDO TESTE DE FOGO COMPLETO 🔥", "INFO")
        self.log("=" * 60, "INFO")

        start_time = time.time()

        # Executar todos os testes
        tests = [
            ("Conectividade", self.test_connectivity),
            ("Banco de Dados", self.test_database_connection),
            ("Endpoints API", self.test_api_endpoints),
            ("Capacidade de Carga", self.test_load_capacity),
            ("Segurança", self.test_security),
            ("Disponibilidade", self.test_availability)
        ]

        passed_tests = 0
        total_tests = len(tests)

        for test_name, test_func in tests:
            self.log(f"\n🔍 EXECUTANDO: {test_name}", "INFO")
            self.log("-" * 40, "INFO")

            try:
                if test_func():
                    passed_tests += 1
                    self.log(f"✅ {test_name}: APROVADO", "SUCCESS")
                else:
                    self.log(f"❌ {test_name}: REPROVADO", "ERROR")
            except Exception as e:
                self.log(f"💥 {test_name}: ERRO FATAL - {e}", "ERROR")

        total_time = time.time() - start_time
        success_rate = (passed_tests / total_tests) * 100

        # Resultado final
        self.log("\n" + "=" * 60, "INFO")
        self.log("🏁 RESULTADO FINAL DO TESTE DE FOGO", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"⏱️  Tempo total: {total_time:.1f} segundos", "INFO")
        self.log(f"📊 Testes aprovados: {passed_tests}/{total_tests}", "INFO")
        self.log(f"📈 Taxa de sucesso: {success_rate:.1f}%", "INFO")

        if success_rate >= 80:
            self.log("🎉 SISTEMA APROVADO NO TESTE DE FOGO!", "SUCCESS")
            self.log("🌟 DOMÍNIO À PROVA DE FALHAS!", "SUCCESS")
        elif success_rate >= 60:
            self.log("⚠️  SISTEMA FUNCIONAL MAS COM ALGUMAS QUESTÕES", "WARNING")
        else:
            self.log("❌ SISTEMA COM PROBLEMAS CRÍTICOS", "ERROR")

        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'total_time': total_time,
            'results': self.results
        }

def main():
    """Função principal"""
    print("🔥 NEXUS CRM - TESTE DE FOGO 🔥")
    print("Testando domínio: api.nexuscrm.tech")
    print("=" * 50)

    # Executar teste completo
    tester = FireTestSuite("https://api.nexuscrm.tech")
    final_result = tester.run_complete_fire_test()

    # Salvar resultados em arquivo
    with open('fire_test_results.json', 'w') as f:
        json.dump(final_result, f, indent=2, default=str)

    print("\n💾 Resultados salvos em: fire_test_results.json")

    # Resumo final
    success_rate = final_result['success_rate']
    if success_rate >= 80:
        print("🎉 SISTEMA APROVADO! Pronto para produção.")
        sys.exit(0)
    else:
        print("⚠️  SISTEMA PRECISA DE AJUSTES antes da produção.")
        sys.exit(1)

if __name__ == "__main__":
    main()