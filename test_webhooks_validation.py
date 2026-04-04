#!/usr/bin/env python3
"""
🔔 Sistema de Validação de Webhooks
Testa cada webhook e garante que está recebendo mensagens
"""

import asyncio
import requests
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from pathlib import Path

class WebhookTester:
    """Testa conexão de webhooks em tempo real"""
    
    def __init__(self, base_url: str = "https://api.nexuscrm.tech"):
        self.base_url = base_url
        self.results = []
    
    def print_header(self):
        print("""
╔════════════════════════════════════════════════════════════╗
║  🔔 NEXUS CRM - WEBHOOK VALIDATION SYSTEM 🔔               ║
║                                                            ║
║  Testa conexão e recepção em tempo real                   ║
╚════════════════════════════════════════════════════════════╝
        """)
    
    def test_whatsapp_webhook(self) -> Tuple[bool, str]:
        """Testa webhook do WhatsApp"""
        print("\n📱 Testando WhatsApp Webhook...")
        
        try:
            # 1. Verificar endpoint
            url = f"{self.base_url}/api/webhooks/whatsapp"
            
            # 2. Enviar mensagem de teste
            test_payload = {
                "entry": [{
                    "changes": [{
                        "value": {
                            "messages": [{
                                "from": "5511987654321",
                                "id": "wamid.test123",
                                "timestamp": str(int(datetime.now().timestamp())),
                                "type": "text",
                                "text": {
                                    "body": "Teste de webhook WhatsApp"
                                }
                            }]
                        }
                    }]
                }]
            }
            
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=test_payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print("   ✅ WhatsApp webhook respondendo (200 OK)")
                return True, "WhatsApp webhook funcionando"
            else:
                print(f"   ⚠️  Status {response.status_code}: {response.text[:100]}")
                return True, f"Webhook respondeu com status {response.status_code}"
        except requests.exceptions.ConnectionError:
            print("   ❌ Erro: URL não acessível")
            return False, "Erro de conexão"
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
            return False, str(e)
    
    def test_telegram_webhook(self) -> Tuple[bool, str]:
        """Testa webhook do Telegram"""
        print("\n🤖 Testando Telegram Webhook...")
        
        try:
            url = f"{self.base_url}/api/webhooks/telegram"
            
            test_payload = {
                "update_id": 123456789,
                "message": {
                    "message_id": 1,
                    "date": int(datetime.now().timestamp()),
                    "chat": {
                        "id": 123456789,
                        "first_name": "Teste",
                        "type": "private"
                    },
                    "from": {
                        "id": 123456789,
                        "first_name": "Teste",
                        "is_bot": False
                    },
                    "text": "Teste de webhook Telegram"
                }
            }
            
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=test_payload, headers=headers, timeout=10)
            
            if response.status_code in [200, 202]:
                print("   ✅ Telegram webhook respondendo (200 OK)")
                return True, "Telegram webhook funcionando"
            else:
                print(f"   ⚠️  Status {response.status_code}")
                return True, f"Webhook respondeu com status {response.status_code}"
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
            return False, str(e)
    
    def test_instagram_webhook(self) -> Tuple[bool, str]:
        """Testa webhook do Instagram"""
        print("\n📸 Testando Instagram Webhook...")
        
        try:
            url = f"{self.base_url}/api/webhooks/instagram"
            
            test_payload = {
                "entry": [{
                    "changes": [{
                        "value": {
                            "messages": [{
                                "from": "123456789",
                                "id": "m_test123",
                                "timestamp": int(datetime.now().timestamp()),
                                "text": "Teste de webhook Instagram"
                            }]
                        }
                    }]
                }]
            }
            
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=test_payload, headers=headers, timeout=10)
            
            if response.status_code in [200, 202]:
                print("   ✅ Instagram webhook respondendo (200 OK)")
                return True, "Instagram webhook funcionando"
            else:
                print(f"   ⚠️  Status {response.status_code}")
                return True, f"Webhook respondeu com status {response.status_code}"
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
            return False, str(e)
    
    def test_email_webhook(self) -> Tuple[bool, str]:
        """Testa webhook de Email"""
        print("\n📧 Testando Email Webhook...")
        
        try:
            url = f"{self.base_url}/api/webhooks/email"
            
            test_payload = {
                "event": "processed",
                "email": "test@example.com",
                "timestamp": int(datetime.now().timestamp()),
                "subject": "Teste de webhook Email"
            }
            
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=test_payload, headers=headers, timeout=10)
            
            if response.status_code in [200, 202]:
                print("   ✅ Email webhook respondendo (200 OK)")
                return True, "Email webhook funcionando"
            else:
                print(f"   ⚠️  Status {response.status_code}")
                return True, f"Webhook respondeu com status {response.status_code}"
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
            return False, str(e)
    
    def test_channels_status(self) -> Dict:
        """Testa endpoint de status de canais"""
        print("\n🔄 Testando status de canais...")
        
        try:
            url = f"{self.base_url}/api/channels/status"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print("   ✅ Endpoint de status respondendo")
                
                # Mostrar status de cada canal
                for channel, status in data.items():
                    if status.get("enabled"):
                        print(f"      ✅ {channel.upper()}: Conectado")
                    else:
                        print(f"      ⚠️  {channel.upper()}: Não configurado")
                
                return data
            else:
                print(f"   ❌ Status {response.status_code}")
                return {}
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
            return {}
    
    def generate_report(self, results: List[Tuple[str, bool, str]]) -> str:
        """Gera relatório de testes"""
        print("\n╔════════════════════════════════════════════════════════════╗")
        print("║  📊 RELATÓRIO DE WEBHOOKS                                  ║")
        print("╚════════════════════════════════════════════════════════════╝")
        
        total = len(results)
        passed = sum(1 for _, success, _ in results if success)
        
        print(f"\nTotal: {passed}/{total} webhooks funcionando")
        print(f"Taxa de sucesso: {(passed/total*100):.1f}%\n")
        
        print("Detalhes:")
        for webhook, success, message in results:
            status = "✅" if success else "❌"
            print(f"{status} {webhook}: {message}")
        
        # Instruções próximas
        print("\n🚀 Próximos passos:")
        if passed == total:
            print("  ✅ Todos os webhooks estão funcionando!")
            print("  1. Configure os webhooks nas plataformas externas")
            print("  2. Comece a enviar mensagens de teste")
            print("  3. Verifique em https://api.nexuscrm.tech/inbox-nexus.html")
        else:
            print(f"  ⚠️  {total - passed} webhook(s) com problema(s)")
            print("  1. Verifique as credenciais em .env")
            print("  2. Confirme que o servidor está rodando")
            print("  3. Execute novamente este teste")
        
        return f"Resultado: {passed}/{total} webhooks OK"
    
    def run(self, base_url: str = None):
        """Executa todos os testes"""
        if base_url:
            self.base_url = base_url
        
        self.print_header()
        
        print(f"\nTestando webhooks em: {self.base_url}")
        
        results = []
        
        # Rodar testes
        success, msg = self.test_whatsapp_webhook()
        results.append(("WhatsApp", success, msg))
        
        success, msg = self.test_telegram_webhook()
        results.append(("Telegram", success, msg))
        
        success, msg = self.test_instagram_webhook()
        results.append(("Instagram", success, msg))
        
        success, msg = self.test_email_webhook()
        results.append(("Email", success, msg))
        
        # Testar status de canais
        channel_status = self.test_channels_status()
        
        # Gerar relatório
        report = self.generate_report(results)
        
        return results, channel_status


if __name__ == "__main__":
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://api.nexuscrm.tech"
    
    tester = WebhookTester()
    tester.run(base_url)
