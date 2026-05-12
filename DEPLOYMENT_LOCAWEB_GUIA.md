# 🚀 GUIA DE DEPLOYMENT - LOCAWEB

## Status Atual ✅

- **Servidor Local**: ✅ Funcionando em http://localhost:8080
- **Webhooks**: ✅ WhatsApp e Instagram operacionais
- **Redis Cache**: ✅ Ativo
- **GitHub**: ✅ Código sincronizado (branch: deploy-production)

---

## 📋 Arquivos de Deployment

### 1. **docker-compose.yml** (Produção)
```bash
docker-compose up -d --build
```
Inicia todos os serviços:
- PostgreSQL (5432)
- Redis (6379)
- FastAPI (8080)

### 2. **deploy_locaweb_auto.sh** (Automático)
```bash
chmod +x deploy_locaweb_auto.sh
./deploy_locaweb_auto.sh
```
Executa:
- Pull do GitHub
- Build dos containers
- Restart dos serviços
- Verificação de saúde

### 3. **Procfile** (Heroku/Locaweb)
```
web: python -m uvicorn app_server:app --host 0.0.0.0 --port ${PORT:-8080}
```

---

## 🔧 Configuração Locaweb

### Pré-requisitos
- [ ] SSH configurado com chave Ed25519
- [ ] Servidor Locaweb: `177.53.142.144`
- [ ] Usuário: `victor-emanuel`
- [ ] Diretório: `/home/victor-emanuel/nexuscrm.tech`
- [ ] Docker e Docker Compose instalados

### Variáveis de Ambiente (`.env` no servidor)
```bash
# Database
DATABASE_URL=postgresql://vexus:password@localhost/vexus_db
REDIS_URL=redis://localhost:6379/0

# API Keys
EVOLUTION_API_URL=https://evolution.nexuscrm.tech
EVOLUTION_API_KEY=your_key_here
TELEGRAM_BOT_TOKEN=your_token_here
FACEBOOK_APP_ID=your_app_id
SENDGRID_API_KEY=your_sendgrid_key

# Server
API_BASE_URL=https://api.nexuscrm.tech
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=https://nexuscrm.tech,https://api.nexuscrm.tech
```

---

## 🚀 Como Fazer Deploy

### Opção 1: Automático (Recomendado)
```bash
cd /home/victor-emanuel/PycharmProjects/Vexus\ Service
chmod +x deploy_locaweb_auto.sh
./deploy_locaweb_auto.sh
```

### Opção 2: Manual SSH
```bash
ssh -i ~/.ssh/id_ed25519 victor-emanuel@177.53.142.144 << 'EOF'
cd /home/victor-emanuel/nexuscrm.tech
git pull origin deploy-production
docker-compose down
docker-compose up -d --build
EOF
```

### Opção 3: CI/CD (GitHub Actions)
Criar arquivo `.github/workflows/deploy.yml` para automação

---

## 📊 Monitoramento Pós-Deploy

### Verificar Logs
```bash
ssh -i ~/.ssh/id_ed25519 victor-emanuel@177.53.142.144
docker-compose logs -f vexus-backend
```

### Testar Endpoints
```bash
# Health Check
curl https://api.nexuscrm.tech/docs

# WhatsApp Webhook
curl -X POST https://api.nexuscrm.tech/webhooks/whatsapp/test \
  -H 'Content-Type: application/json' \
  -d '{"event":"messages.upsert","data":{...}}'
```

### Escalar Automaticamente
Se usar Kubernetes:
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

---

## ⚠️ Troubleshooting

### Servidor não responde
```bash
ssh -i ~/.ssh/id_ed25519 victor-emanuel@177.53.142.144
docker ps -a
docker logs vexus-backend
```

### Database connection error
```bash
docker exec vexus-postgres pg_isready -U vexus
```

### Redis indisponível
```bash
docker exec vexus-redis redis-cli ping
```

### Limpar tudo e recomeçar
```bash
docker-compose down -v
docker-compose up -d --build
```

---

## 📈 Performance

### Monitoramento
- **Logs**: `docker-compose logs -f`
- **CPU/Memória**: `docker stats`
- **Portas**: `lsof -i :8080`

### Otimizações
- [ ] Ativar compressão gzip
- [ ] Configurar cache headers
- [ ] Usar CDN para assets estáticos
- [ ] Aumentar worker processes

---

## 🔐 Segurança

- [ ] Certificado SSL/TLS renovado
- [ ] CORS configurado corretamente
- [ ] Secrets não commitados no Git
- [ ] Senhas de BD alteradas
- [ ] Firewall restrito a portas necessárias

---

## ✅ Checklist Pré-Deploy

- [ ] Testes locais passando
- [ ] Webhooks testados
- [ ] `.env` atualizado no servidor
- [ ] Backup do banco de dados feito
- [ ] Certificados SSL válidos
- [ ] Monitoramento configurado

---

## 📞 Suporte

Para logs detalhados:
```bash
tail -f /home/victor-emanuel/nexuscrm.tech/backend.log
tail -f /home/victor-emanuel/nexuscrm.tech/server.log
```

**Última atualização**: 2026-05-12
**Status**: ✅ Pronto para Produção
