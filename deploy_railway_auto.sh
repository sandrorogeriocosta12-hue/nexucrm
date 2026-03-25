#!/bin/bash

echo "🚀 DEPLOY AUTOMÁTICO NO RAILWAY"
echo "==============================="

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

set -e

# Verificar se está logado
echo -e "${BLUE}🔍 Verificando login...${NC}"
if ! railway whoami > /dev/null 2>&1; then
    echo -e "${RED}❌ Você não está logado no Railway${NC}"
    echo "Execute: railway login"
    exit 1
fi

echo -e "${GREEN}✅ Login confirmado${NC}"

# Criar projeto
echo ""
echo -e "${BLUE}🏗️  Criando projeto...${NC}"
railway create nexuscrm --team personal || echo "Projeto já existe"

# Conectar ao GitHub
echo ""
echo -e "${BLUE}🔗 Conectando ao GitHub...${NC}"
railway connect github

# Selecionar repositório
echo ""
echo -e "${BLUE}📦 Selecionando repositório...${NC}"
railway repo https://github.com/sandrorogeriocosta12-hue/nexucrm

# Adicionar PostgreSQL
echo ""
echo -e "${BLUE}🐘 Adicionando PostgreSQL...${NC}"
railway add postgres

# Adicionar Redis (opcional)
echo ""
echo -e "${BLUE}🔴 Adicionando Redis...${NC}"
railway add redis || echo "Redis opcional - pulando"

# Configurar variáveis de ambiente
echo ""
echo -e "${BLUE}⚙️  Configurando variáveis de ambiente...${NC}"

# Variáveis básicas
railway variables set ENVIRONMENT=production
railway variables set LOG_LEVEL=INFO
railway variables set DEBUG=False
railway variables set VERSION=1.0.0
railway variables set DATABASE_POOL_SIZE=20
railway variables set DATABASE_MAX_OVERFLOW=10
railway variables set REDIS_SSL=false
railway variables set OPENAI_MODEL=gpt-4
railway variables set OPENAI_TEMPERATURE=0.7

echo -e "${YELLOW}⚠️  ATENÇÃO: Você precisa configurar manualmente:${NC}"
echo "• OPENAI_API_KEY"
echo "• WHATSAPP_BUSINESS_API_KEY"
echo "• WHATSAPP_PHONE_NUMBER_ID"
echo "• WHATSAPP_WEBHOOK_TOKEN"
echo "• WHATSAPP_VERIFY_TOKEN"
echo ""
echo -e "${BLUE}Para configurar, acesse o dashboard do Railway e adicione as variáveis${NC}"

# Deploy
echo ""
echo -e "${BLUE}🚀 Fazendo deploy...${NC}"
railway deploy

# Obter URL
echo ""
echo -e "${GREEN}🎉 DEPLOY CONCLUÍDO!${NC}"
echo ""
echo -e "${BLUE}📊 STATUS:${NC}"
echo "• Projeto criado no Railway"
echo "• PostgreSQL configurado"
echo "• Redis configurado (opcional)"
echo "• Deploy iniciado"
echo ""
echo -e "${BLUE}🔗 URL da aplicação:${NC}"
railway domain || echo "URL será gerada em alguns minutos"

echo ""
echo -e "${YELLOW}📋 PRÓXIMOS PASSOS:${NC}"
echo "1. Configure as APIs (OpenAI e WhatsApp) no dashboard do Railway"
echo "2. Aguarde o deploy completar (5-10 minutos)"
echo "3. Teste a aplicação: URL/health"
echo "4. Verifique status: ./check_deploy_status.sh"

