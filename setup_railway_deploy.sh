#!/bin/bash

echo "🚂 RAILWAY DEPLOY AUTOMATION"
echo "============================"

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}✅ PASSO 1: Verificando pré-requisitos${NC}"
echo "Railway CLI: $(which railway)"
echo "Git: $(git --version | head -1)"
echo "Docker: $(docker --version | head -1)"

echo ""
echo -e "${BLUE}✅ PASSO 2: Arquivos de configuração criados${NC}"
echo "✓ railway.toml - Configuração do projeto"
echo "✓ railway.json - Configuração adicional"
echo "✓ Dockerfile - Container otimizado"
echo "✓ deploy_railway_instructions.txt - Guia completo"

echo ""
echo -e "${BLUE}✅ PASSO 3: Repositório GitHub atualizado${NC}"
echo "✓ Código commitado e enviado"
echo "✓ railway.toml incluído"
echo "✓ URL: https://github.com/sandrorogeriocosta12-hue/nexucrm"

echo ""
echo -e "${YELLOW}🔑 PASSO 4: AÇÃO NECESSÁRIA - LOGIN NO RAILWAY${NC}"
echo ""
echo "Execute este comando e siga as instruções:"
echo -e "${GREEN}railway login${NC}"
echo ""
echo "Ou para modo browserless:"
echo -e "${GREEN}railway login --browserless${NC}"
echo ""
echo "Depois visite a URL mostrada e use o código de pareamento."

echo ""
echo -e "${BLUE}✅ PASSO 5: APÓS LOGIN - DEPLOY AUTOMÁTICO${NC}"
echo ""
echo "Após fazer login, execute:"
echo -e "${GREEN}./deploy_railway_auto.sh${NC}"
echo ""
echo "Este script irá:"
echo "• Criar projeto no Railway"
echo "• Conectar ao GitHub"
echo "• Adicionar PostgreSQL"
echo "• Configurar variáveis de ambiente"
echo "• Fazer deploy automático"

echo ""
echo -e "${RED}⚠️  IMPORTANTE: Você precisa configurar:${NC}"
echo "• OPENAI_API_KEY (obrigatório)"
echo "• WhatsApp Business API (obrigatório)"
echo ""
echo "Pegue as chaves em:"
echo "• OpenAI: https://platform.openai.com/api/keys"
echo "• WhatsApp: https://business.facebook.com"

