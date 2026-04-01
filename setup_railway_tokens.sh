#!/bin/bash
#
# 🚀 SCRIPT DE CONFIGURAÇÃO DOS TOKENS NO RAILWAY
# Adiciona todas as variáveis de ambiente necessárias
#
# USAR: bash setup_railway_tokens.sh
#

set -e

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    🚀 SETUP DOS TOKENS NO RAILWAY                           ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verificar se Railway CLI está instalado
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI não está instalado${NC}"
    echo "Instale com: npm install -g @railway/cli"
    exit 1
fi

echo -e "${BLUE}✓ Railway CLI encontrado${NC}"
echo ""

# Verificar status de autenticação
echo -e "${YELLOW}🔐 Verificando autenticação no Railway...${NC}"
if ! railway whoami > /dev/null 2>&1; then
    echo -e "${YELLOW}Você precisa fazer login no Railway${NC}"
    echo "Execute: railway login"
    exit 1
fi

USER=$(railway whoami 2>/dev/null || echo "unknown")
echo -e "${GREEN}✓ Autenticado como: $USER${NC}"
echo ""

# List projects
echo -e "${YELLOW}📋 Projetos disponíveis no Railway:${NC}"
railway projects list 2>/dev/null || echo "Nenhum projeto encontrado"
echo ""

# Pedir informações
read -p "📝 Digite o ID ou nome do projeto (ou deixe em branco para usar ./railway.json): " PROJECT_ID

if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}Verificando ./railway.json...${NC}"
    if [ -f "./railway.json" ]; then
        echo -e "${GREEN}✓ railway.json encontrado${NC}"
    else
        echo -e "${RED}❌ railway.json não encontrado${NC}"
        exit 1
    fi
else
    echo -e "${BLUE}Usando projeto: $PROJECT_ID${NC}"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    ADICIONE OS TOKENS ABAIXO                                ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Função para perguntar por token
add_token() {
    local TOKEN_NAME=$1
    local TOKEN_DESC=$2
    local DEFAULT=${3:-}
    
    echo -e "${BLUE}---${NC}"
    echo -e "ℹ️  $TOKEN_DESC"
    
    if [ -z "$DEFAULT" ]; then
        read -p "$(echo -e ${YELLOW}Digite o valor para $TOKEN_NAME (ou deixe em branco para pular):${NC}) " TOKEN_VALUE
    else
        read -p "$(echo -e ${YELLOW}Digite o valor para $TOKEN_NAME [$DEFAULT]:${NC}) " TOKEN_VALUE
        TOKEN_VALUE=${TOKEN_VALUE:-$DEFAULT}
    fi
    
    if [ -n "$TOKEN_VALUE" ]; then
        echo -e "${YELLOW}Adicionando $TOKEN_NAME...${NC}"
        
        if [ -z "$PROJECT_ID" ]; then
            railway variables set $TOKEN_NAME="$TOKEN_VALUE" 2>/dev/null || echo -e "${RED}Erro ao adicionar $TOKEN_NAME${NC}"
        else
            railway variables set -p $PROJECT_ID $TOKEN_NAME="$TOKEN_VALUE" 2>/dev/null || echo -e "${RED}Erro ao adicionar $TOKEN_NAME${NC}"
        fi
        
        echo -e "${GREEN}✓ $TOKEN_NAME adicionado!${NC}"
        echo ""
    else
        echo -e "${YELLOW}⏭️  Pulando $TOKEN_NAME${NC}"
        echo ""
    fi
}

# Coletar tokens
echo -e "${BOLD}${BLUE}1. WHATSAPP CONFIGURATION${NC}"
add_token "WHATSAPP_ACCESS_TOKEN" "Token de acesso da API WhatsApp Business (Meta Developers)"
add_token "WHATSAPP_PHONE_ID" "ID do número de telefone WhatsApp (formato: +5511999999999 ou ID numérico)"
add_token "WHATSAPP_BUSINESS_ID" "ID da empresa WhatsApp (opcional)"

echo -e "${BOLD}${BLUE}2. TELEGRAM CONFIGURATION${NC}"
add_token "TELEGRAM_BOT_TOKEN" "Token do bot Telegram (@BotFather /newbot)"

echo -e "${BOLD}${BLUE}3. EMAIL CONFIGURATION (SendGrid)${NC}"
add_token "SENDGRID_API_KEY" "API Key do SendGrid (https://sendgrid.com/)"
add_token "EMAIL_FROM" "Email de envio (ex: noreply@seudominio.com)" "nexus@example.com"

echo -e "${BOLD}${BLUE}4. INSTAGRAM / FACEBOOK (Meta)${NC}"
add_token "META_BUSINESS_TOKEN" "Token da Meta Business Platform"
add_token "INSTAGRAM_BUSINESS_ID" "ID da conta Instagram (opcional)"
add_token "FACEBOOK_PAGE_ID" "ID da página Facebook (opcional)"

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                         ✅ CONFIGURAÇÃO CONCLUÍDA!                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}✓ Variáveis adicionadas ao Railway!${NC}"
echo ""
echo -e "${YELLOW}Próximos passos:${NC}"
echo "  1. Deploy automático será iniciado em alguns segundos"
echo "  2. Aguarde ~5-10 minutos para a aplicação reiniciar"
echo "  3. Teste os canais:"
echo ""
echo "     python3 test_crm_complete.py"
echo ""
echo -e "${BLUE}Ou teste um canal específico:${NC}"
echo ""
echo "     curl -X POST https://api.nexuscrm.tech/api/send-message \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"channel\":\"whatsapp\",\"destination\":\"5511999999999\",\"text\":\"Teste!\"}'"
echo ""
echo -e "${GREEN}Sistema pronto! Aproveite! 🎉${NC}"
