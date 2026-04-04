#!/usr/bin/env python3
"""
🔐 Setup Wizard de Tokens Interativo
Configura WhatsApp, Telegram, SendGrid, Meta de forma fácil
"""

import os
import sys
import json
import requests
from typing import Dict, Tuple, Optional
from pathlib import Path
from datetime import datetime

class TokenValidator:
    """Valida tokens de cada plataforma"""
    
    @staticmethod
    def validate_whatsapp(token: str, phone_id: str) -> Tuple[bool, str]:
        """Valida WhatsApp token"""
        try:
            url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200 or "unsupported_get_request" in response.text:
                return True, "✅ WhatsApp token válido"
            else:
                return False, f"❌ Token inválido: {response.status_code}"
        except Exception as e:
            return False, f"❌ Erro ao validar: {str(e)}"
    
    @staticmethod
    def validate_telegram(token: str) -> Tuple[bool, str]:
        """Valida Telegram token"""
        try:
            url = f"https://api.telegram.org/bot{token}/getMe"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    bot_name = data.get("result", {}).get("first_name", "Bot")
                    return True, f"✅ Telegram bot '{bot_name}' conectado"
                else:
                    return False, "❌ Token inválido"
            else:
                return False, f"❌ Status {response.status_code}"
        except Exception as e:
            return False, f"❌ Erro ao validar: {str(e)}"
    
    @staticmethod
    def validate_sendgrid(token: str) -> Tuple[bool, str]:
        """Valida SendGrid API key"""
        try:
            url = "https://api.sendgrid.com/v3/mail/validate"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code in [200, 400]:
                return True, "✅ SendGrid API key válida"
            else:
                return False, f"❌ Status {response.status_code}"
        except Exception as e:
            return False, f"❌ Erro ao validar: {str(e)}"
    
    @staticmethod
    def validate_meta(token: str) -> Tuple[bool, str]:
        """Valida Meta Business token"""
        try:
            url = "https://graph.instagram.com/me"
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                user_id = data.get("id", "Unknown")
                return True, f"✅ Meta token válido (ID: {user_id})"
            else:
                return False, f"❌ Status {response.status_code}"
        except Exception as e:
            return False, f"❌ Erro ao validar: {str(e)}"


class TokenConfigWizard:
    """Wizard interativo para configurar tokens"""
    
    def __init__(self):
        self.env_file = Path(".env")
        self.env_content = self._load_env()
        self.validator = TokenValidator()
    
    def _load_env(self) -> Dict[str, str]:
        """Carrega .env atual"""
        env_dict = {}
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_dict[key.strip()] = value.strip()
        return env_dict
    
    def _save_env(self):
        """Salva .env atualizado"""
        with open(self.env_file, 'w') as f:
            # Preservar comentários e adicionar cabeçalho
            f.write("# 🔐 Nexus CRM - Configuração de Integração\n")
            f.write(f"# Última atualização: {datetime.now().isoformat()}\n\n")
            
            # Agrupar por seção
            sections = {
                "WHATSAPP": ["WHATSAPP_ACCESS_TOKEN", "WHATSAPP_PHONE_ID", "WHATSAPP_BUSINESS_ID"],
                "TELEGRAM": ["TELEGRAM_BOT_TOKEN"],
                "SENDGRID": ["SENDGRID_API_KEY", "EMAIL_FROM"],
                "META": ["META_BUSINESS_TOKEN", "INSTAGRAM_BUSINESS_ID"],
                "DATABASE": ["DATABASE_URL", "SQLALCHEMY_SILENCE_UBER_WARNING"],
                "API": ["API_KEY", "SECRET_KEY", "JWT_SECRET"],
            }
            
            # Escrever seções
            for section, keys in sections.items():
                if any(k in self.env_content for k in keys):
                    f.write(f"# === {section} ===\n")
                    for key in keys:
                        if key in self.env_content:
                            f.write(f"{key}={self.env_content[key]}\n")
                    f.write("\n")
            
            # Escrever resto
            written = set()
            for section, keys in sections.items():
                written.update(keys)
            
            remaining = {k: v for k, v in self.env_content.items() if k not in written}
            if remaining:
                f.write("# === Outras Configurações ===\n")
                for key, value in remaining.items():
                    f.write(f"{key}={value}\n")
    
    def print_header(self):
        """Printa cabeçalho do wizard"""
        print("""
╔════════════════════════════════════════════════════════════╗
║  🔐 NEXUS CRM - TOKEN CONFIGURATION WIZARD 🔐              ║
║                                                            ║
║  Configure todas as integrações em 5 minutos!            ║
╚════════════════════════════════════════════════════════════╝
        """)
    
    def ask_whatsapp(self):
        """Configurar WhatsApp"""
        print("\n📱 === WHATSAPP BUSINESS API ===")
        print("Você pode obter as credenciais em: https://developers.facebook.com/")
        
        token = input("\n1. Cole seu WHATSAPP_ACCESS_TOKEN: ").strip()
        if token:
            phone_id = input("2. Cole seu WHATSAPP_PHONE_ID: ").strip()
            business_id = input("3. Cole seu WHATSAPP_BUSINESS_ID: ").strip()
            
            # Validar
            is_valid, message = self.validator.validate_whatsapp(token, phone_id)
            print(message)
            
            if is_valid or input("\nSalvar mesmo assim? (s/n): ").lower() == "s":
                self.env_content["WHATSAPP_ACCESS_TOKEN"] = token
                self.env_content["WHATSAPP_PHONE_ID"] = phone_id
                self.env_content["WHATSAPP_BUSINESS_ID"] = business_id
                return True
        return False
    
    def ask_telegram(self):
        """Configurar Telegram"""
        print("\n🤖 === TELEGRAM BOT API ===")
        print("1. Fale com @BotFather no Telegram")
        print("2. Crie um novo bot: /newbot")
        print("3. Copie o token fornecido")
        
        token = input("\nCole seu TELEGRAM_BOT_TOKEN: ").strip()
        if token:
            is_valid, message = self.validator.validate_telegram(token)
            print(message)
            
            if is_valid or input("\nSalvar mesmo assim? (s/n): ").lower() == "s":
                self.env_content["TELEGRAM_BOT_TOKEN"] = token
                return True
        return False
    
    def ask_sendgrid(self):
        """Configurar SendGrid"""
        print("\n📧 === SENDGRID EMAIL API ===")
        print("1. Crie conta em: https://sendgrid.com/")
        print("2. Vá para: Settings > API Keys")
        print("3. Crie nova API Key (Full Access)")
        
        token = input("\nCole seu SENDGRID_API_KEY: ").strip()
        if token:
            is_valid, message = self.validator.validate_sendgrid(token)
            print(message)
            
            email = input("Cole o email de origem (ex: noreply@nexuscrm.tech): ").strip()
            
            if (is_valid or input("\nSalvar mesmo assim? (s/n): ").lower() == "s") and email:
                self.env_content["SENDGRID_API_KEY"] = token
                self.env_content["EMAIL_FROM"] = email
                return True
        return False
    
    def ask_meta(self):
        """Configurar Meta/Instagram"""
        print("\n📸 === META BUSINESS (Instagram/Facebook) ===")
        print("1. Vá para: facebook.com/business/tools")
        print("2. Selecione seu aplicativo")
        print("3. Copie o Business Token em Settings")
        
        token = input("\nCole seu META_BUSINESS_TOKEN: ").strip()
        if token:
            is_valid, message = self.validator.validate_meta(token)
            print(message)
            
            insta_id = input("Cole seu INSTAGRAM_BUSINESS_ID (opcional): ").strip()
            
            if is_valid or input("\nSalvar mesmo assim? (s/n): ").lower() == "s":
                self.env_content["META_BUSINESS_TOKEN"] = token
                if insta_id:
                    self.env_content["INSTAGRAM_BUSINESS_ID"] = insta_id
                return True
        return False
    
    def show_summary(self):
        """Mostra resumo do que foi configurado"""
        print("\n╔════════════════════════════════════════════════════════════╗")
        print("║  ✅ RESUMO DA CONFIGURAÇÃO                                 ║")
        print("╚════════════════════════════════════════════════════════════╝")
        
        configured = []
        if "WHATSAPP_ACCESS_TOKEN" in self.env_content:
            configured.append("📱 WhatsApp")
        if "TELEGRAM_BOT_TOKEN" in self.env_content:
            configured.append("🤖 Telegram")
        if "SENDGRID_API_KEY" in self.env_content:
            configured.append("📧 SendGrid")
        if "META_BUSINESS_TOKEN" in self.env_content:
            configured.append("📸 Meta/Instagram")
        
        print("\nIntegrações configuradas:")
        for item in configured:
            print(f"  ✅ {item}")
        
        print(f"\nArquivo .env salvo em: {self.env_file.absolute()}")
        print("\n🚀 Próximos passos:")
        print("  1. Deploy para Railway com os novos tokens")
        print("  2. Testar webhooks em /api/channels/status")
        print("  3. Começar a receber mensagens de verdade!")
    
    def run(self):
        """Executa o wizard"""
        self.print_header()
        
        print("\nQual integração deseja configurar? (pode selecionar múltiplas)")
        
        configured = []
        
        if input("\n[1/4] Configurar WhatsApp? (s/n): ").lower() == "s":
            if self.ask_whatsapp():
                configured.append("WhatsApp")
        
        if input("\n[2/4] Configurar Telegram? (s/n): ").lower() == "s":
            if self.ask_telegram():
                configured.append("Telegram")
        
        if input("\n[3/4] Configurar SendGrid? (s/n): ").lower() == "s":
            if self.ask_sendgrid():
                configured.append("SendGrid")
        
        if input("\n[4/4] Configurar Meta/Instagram? (s/n): ").lower() == "s":
            if self.ask_meta():
                configured.append("Meta")
        
        if configured:
            self._save_env()
            self.show_summary()
            return True
        else:
            print("\n❌ Nenhuma integração foi configurada.")
            return False


if __name__ == "__main__":
    wizard = TokenConfigWizard()
    success = wizard.run()
    sys.exit(0 if success else 1)
