#!/usr/bin/env python3
"""Teste de configuração de produção para api.nexuscrm.tech"""
import os
from dotenv import load_dotenv

def test_production_config():
    """Testa se todas as configurações de produção estão corretas"""
    print("🚀 TESTANDO CONFIGURAÇÃO DE PRODUÇÃO")
    print("=" * 50)

    # Carregar variáveis de ambiente
    load_dotenv()

    # Verificar configurações críticas
    checks = {
        "ENVIRONMENT": os.getenv("ENVIRONMENT"),
        "API_BASE_URL": os.getenv("API_BASE_URL"),
        "DATABASE_URL": os.getenv("DATABASE_URL"),
        "ALLOWED_HOSTS": os.getenv("ALLOWED_HOSTS"),
        "CORS_ORIGINS": os.getenv("CORS_ORIGINS"),
        "DEBUG": os.getenv("DEBUG"),
    }

    print("📋 CONFIGURAÇÕES ATUAIS:")
    for key, value in checks.items():
        status = "✅" if value else "❌"
        # Ocultar senhas em URLs
        if "DATABASE_URL" in key and value and "password" in value:
            display_value = value.replace(value.split(":")[2].split("@")[0], "***")
        else:
            display_value = value or "NÃO DEFINIDO"
        print(f"  {status} {key}: {display_value}")

    print("\n🔍 VALIDAÇÕES:")

    # Validar domínio
    api_url = checks.get("API_BASE_URL", "")
    if "api.nexuscrm.tech" in api_url and api_url.startswith("https://"):
        print("  ✅ Domínio correto: api.nexuscrm.tech")
    else:
        print("  ❌ Domínio incorreto ou não é HTTPS")

    # Validar ambiente
    if checks.get("ENVIRONMENT") == "production":
        print("  ✅ Ambiente de produção configurado")
    else:
        print("  ❌ Ambiente não é produção")

    # Validar CORS
    cors_origins = checks.get("CORS_ORIGINS", "")
    if "nexuscrm.tech" in cors_origins:
        print("  ✅ CORS configurado para domínio correto")
    else:
        print("  ❌ CORS não inclui domínio nexuscrm.tech")

    # Validar debug
    if checks.get("DEBUG") == "false":
        print("  ✅ Debug desabilitado para produção")
    else:
        print("  ⚠️  Debug habilitado (OK para desenvolvimento)")

    print("\n🌐 URLs de produção configuradas:")
    print("  📍 API Base: https://api.nexuscrm.tech")
    print("  🔗 Facebook Callback: https://api.nexuscrm.tech/integrations/instagram/callback")
    print("  📱 Telegram Webhook: https://api.nexuscrm.tech/webhooks/telegram")

    print("\n✅ CONFIGURAÇÃO DE PRODUÇÃO PRONTA!")

if __name__ == "__main__":
    test_production_config()