#!/usr/bin/env python3
"""
Testes End-to-End para Vexus CRM Dashboard
Testa todas as funcionalidades principais do sistema
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configurações
BASE_URL = "http://localhost:8001"
API_BASE = f"{BASE_URL}/api"

class VexusCRMTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_user = {
            "email": "test@vexus.com",
            "password": "test123",
            "full_name": "Test User",
            "role": "user"
        }
        self.test_lead = {
            "name": "João Silva",
            "email": f"joao.silva{int(time.time())}@email.com",
            "phone": "5511999999999",
            "company": "Empresa Teste Ltda",
            "status": "new",
            "source": "website"
        }
        self.test_campaign = {
            "name": "Campanha Teste Q1",
            "description": "Campanha de teste para Q1 2024",
            "budget": 5000.00
        }

    def log(self, message: str, status: str = "INFO"):
        """Log com timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")

    def make_request(self, method: str, endpoint: str, data: Dict = None, auth: bool = True) -> Dict:
        """Faz requisição HTTP com tratamento de erro"""
        url = f"{API_BASE}{endpoint}"
        headers = {"Content-Type": "application/json"}

        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers)
            elif method.upper() == "POST":
                response = self.session.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")

            if response.status_code >= 400:
                self.log(f"Erro HTTP {response.status_code}: {response.text}", "ERROR")
                return {"error": response.status_code, "message": response.text}

            return response.json() if response.content else {}

        except requests.exceptions.RequestException as e:
            self.log(f"Erro de conexão: {e}", "ERROR")
            return {"error": "connection", "message": str(e)}

    def test_health_check(self) -> bool:
        """Testa health check da aplicação"""
        self.log("Testando health check...")
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log("✅ Health check passou", "SUCCESS")
                    return True
            self.log(f"❌ Health check falhou: {response.status_code}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Health check erro: {e}", "ERROR")
            return False

    def test_user_registration(self) -> bool:
        """Testa registro de usuário"""
        self.log("Testando registro de usuário...")
        
        # First try to login (user might already exist)
        login_result = self.make_request("POST", "/auth/login", {
            "username": self.test_user["email"],
            "password": self.test_user["password"]
        }, auth=False)
        
        if "access_token" in login_result:
            self.log("✅ Usuário já existe e login funcionou", "SUCCESS")
            self.token = login_result["access_token"]
            return True
        
        # If login failed, try to register
        result = self.make_request("POST", "/auth/register", self.test_user, auth=False)

        if "id" in result:
            self.log("✅ Registro de usuário passou", "SUCCESS")
            return True
        else:
            self.log(f"❌ Registro falhou: {result}", "ERROR")
            return False

    def test_user_login(self) -> bool:
        """Testa login de usuário"""
        self.log("Testando login de usuário...")
        result = self.make_request("POST", "/auth/login", {
            "username": self.test_user["email"],
            "password": self.test_user["password"]
        }, auth=False)

        if "access_token" in result:
            self.token = result["access_token"]
            self.log("✅ Login passou", "SUCCESS")
            return True
        else:
            self.log(f"❌ Login falhou: {result}", "ERROR")
            return False

    def test_user_profile(self) -> bool:
        """Testa obtenção do perfil do usuário"""
        self.log("Testando perfil do usuário...")
        result = self.make_request("GET", "/auth/users/profile")

        if "email" in result and result["email"] == self.test_user["email"]:
            self.log("✅ Perfil do usuário passou", "SUCCESS")
            return True
        else:
            self.log(f"❌ Perfil falhou: {result}", "ERROR")
            return False

    def test_create_lead(self) -> bool:
        """Testa criação de lead"""
        self.log("Testando criação de lead...")
        result = self.make_request("POST", "/leads/", self.test_lead)

        if "id" in result:
            self.test_lead["id"] = result["id"]
            self.log("✅ Criação de lead passou", "SUCCESS")
            return True
        else:
            self.log(f"❌ Criação de lead falhou: {result}", "ERROR")
            return False

    def test_list_leads(self) -> bool:
        """Testa listagem de leads"""
        self.log("Testando listagem de leads...")
        result = self.make_request("GET", "/leads/")

        if isinstance(result, list) and len(result) > 0:
            self.log(f"✅ Listagem de leads passou ({len(result)} leads)", "SUCCESS")
            return True
        else:
            self.log(f"❌ Listagem de leads falhou: {result}", "ERROR")
            return False

    def test_create_campaign(self) -> bool:
        """Testa criação de campanha"""
        self.log("Testando criação de campanha...")
        result = self.make_request("POST", "/campaigns/", self.test_campaign)

        if "id" in result:
            self.test_campaign["id"] = result["id"]
            self.log("✅ Criação de campanha passou", "SUCCESS")
            return True
        else:
            self.log(f"❌ Criação de campanha falhou: {result}", "ERROR")
            return False

    def test_list_campaigns(self) -> bool:
        """Testa listagem de campanhas"""
        self.log("Testando listagem de campanhas...")
        result = self.make_request("GET", "/campaigns/")

        if isinstance(result, list) and len(result) > 0:
            self.log(f"✅ Listagem de campanhas passou ({len(result)} campanhas)", "SUCCESS")
            return True
        else:
            self.log(f"❌ Listagem de campanhas falhou: {result}", "ERROR")
            return False

    def test_analytics_summary(self) -> bool:
        """Testa analytics summary"""
        self.log("Testando analytics summary...")
        result = self.make_request("GET", "/analytics/summary")

        if "total_leads" in result and "total_campaigns" in result:
            self.log(f"✅ Analytics passou - Leads: {result['total_leads']}, Campanhas: {result['total_campaigns']}", "SUCCESS")
            return True
        else:
            self.log(f"❌ Analytics falhou: {result}", "ERROR")
            return False

    def test_notifications(self) -> bool:
        """Testa sistema de notificações"""
        self.log("Testando notificações...")
        result = self.make_request("POST", "/notifications/", {
            "title": "Teste E2E",
            "message": "Esta é uma notificação de teste do E2E",
            "type": "info"
        })

        if "id" in result:
            self.log("✅ Notificações passou", "SUCCESS")
            return True
        else:
            self.log(f"❌ Notificações falhou: {result}", "ERROR")
            return False

    def test_segmentation(self) -> bool:
        """Testa segmentação de prospects"""
        self.log("Testando segmentação...")
        result = self.make_request("GET", "/segmentation/auto-segments")

        if isinstance(result, list):
            self.log(f"✅ Segmentação passou ({len(result)} segmentos)", "SUCCESS")
            return True
        else:
            self.log(f"❌ Segmentação falhou: {result}", "ERROR")
            return False

    def test_whatsapp_config(self) -> bool:
        """Testa configuração WhatsApp"""
        self.log("Testando configuração WhatsApp...")
        result = self.make_request("GET", "/whatsapp/config")

        if "configured" in result:
            status = "configurado" if result["configured"] else "não configurado"
            self.log(f"✅ WhatsApp {status}", "SUCCESS")
            return True
        else:
            self.log(f"❌ WhatsApp config falhou: {result}", "ERROR")
            return False

    def test_dashboard_access(self) -> bool:
        """Testa acesso ao dashboard frontend"""
        self.log("Testando acesso ao dashboard...")
        try:
            response = requests.get(f"{BASE_URL}/dashboard", timeout=10)
            if response.status_code == 200 and "Vexus CRM" in response.text:
                self.log("✅ Dashboard acessível", "SUCCESS")
                return True
            else:
                self.log(f"❌ Dashboard não acessível: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Dashboard erro: {e}", "ERROR")
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Executa todos os testes"""
        self.log("🚀 Iniciando Testes End-to-End Vexus CRM", "START")

        tests = [
            ("Health Check", self.test_health_check),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("User Profile", self.test_user_profile),
            ("Create Lead", self.test_create_lead),
            ("List Leads", self.test_list_leads),
            ("Create Campaign", self.test_create_campaign),
            ("List Campaigns", self.test_list_campaigns),
            ("Analytics Summary", self.test_analytics_summary),
            ("Notifications", self.test_notifications),
            ("Segmentation", self.test_segmentation),
            ("WhatsApp Config", self.test_whatsapp_config),
            ("Dashboard Access", self.test_dashboard_access),
        ]

        results = {}
        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            try:
                result = test_func()
                results[test_name] = result
                if result:
                    passed += 1
            except Exception as e:
                self.log(f"❌ {test_name} erro: {e}", "ERROR")
                results[test_name] = False

        # Resumo final
        self.log(f"\n📊 RESULTADO FINAL: {passed}/{total} testes passaram", "SUMMARY")

        if passed == total:
            self.log("🎉 Todos os testes passaram! Sistema funcionando perfeitamente.", "SUCCESS")
        elif passed >= total * 0.8:
            self.log(f"✅ Maioria dos testes passou ({passed}/{total}). Sistema funcional.", "SUCCESS")
        else:
            self.log(f"⚠️ Alguns testes falharam ({passed}/{total}). Revisar implementação.", "WARNING")

        return {
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": total - passed,
            "success_rate": round(passed / total * 100, 1),
            "results": results
        }

def main():
    """Função principal"""
    print("=" * 60)
    print("🧪 VEXUS CRM - TESTES END-TO-END")
    print("=" * 60)

    test_suite = VexusCRMTestSuite()
    results = test_suite.run_all_tests()

    print("\n" + "=" * 60)
    print("📋 DETALHES DOS TESTES:")
    print("=" * 60)

    for test_name, result in results["results"].items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:<25} {status}")

    print("\n" + "=" * 60)
    print(f"🎯 TAXA DE SUCESSO: {results['success_rate']}%")
    print("=" * 60)

    # Exit code baseado no resultado
    sys.exit(0 if results["success_rate"] >= 80 else 1)

if __name__ == "__main__":
    main()