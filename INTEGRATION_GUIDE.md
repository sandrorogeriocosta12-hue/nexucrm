# 🚀 Nexus CRM - Guia de Integração "Um Clique"

## Visão Geral
Sistema completo de integração com 4 canais (WhatsApp, Telegram, Instagram, Email) usando:
- ✅ **WhatsApp**: QR Code (Evolution API)
- ✅ **Telegram**: Token simples + BotFather
- ✅ **Instagram**: OAuth Facebook (permissions automáticas)
- ✅ **Email**: SendGrid (em breve)

---

## 📋 Pré-requisitos

### 1️⃣ Sistemas Operacionais
```bash
# Ubuntu/Linux
sudo apt update && sudo apt install docker.io docker-compose

# macOS
brew install docker
# ou use Docker Desktop

# Windows
# Download Docker Desktop oficial
```

### 2️⃣ Contas e Credenciais Necessárias

#### WhatsApp (Evolution API)
- ✅ Docker instalado (É tudo!)
- Container roda localmente: `http://localhost:3000`

#### Telegram
- 📝 Chat com @BotFather no Telegram
- Comando: `/newbot`
- Recebe token: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`

#### Instagram (Meta OAuth)
- 🔐 App ID: `https://developers.facebook.com/apps/create`
- 🔑 App Secret: gerado no painel
- 🔗 Redirect URI: `https://api.nexuscrm.tech/integrations/instagram/callback`

#### SendGrid (Email)
- 🔑 API Key: https://app.sendgrid.com/settings/api_keys

---

## ⚙️ Configuração Passo a Passo

### PASSO 1: Setup Evolution API (WhatsApp)

```bash
# Clonar repo (opcional - nosso script faz tudo)
chmod +x setup_evolution_api.sh
./setup_evolution_api.sh

# Resultado: Container rodando em http://localhost:3000
# Health check:
curl http://localhost:3000/health
# Resposta esperada: { "status": "ok" }
```

**Arquivo**: [setup_evolution_api.sh](setup_evolution_api.sh)

---

### PASSO 2: Integrar Módulos no app_server.py

```python
# No seu app_server.py (após imports do FastAPI):

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from webhook_receiver import app as webhook_app
from one_click_integrations import app as integration_app

app = FastAPI()

# ✅ Incluir routers
app.include_router(webhook_app.router, tags=["webhooks"])
app.include_router(integration_app.router, tags=["integrations"])

# ✅ Servir frontend HTML estático
app.mount("/integrations", StaticFiles(directory="frontend", html=True), name="integrations")

# Seu código existente continua aqui...
```

---

### PASSO 3: Configurar Environment Variables (.env)

```bash
# .env na raiz do projeto

# ═══════════════════════════════════════════════
# WHATSAPP (Evolution API)
# ═══════════════════════════════════════════════
EVOLUTION_API_URL=http://localhost:3000
EVOLUTION_API_KEY=seu_api_key_gerado

# ═══════════════════════════════════════════════
# INSTAGRAM/FACEBOOK (OAuth)
# ═══════════════════════════════════════════════
FACEBOOK_APP_ID=123456789
FACEBOOK_APP_SECRET=sua_app_secret
FACEBOOK_REDIRECT_URI=https://api.nexuscrm.tech/integrations/instagram/callback
INSTAGRAM_VERIFY_TOKEN=seu_token_aleatorio

# ═══════════════════════════════════════════════
# TELEGRAM
# ═══════════════════════════════════════════════
TELEGRAM_WEBHOOK_URL=https://api.nexuscrm.tech/webhooks/telegram

# ═══════════════════════════════════════════════
# SENDGRID (Email)
# ═══════════════════════════════════════════════
SENDGRID_API_KEY=SG.sua_key_aqui

# ═══════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════
DATABASE_URL=postgresql://user:password@localhost/nexus_crm
```

---

### PASSO 4: Criar Tabela de Integrações (Database)

```sql
-- SQL Script para criar a tabela de integrações

CREATE TABLE IF NOT EXISTS integrations (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(100) NOT NULL,
    channel VARCHAR(20) NOT NULL,  -- whatsapp, telegram, instagram, email
    access_token TEXT,              -- JWT ou token OAuth
    instance_name VARCHAR(100),     -- ex: nexus_client123
    metadata JSONB,                 -- dados extras por canal
    connected_at TIMESTAMP,
    webhook_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(client_id, channel)
);

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(100) NOT NULL,
    channel VARCHAR(20) NOT NULL,  -- whatsapp, telegram, instagram
    sender VARCHAR(100) NOT NULL,
    sender_name VARCHAR(200),
    message_text TEXT,
    message_type VARCHAR(20),      -- text, image, audio, etc
    received_at TIMESTAMP NOT NULL,
    ai_score FLOAT,                -- 0-100
    ai_category VARCHAR(50),       -- lead, support, spam, etc
    response_sent BOOLEAN DEFAULT FALSE,
    response_text TEXT,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, processed, responded
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

CREATE INDEX idx_messages_client_channel ON messages(client_id, channel);
CREATE INDEX idx_messages_received_at ON messages(received_at DESC);
```

---

## 🎮 Como Usar (Cliente)

### 1. Acessar Dashboard
```
https://api.nexuscrm.tech/integrations
```

### 2. WhatsApp - "Gerar QR Code"
```
Cliente clica botão → QR aparece
Cliente aponta celular → WhatsApp escaneia automaticamente
Sistema escuta mensagens em tempo real
```

### 3. Telegram - "Colar Token"
```
Cliente abre @BotFather → /newbot
Copia token: 123456:ABCdef...
Cola no campo Nexus
Click "✓" → validado!
```

### 4. Instagram - "Conectar com Facebook"
```
Cliente clica botão
Redirecionado para login Meta (seguro)
Autoriza permissões
Meta envia código → Nexus valida
Auto-conectado! ✓
```

---

## 📡 Fluxo de Mensagens

```
┌─── Cliente envia mensagem ─────────────┐
│                                        │
├─ WhatsApp → Evolution API → Webhook    │
├─ Telegram → Telegram API → Webhook     │
├─ Instagram → Meta → Webhook            │
│                                        │
→ POST /webhooks/{channel}/{id}
  ├─ database: salvar mensagem
  ├─ ai_engine: score (0-100)
  ├─ se score > 0.8:
  │   └─ auto_response: mandar reply
  └─ status: "processed"
```

---

## 🧪 Testar Locally

### Test 1: WhatsApp QR
```bash
# Terminal 1: Rodar servidor
python app_server.py

# Terminal 2: Gerar QR
curl -X POST http://localhost:8000/integrations/whatsapp/generate-qrcode \
  -H "Content-Type: application/json" \
  -d '{"client_id":"test123","instance_name":"nexus_test"}'

# Resposta: { "qrcode_url": "data:image/png;base64,..." }
```

### Test 2: Telegram
```bash
# Botão que abre: https://t.me/BotFather
# User cria bot: /newbot
# Copia token
# POST para conectar:
curl -X POST http://localhost:8000/integrations/telegram/connect \
  -H "Content-Type: application/json" \
  -d '{"client_id":"test123","bot_token":"123456:ABCdef..."}'
```

### Test 3: Webhook (simular mensagem)
```bash
# Simular WhatsApp
curl -X POST http://localhost:8000/webhooks/whatsapp/nexus_test \
  -H "Content-Type: application/json" \
  -d '{
    "event":"messages.upsert",
    "data":{
      "messages":[{
        "from":"5511987654321",
        "text":"Olá, gostaria de saber sobre seus planos",
        "messageTimestamp":1234567890
      }]
    }
  }'
```

---

## 🔒 Segurança

### 1. Webhook Verification (Meta)
```
GET /webhooks/instagram?hub.mode=subscribe&hub.challenge=12345
Nexus valida hub.verify_token
Retorna hub.challenge se válido
Meta verifica resposta → confia em nossos webhooks
```

### 2. Token Storage
```python
# Tokens armazenados com hash no database
from cryptography.fernet import Fernet

cipher = Fernet(ENCRYPTION_KEY)
encrypted_token = cipher.encrypt(raw_token.encode())
# Salvar encrypted_token no database

# Ao usar:
token = cipher.decrypt(encrypted_token).decode()
```

### 3. API Authentication
```python
# Cada webhook tem secret token obrigatório
@app.post("/webhooks/{channel}/{client_id}")
async def webhook(request: Request, client_id: str):
    # Validar secret do query param
    secret = request.query_params.get("secret")
    if secret != get_client_webhook_secret(client_id):
        raise HTTPException(status_code=401)
```

---

## 📊 Status Dashboard

### Endpoint: GET /integrations/status/{client_id}
```json
{
  "client_id": "abc123",
  "channels": [
    {
      "channel": "whatsapp",
      "status": "connected",
      "instance_name": "nexus_abc123",
      "connected_at": "2024-01-15T10:30:00Z"
    },
    {
      "channel": "telegram",
      "status": "connected",
      "bot_name": "NexusBot",
      "connected_at": "2024-01-15T10:35:00Z"
    },
    {
      "channel": "instagram",
      "status": "connected",
      "account_name": "empresa_xyz",
      "connected_at": "2024-01-15T10:40:00Z"
    },
    {
      "channel": "email",
      "status": "disconnected"
    }
  ],
  "message_count": 145,
  "processed_today": 87
}
```

---

## 🚀 Deployment (Railway/Render)

### Railway Environment Variables
```
EVOLUTION_API_URL=http://localhost:3000
FACEBOOK_APP_ID=...
FACEBOOK_APP_SECRET=...
DATABASE_URL=postgresql://...
```

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copiar módulos
COPY app_server.py .
COPY webhook_receiver.py .
COPY one_click_integrations.py .
COPY frontend/ ./frontend/

CMD ["uvicorn", "app_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📞 Suporte & Troubleshooting

### WhatsApp QR não aparece?
```bash
# Verificar Evolution API
curl http://localhost:3000/health

# Logs do container
docker logs evolution-api

# Criar nova instância
curl -X POST http://localhost:3000/instance/create \
  -H "x-api-key: YOUR_KEY" \
  -d '{"instanceName":"debug_test"}'
```

### Telegram não conecta?
```bash
# Validar token
curl https://api.telegram.org/bot{TOKEN}/getMe

# Verificar webhook registrado
curl https://api.telegram.org/bot{TOKEN}/getWebhookInfo
```

### Instagram OAuth falha?
```bash
# Verificar redirect URI exato
# Confirmar App Secret
# Testar OAuth URL manualmente em navegador
```

---

## 📅 Timeline Execução (Quinta-Segunda)

```
QUINTA (hoje)
├─ ✅ Setup Evolution API (docker)
├─ ✅ Criar webhook_receiver.py
├─ ✅ Criar one_click_integrations.py
└─ ✅ Criar frontend HTML

SEXTA
├─ Integrar módulos em app_server.py
├─ Testar QR Code WhatsApp
├─ Testar Telegram token
└─ Testar Instagram OAuth

SÁBADO
├─ Integrar NexusLearningEngine (AI scoring)
├─ Implementar auto-responses
└─ Dashboard de status

DOMINGO
├─ QA completo (todos 4 canais)
├─ Load testing
└─ Documentação final

SEGUNDA 🎉
└─ GO LIVE - Clientes usando!!!
```

---

## 📚 Referências

- [Arquivo webhook_receiver.py](webhook_receiver.py) - Escuta mensagens em tempo real
- [Arquivo one_click_integrations.py](one_click_integrations.py) - OAuth, QR, bot token
- [Arquivo setup_evolution_api.sh](setup_evolution_api.sh) - Docker setup
- [Arquivo integrations-oneclick.html](frontend/integrations-oneclick.html) - Interface cliente

---

**Desenvolvido por**: Nexus CRM Team  
**Data**: Quinta, 15 de Janeiro, 2024  
**Status**: 🟢 Produção
