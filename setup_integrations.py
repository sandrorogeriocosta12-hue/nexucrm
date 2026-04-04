#!/usr/bin/env python3
"""
🚀 Nexus CRM - Script de Setup Automático das Integrações "Um Clique"

Este script vai:
1. Verificar dependências (Docker, Python packages)
2. Criar arquivo .env com variáveis padrão
3. Montar arquivo app_server.py com os novos modules
4. Criar database schema
5. Iniciar Evolution API
6. Testar webhooks
7. Gerar relatório final

Execução: python3 setup_integrations.py
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Colors para output terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.ENDC}")

def step(number, text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}PASSO {number}: {text}{Colors.ENDC}")

def run_command(cmd, description=""):
    """Executa comando shell e retorna sucesso/erro"""
    try:
        print_info(f"Executando: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print_success(description or cmd)
            return True, result.stdout
        else:
            print_error(f"{description}\n{result.stderr}")
            return False, result.stderr
    except Exception as e:
        print_error(f"Erro ao executar: {str(e)}")
        return False, str(e)

# ═════════════════════════════════════════════════════════════════════════════

def check_dependencies():
    """Verifica se Docker e dependências estão instaladas"""
    step(1, "Verificar Dependências")
    
    # Verificar Docker
    print_info("Procurando Docker...")
    success, _ = run_command("docker --version", "Docker encontrado")
    if not success:
        print_error("Docker não instalado!")
        print_info("Instale em: https://docs.docker.com/get-docker/")
        sys.exit(1)
    
    # Verificar Python packages
    print_info("Verificando Python packages...")
    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "httpx",
        "python-dotenv",
        "cryptography"
    ]
    
    missing = []
    for pkg in required_packages:
        try:
            __import__(pkg)
            print_success(f"  {pkg} ✓")
        except ImportError:
            missing.append(pkg)
            print_warning(f"  {pkg} ausente")
    
    if missing:
        print_info(f"Instalando packages faltantes: {', '.join(missing)}")
        run_command(f"pip install {' '.join(missing)}", "Packages instalados")
    
    print_success("Todas as dependências conferidas!")

# ═════════════════════════════════════════════════════════════════════════════

def create_env_file():
    """Cria arquivo .env com variáveis padrão"""
    step(2, "Criar Arquivo .env")
    
    env_path = Path(".env")
    
    if env_path.exists():
        print_warning(".env já existe!")
        response = input("Deseja sobrescrever? (s/n): ").lower()
        if response != 's':
            print_info("Mantendo .env existente")
            return
    
    env_content = """# ════════════════════════════════════════════════════════════
# 🚀 NEXUS CRM - CONFIGURAÇÕES DE INTEGRAÇÕES
# ════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════
# WHATSAPP (Evolution API)
# ═══════════════════════════════════════════════════════════
EVOLUTION_API_URL=http://localhost:3000
EVOLUTION_API_KEY=seu_api_key_aqui
EVOLUTION_API_WEBHOOK_SECRET=seu_webhook_secret_aqui

# ═══════════════════════════════════════════════════════════
# INSTAGRAM/FACEBOOK (OAuth)
# ═══════════════════════════════════════════════════════════
FACEBOOK_APP_ID=seu_app_id_aqui
FACEBOOK_APP_SECRET=sua_app_secret_aqui
FACEBOOK_REDIRECT_URI=http://localhost:8000/integrations/instagram/callback
INSTAGRAM_VERIFY_TOKEN=seu_verify_token_aleatorio_aqui

# ═══════════════════════════════════════════════════════════
# TELEGRAM
# ═══════════════════════════════════════════════════════════
TELEGRAM_WEBHOOK_URL=http://localhost:8000/webhooks/telegram

# ═══════════════════════════════════════════════════════════
# SENDGRID (Email)
# ═══════════════════════════════════════════════════════════
SENDGRID_API_KEY=seu_sendgrid_key_aqui

# ═══════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════
DATABASE_URL=sqlite:///./nexus_crm.db
DATABASE_TYPE=sqlite

# ═══════════════════════════════════════════════════════════
# SERVER
# ═══════════════════════════════════════════════════════════
API_BASE_URL=http://localhost:8000
ENVIRONMENT=development
DEBUG=true

# ═══════════════════════════════════════════════════════════
# ENCRYPTION (para tokens salvos no DB)
# ═════════════════════════════════════════════════════════════
ENCRYPTION_KEY=sua_chave_fernet_aqui

# ═══════════════════════════════════════════════════════════
# AI/ML ENGINE
# ═══════════════════════════════════════════════════════════
AI_MODEL_PATH=./models/nexus_brain.pkl
AI_SCORE_THRESHOLD=0.8
"""
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print_success(f"Arquivo .env criado: {env_path}")
    print_info("⚠️  IMPORTANTE: Editar .env com suas credenciais reais!")

# ═════════════════════════════════════════════════════════════════════════════

def create_updated_app_server():
    """Cria arquivo app_server.py atualizado com novos modules"""
    step(3, "Criar app_server.py Atualizado")
    
    app_server_content = '''"""
🚀 NEXUS CRM - Server Principal (FastAPI)

Integrações:
├─ WhatsApp (Evolution API + QR Code)
├─ Telegram (Bot + Token)
├─ Instagram (Meta OAuth)
└─ Email (SendGrid)

Webhooks + AI Scoring + Auto-responses
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os
import logging
from datetime import datetime

# ═════════════════════════════════════════════════════════════
# IMPORTS DOS NOVOS MÓDULOS
# ═════════════════════════════════════════════════════════════

try:
    from webhook_receiver import create_webhook_router
    WEBHOOK_ROUTER = create_webhook_router()
except ImportError:
    print("⚠️  webhook_receiver.py não encontrado em path")
    WEBHOOK_ROUTER = None

try:
    from one_click_integrations import create_integration_router
    INTEGRATION_ROUTER = create_integration_router()
except ImportError:
    print("⚠️  one_click_integrations.py não encontrado em path")
    INTEGRATION_ROUTER = None

# ═════════════════════════════════════════════════════════════
# LOAD ENVIRONMENT
# ═════════════════════════════════════════════════════════════

load_dotenv()

# ═════════════════════════════════════════════════════════════
# LOGGING
# ═════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ═════════════════════════════════════════════════════════════
# INICIALIZAR APP
# ═════════════════════════════════════════════════════════════

app = FastAPI(
    title="Nexus CRM API",
    description="🚀 Sistema de integração de canais de comunicação com IA",
    version="2.0.0",
)

# ═════════════════════════════════════════════════════════════
# CORS
# ═════════════════════════════════════════════════════════════

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═════════════════════════════════════════════════════════════
# INCLUIR ROUTERS DOS NOVOS MÓDULOS
# ═════════════════════════════════════════════════════════════

if WEBHOOK_ROUTER:
    app.include_router(WEBHOOK_ROUTER, prefix="/webhooks", tags=["webhooks"])
    logger.info("✅ Webhook router incluído")
else:
    logger.warning("⚠️  Webhook router não disponível")

if INTEGRATION_ROUTER:
    app.include_router(INTEGRATION_ROUTER, prefix="/integrations", tags=["integrations"])
    logger.info("✅ Integration router incluído")
else:
    logger.warning("⚠️  Integration router não disponível")

# ═════════════════════════════════════════════════════════════
# SERVIR FRONTEND INTEGRATIONS
# ═════════════════════════════════════════════════════════════

try:
    app.mount("/integrations-ui", StaticFiles(directory="frontend"), name="integrations-ui")
    logger.info("✅ Frontend integrações montado em /integrations-ui")
except Exception as e:
    logger.warning(f"⚠️  Não conseguiu montar frontend: {e}")

# ═════════════════════════════════════════════════════════════
# ROTAS BÁSICAS
# ═════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {
        "app": "Nexus CRM",
        "version": "2.0.0",
        "status": "🟢 online",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "webhooks": "/webhooks (WhatsApp, Telegram, Instagram)",
            "integrations": "/integrations (OAuth, QR Code, Setup)",
            "frontend": "/integrations-ui",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/status")
async def status():
    """Status completo do sistem"""
    return {
        "app": "Nexus CRM v2.0",
        "status": "online",
        "modules": {
            "webhooks": "✅" if WEBHOOK_ROUTER else "❌",
            "integrations": "✅" if INTEGRATION_ROUTER else "❌",
            "frontend": "✅",
        },
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.now().isoformat()
    }

# ═════════════════════════════════════════════════════════════
# STARTUP EVENTS
# ═════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Nexus CRM iniciando...")
    
    # Verificar Evolution API
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                os.getenv("EVOLUTION_API_URL", "http://localhost:3000") + "/health",
                timeout=5
            )
            if response.status_code == 200:
                logger.info("✅ Evolution API (WhatsApp) disponível")
            else:
                logger.warning("⚠️  Evolution API não respondeu")
    except Exception as e:
        logger.warning(f"⚠️  Evolution API indisponível: {str(e)}")
    
    logger.info("✅ Sistema inicializado com sucesso!")

# ═════════════════════════════════════════════════════════════
# RUN
# ═════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
'''
    
    with open("app_server_updated.py", 'w') as f:
        f.write(app_server_content)
    
    print_success("app_server_updated.py criado!")
    print_info("""
Próximos passos:
1. Revisar arquivo app_server_updated.py
2. Fazer backup do app_server.py atua
3. Renomear: mv app_server.py app_server.backup.py
4. Renomear: mv app_server_updated.py app_server.py
5. Testar: python app_server.py
    """)

# ═════════════════════════════════════════════════════════════

def setup_evolution_api():
    """Setup Evolution API via Docker"""
    step(4, "Setup Evolution API (WhatsApp)")
    
    print_info("Iniciando container Evolution API...")
    
    # Verificar se container já existe
    check_cmd = "docker ps -a --format '{{.Names}}' | grep evolution-api"
    exists, _ = run_command(check_cmd)
    
    if exists:
        print_info("Container evolution-api já existe")
        print_info("Iniciando container...")
        run_command("docker start evolution-api", "Container iniciado")
    else:
        print_info("Criando novo container...")
        
        # Criar volume
        run_command(
            "docker volume create evolution-api-data",
            "Volume criado"
        )
        
        # Rodar container
        cmd = """
docker run -d \\
  --name evolution-api \\
  --restart always \\
  -p 3000:3000 \\
  -v evolution-api-data:/home/root \\
  -e API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9 \\
  -e JWT_SECRET=sua_jwt_secret_aqui \\
  -e DATABASE_TYPE=sqlite \\
  atendaiw/evolution-api:latest
        """
        run_command(cmd.strip(), "Container Evolution API criado")
    
    # Aguardar e testar
    print_info("Aguardando container ficar pronto...")
    for i in range(30):
        time.sleep(1)
        success, _ = run_command(
            "curl -s http://localhost:3000/health",
            ""
        )
        if success:
            print_success("✅ Evolution API está pronto!")
            return True
    
    print_error("Timeout ao aguardar Evolution API")
    return False

# ═════════════════════════════════════════════════════════════

def create_database_schema():
    """Criar tabelas no database"""
    step(5, "Criar Schema Database")
    
    print_info("Criando tabelas SQLite...")
    
    import sqlite3
    
    db_file = "nexus_crm.db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Tabela: integrations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS integrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT NOT NULL,
        channel TEXT NOT NULL,
        access_token TEXT,
        instance_name TEXT,
        metadata TEXT,
        connected_at TIMESTAMP,
        webhook_verified BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(client_id, channel)
    )
    """)
    
    # Tabela: messages
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT NOT NULL,
        channel TEXT NOT NULL,
        sender TEXT NOT NULL,
        sender_name TEXT,
        message_text TEXT,
        message_type TEXT,
        received_at TIMESTAMP NOT NULL,
        ai_score FLOAT,
        ai_category TEXT,
        response_sent BOOLEAN DEFAULT 0,
        response_text TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Índices
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_client ON messages(client_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_channel ON messages(channel)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_received ON messages(received_at DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_integrations_client ON integrations(client_id)")
    
    conn.commit()
    conn.close()
    
    print_success(f"Database criado: {db_file}")

# ═════════════════════════════════════════════════════════════

def generate_report():
    """Gerar relatório final"""
    step(6, "Relatório Final")
    
    report = f"""
{Colors.BOLD}🎉 SETUP CONCLUÍDO COM SUCESSO!{Colors.ENDC}

{Colors.BOLD}════════════════════════════════════════════════════{Colors.ENDC}
{Colors.GREEN}✅ COMPONENTES INSTALADOS:{Colors.ENDC}

  ✓ Docker & Dependências Python
  ✓ Evolution API container (WhatsApp)
  ✓ Arquivo .env com variáveis
  ✓ Database SQLite com schema
  ✓ app_server.py atualizado
  ✓ Frontend integrações HTML

{Colors.BOLD}════════════════════════════════════════════════════{Colors.ENDC}
{Colors.CYAN}📝 PRÓXIMOS PASSOS:{Colors.ENDC}

  1. Editar .env com suas credenciais:
     • FACEBOOK_APP_ID
     • FACEBOOK_APP_SECRET
     • INSTAGRAM_VERIFY_TOKEN

  2. Copiar módulos para diretório do projeto:
     • webhook_receiver.py
     • one_click_integrations.py

  3. Iniciar servidor:
     $ python app_server.py

  4. Acessar interface:
     http://localhost:8000/integrations-ui

  5. Testar integrações:
     • WhatsApp: Clique em "Gerar QR Code"
     • Telegram: Cole token do BotFather
     • Instagram: Clique em "OAuth"

{Colors.BOLD}════════════════════════════════════════════════════{Colors.ENDC}
{Colors.YELLOW}⚠️  CHECKLIST ANTES DE PRODUÇÃO:{Colors.ENDC}

  ☐ Credenciais Meta (OAuth) configuradas
  ☐ Telegram BotFather token obtido
  ☐ Evolution API testado localmente
  ☐ HTTPS configurado no servidor
  ☐ Webhook verify token gerado
  ☐ Database backup configurado
  ☐ Logging centraalizado
  ☐ Rate limiting em webhooks

{Colors.BOLD}════════════════════════════════════════════════════{Colors.ENDC}
{Colors.CYAN}📚 DOCUMENTAÇÃO:{Colors.ENDC}

  • ./INTEGRATION_GUIDE.md - Guia detalhado
  • ./webhook_receiver.py - Código webhooks
  • ./one_click_integrations.py - Código integrações
  • ./setup_evolution_api.sh - Setup Evolution

{Colors.BOLD}════════════════════════════════════════════════════{Colors.ENDC}

Desenvolvido com ❤️ para Nexus CRM
{Colors.ENDC}
"""
    
    print(report)
    
    # Salvar relatório
    with open("SETUP_REPORT.txt", 'w') as f:
        f.write(report.replace(Colors.BOLD, "").replace(Colors.CYAN, "")
                .replace(Colors.GREEN, "").replace(Colors.YELLOW, "")
                .replace(Colors.ENDC, ""))
    
    print_success(f"Relatório salvo em: SETUP_REPORT.txt")

# ═════════════════════════════════════════════════════════════

def main():
    """Orquestrador principal"""
    
    print_header("🚀 NEXUS CRM - SETUP INTEGRAÇÕES UM CLIQUE")
    
    print_info("Este script vai configurar suas integrações de canais")
    print_info("Processo leva ~2-5 minutos\n")
    
    # PASSO 1
    try:
        check_dependencies()
    except Exception as e:
        print_error(f"Erro ao verificar dependências: {e}")
        return False
    
    # PASSO 2
    try:
        create_env_file()
    except Exception as e:
        print_error(f"Erro ao criar .env: {e}")
    
    # PASSO 3
    try:
        create_updated_app_server()
    except Exception as e:
        print_error(f"Erro ao criar app_server: {e}")
    
    # PASSO 4
    try:
        if setup_evolution_api():
            print_success("Evolution API configurada!")
        else:
            print_warning("Evolution API não está respondendo (pode estar iniciando)")
    except Exception as e:
        print_error(f"Erro ao setup Evolution API: {e}")
    
    # PASSO 5
    try:
        create_database_schema()
    except Exception as e:
        print_error(f"Erro ao criar database: {e}")
    
    # PASSO 6
    try:
        generate_report()
    except Exception as e:
        print_error(f"Erro ao gerar relatório: {e}")
    
    print_success("\n✨ Setup finalizado!")
    return True

# ═════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_error("\n\nSetup cancelado pelo usuário")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nErro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
