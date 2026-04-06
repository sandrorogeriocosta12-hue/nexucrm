# 🚀 NEXUS CRM - CONFIGURAÇÃO DE PRODUÇÃO

## 🌐 Domínio: api.nexuscrm.tech

Este guia explica como configurar e executar o Nexus CRM em produção no domínio `api.nexuscrm.tech`.

## 📋 Pré-requisitos

- ✅ PostgreSQL 16 instalado e configurado
- ✅ Python 3.8+ com ambiente virtual
- ✅ Certificado SSL (Cloudflare configurado)
- ✅ Domínio apontando para o servidor

## 🔧 Configuração

### 1. Arquivo .env (Produção)

O arquivo `.env` foi configurado para produção:

```env
# Servidor
API_BASE_URL=https://api.nexuscrm.tech
ENVIRONMENT=production
DEBUG=false
ALLOWED_HOSTS=nexuscrm.tech,www.nexuscrm.tech,api.nexuscrm.tech
CORS_ORIGINS=https://nexuscrm.tech,https://www.nexuscrm.tech,https://api.nexuscrm.tech

# Banco de dados
DATABASE_URL=postgresql://vexus:password@localhost/vexus_crm

# Webhooks e integrações
FACEBOOK_REDIRECT_URI=https://api.nexuscrm.tech/integrations/instagram/callback
TELEGRAM_WEBHOOK_URL=https://api.nexuscrm.tech/webhooks/telegram
EVOLUTION_API_URL=https://evolution.nexuscrm.tech
```

### 2. Testar Configuração

Execute o teste de configuração:

```bash
python3 test_production_config.py
```

## 🚀 Executar em Produção

### Opção 1: Script Automático (Recomendado)

```bash
./start_production.sh
```

### Opção 2: Manual

```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Iniciar com Gunicorn
gunicorn app_server:app \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --access-logfile - \
    --error-logfile - \
    --log-level info
```

## 🔒 Segurança

- ✅ CORS configurado apenas para domínios autorizados
- ✅ Debug desabilitado
- ✅ Ambiente de produção ativo
- ✅ SSL via Cloudflare
- ✅ Rate limiting configurado

## 🌐 URLs de Produção

- **API Principal**: https://api.nexuscrm.tech
- **Documentação**: https://api.nexuscrm.tech/docs
- **Health Check**: https://api.nexuscrm.tech/health
- **Frontend**: https://nexuscrm.tech (se configurado)

## 📊 Monitoramento

- Logs em tempo real no terminal
- Health check endpoint: `/health`
- Métricas disponíveis em: `/metrics`

## 🔄 Webhooks Configurados

- **Facebook/Instagram**: `https://api.nexuscrm.tech/integrations/instagram/callback`
- **Telegram**: `https://api.nexuscrm.tech/webhooks/telegram`
- **WhatsApp**: Via Evolution API em `https://evolution.nexuscrm.tech`

## 🐳 Docker (Opcional)

Para deploy com Docker:

```bash
docker build -t nexus-crm .
docker run -p 8000:8000 --env-file .env nexus-crm
```

## 📞 Suporte

Em caso de problemas:
1. Verificar logs do Gunicorn
2. Testar conectividade com `curl https://api.nexuscrm.tech/health`
3. Verificar configurações no Cloudflare

---
**🎉 Sistema pronto para produção no domínio api.nexuscrm.tech!**