# 🎯 NEXUS CRM - STAGING ENVIRONMENT SETUP

## O que é Staging?

Staging é um ambiente que **espelha produção** e permite testar todas as mudanças antes de ir ao ar.

```
Development (Local)
        ↓
    ✅ Tests
        ↓
Staging (Production-like)
        ↓
    ✅ Final Testing
        ↓
Production (Live)
```

---

## 📋 SETUP DO STAGING

### 1. Crie uma Segunda Aplicação no Railway

```bash
# Opção A: Railway CLI
railway login
railway create
# Selecione: Python
# Conecte seu GitHub
# Selecione branch: staging (crie se não existir)

# Opção B: Dashboard
# 1. Vá para https://railway.app
# 2. New Project
# 3. Deploy from GitHub
# 4. Selecione repositório
# 5. Crie nova aplicação para staging
```

### 2. Configure Variáveis de Ambiente (Staging)

```bash
# Crie .env.staging
cp .env.example .env.staging

# Configure valores para staging
ENVIRONMENT=staging
DEBUG=false
DATABASE_URL=postgresql://staging_user:staging_pass@staging-db.railway.internal:5432/nexuscrm_staging
SENTRY_DSN=https://staging-key@sentry.io/staging-project
REDIS_URL=redis://staging-redis.railway.internal:6379/0
```

### 3. Configure GitHub Workflow para Deploy Automático em Staging

```yaml
# .github/workflows/deploy-staging.yml
name: Deploy Staging

on:
  push:
    branches: [ staging ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to Staging
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_STAGING_TOKEN }}
        run: |
          railway link ${{ secrets.RAILWAY_STAGING_PROJECT }}
          railway up --environment staging
```

### 4. Configure Monitoramento do Staging

```bash
# Sentry
SENTRY_ENVIRONMENT=staging

# UptimeRobot
# Crie monitor para: https://staging-api.nexuscrm.tech/health

# Slack (alertas)
SLACK_WEBHOOK_STAGING=https://hooks.slack.com/services/YOUR/STAGING/WEBHOOK
```

---

## 🧪 TESTANDO EM STAGING

### Testes Automatizados

```bash
# Executar testes
pytest tests/ -v --cov=vexus_crm

# Testes de performance
pytest tests/performance/ -v

# Testes de segurança
pytest tests/security/ -v
```

### Testes Manuais

```bash
# 1. Testar signup
curl -X POST https://staging-api.nexuscrm.tech/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@staging.com",
    "password": "TestPassword123!",
    "name": "Test User"
  }'

# 2. Testar login
curl -X POST https://staging-api.nexuscrm.tech/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@staging.com",
    "password": "TestPassword123!"
  }'

# 3. Testar endpoints
curl -X GET https://staging-api.nexuscrm.tech/api/contacts \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Testes de Carga em Staging

```bash
# Usando Apache Bench
ab -n 1000 -c 10 https://staging-api.nexuscrm.tech/health

# Usando wrk
wrk -t4 -c100 -d30s https://staging-api.nexuscrm.tech/health

# Usando k6
k6 run tests/load-test.js --vus 50 --duration 5m
```

---

## 📊 MONITORAMENTO DO STAGING

### Métricas a Acompanhar

```
Latência de API ........... < 200ms
Taxa de erro .............. < 0.5%
Taxa de cache hit ......... > 80%
Uso de memória ............ < 60%
Uso de CPU ................ < 70%
Conexões de banco ......... < 90%
Requisições/segundo ....... > 100
```

### Check-list Pré-Produção

```
API Tests:
  [ ] Health check responde
  [ ] API docs acessível (/api/docs)
  [ ] Todos os endpoints funcionando
  [ ] Rate limiting funcionando
  
Database:
  [ ] Conexão óK
  [ ] Queries rápidas (< 100ms)
  [ ] Índices verificados
  [ ] Backup recente
  
Security:
  [ ] HTTPS funciona
  [ ] Headers de segurança presentes
  [ ] CORS correto
  [ ] Autenticação funciona
  [ ] 2FA funciona (se habilitado)
  
Performance:
  [ ] Latência aceitável
  [ ] Cache funcionando
  [ ] Sem memory leaks
  [ ] Sem queries N+1
  
Monitoring:
  [ ] Sentry recebendo erros
  [ ] Logs centralizados
  [ ] Alertas configurados
  [ ] Uptime monitoring ativo
```

---

## 🚀 PROMOVER PARA PRODUÇÃO

### 1. QA Aprova Staging

```bash
# Criar nova tag
git tag -a v1.0.1 -m "Release v1.0.1 - Tested in Staging"
git push origin v1.0.1
```

### 2. Merge para Production Branch

```bash
# Merge de staging para main
git checkout main
git pull origin main
git merge staging
git push origin main
```

### 3. Railway Deploy Automático

```bash
# CI/CD automático disparado pelo merge em main
# GitHub Actions fará:
# 1. Rodar testes
# 2. Build Docker
# 3. Deploy para production
```

### 4. Verificar Produção

```bash
# Health check
curl https://api.nexuscrm.tech/health

# Status
curl https://api.nexuscrm.tech/status

# Smoke tests
pytest tests/smoke/ -v
```

---

## 📈 AMBIENTE STAGING IDEAL

```
┌─ Staging Environment ──────────────────────┐
│                                              │
│  Database: PostgreSQL (clonado de prod)      │
│  Cache: Redis (separado de prod)             │
│  API: FastAPI (mesma config que prod)        │
│  Monitoring: Sentry (projeto separado)       │
│  Logs: Mesma estratégia que prod             │
│  Backups: Diários (5 dias retenção)          │
│                                              │
│  Performance: 80-90% da produção             │
│  Dados: Cópia anonimizada de dados reais     │
│  Usuarios: Apenas para testes                │
│  Emails: Não enviados para usuários reais    │
│                                              │
└──────────────────────────────────────────────┘
```

---

## 🔄 GIT WORKFLOW COM STAGING

```
main (produção)
  ↑
  |
  ├── staging branch
  |     ↑
  |     |
  |     ├── feature-branch-1
  |     |
  |     └── feature-branch-2
  |

Fluxo:
1. feature-branch → Pull Request para staging
2. Tests rodam automaticamente
3. QA testa em staging
4. Merge em staging (auto-deploy)
5. Após aprovação final: merge em main (auto-deploy produção)
```

---

## ⚙️ CONFIGURAR GITHUB PROTECTION RULES

```
Para branch: main
  [ ] Require pull request before merging
  [ ] Require status checks to pass
  [ ] Require branches to be up to date
  [ ] Require a review from owner
  [ ] Require conversation resolution
  
Para branch: staging
  [ ] Require pull request before merging
  [ ] Require status checks to pass
  [ ] Dismiss stale reviews
```

---

## 📝 CHECKLIST FINAL (Antes de Produção)

### Semana 1 de Staging

- [ ] Deploy inicial em staging
- [ ] Testes básicos passando
- [ ] Monitoring configurado
- [ ] Logs funcionando

### Semana 2 de Staging

- [ ] 100% testes passando
- [ ] Load testing completo
- [ ] Security audit feito
- [ ] Performance otimizada

### Antes de Produção

- [ ] Zero erros em staging 48h
- [ ] Backup testado
- [ ] Disaster recovery testado
- [ ] Runbook preparado
- [ ] On-call schedule configurado
- [ ] Comunicação planejada

---

## 🎯 RESUMO

| Etapa | Ação | Tempo |
|-------|------|-------|
| Setup Staging | Criar app + DB + config | 30 min |
| Testes Iniciais | Testes automatizados | 15 min |
| QA Manual | Testes funcionais | 2-4 horas |
| Otimização | Performance tuning | 1-2 dias |
| Security | Testes segurança | 4 horas |
| Produção | Merge e deploy | 10 min |

**Tempo Total Recomendado: 1-2 semanas por release**

