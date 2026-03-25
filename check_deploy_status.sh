#!/bin/bash

echo "🔍 VERIFICANDO STATUS DO DEPLOY"
echo "================================="

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# URLs para verificar
RENDER_URL="https://nexuscrm.onrender.com"
RAILWAY_URL="https://nexucrm-production.up.railway.app"
LOCAL_URL="http://localhost:8000"

echo -e "${BLUE}📍 Testando URLs:${NC}"

# Teste Railway (PRINCIPAL)
echo -n "Railway: "
if curl -s --max-time 10 -o /dev/null -w "%{http_code}" "$RAILWAY_URL/health" | grep -q "200"; then
    echo -e "${GREEN}✅ ONLINE${NC}"
    echo "  URL: $RAILWAY_URL"
    echo "  Signup: $RAILWAY_URL/signup"
else
    echo -e "${RED}❌ OFFLINE${NC}"
    echo "  Configure deploy no Railway seguindo: deploy_railway_instructions.txt"
fi

# Teste Render (SECUNDÁRIO)
echo -n "Render: "
if curl -s --max-time 10 -o /dev/null -w "%{http_code}" "$RENDER_URL/health" | grep -q "200"; then
    echo -e "${GREEN}✅ ONLINE${NC}"
    echo "  URL: $RENDER_URL"
else
    echo -e "${YELLOW}⚠️  NÃO CONFIGURADO${NC}"
fi

# Teste Local
echo -n "Local: "
if curl -s --max-time 5 -o /dev/null -w "%{http_code}" "$LOCAL_URL/health" | grep -q "200"; then
    echo -e "${GREEN}✅ ONLINE${NC}"
    echo "  URL: $LOCAL_URL"
else
    echo -e "${RED}❌ OFFLINE${NC}"
fi

echo ""
echo -e "${BLUE}📋 PRÓXIMOS PASSOS:${NC}"
echo "1. Configure deploy no Railway seguindo: deploy_railway_instructions.txt"
echo "2. Adicione PostgreSQL e Redis no Railway"
echo "3. Configure as variáveis de ambiente (OpenAI e WhatsApp obrigatórias)"
echo "4. Teste novamente com: ./check_deploy_status.sh"
echo ""
echo -e "${BLUE}🔗 LINKS ÚTEIS:${NC}"
echo "• Railway: https://railway.app"
echo "• GitHub Repo: https://github.com/sandrorogeriocosta12-hue/nexucrm"
echo "• Instruções: cat deploy_railway_instructions.txt"

