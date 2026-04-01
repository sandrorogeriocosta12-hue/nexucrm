#!/bin/bash
#
# 📊 VERIFICAR STATUS DAS CONFIGURAÇÕES NO RAILWAY
# Mostra quais variáveis estão configuradas e quais estão faltando
#
# USAR: bash check_railway_config.sh
#

set -e

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║              📊 CHECK - STATUS DAS CONFIGURAÇÕES NO RAILWAY                 ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
GRAY='\033[0;90m'
NC='\033[0m'

# Verificar se Railway CLI está instalado
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI não está instalado${NC}"
    echo "Instale com: npm install -g @railway/cli"
    exit 1
fi

echo -e "${BLUE}✓ Railway CLI encontrado${NC}"
echo ""

# Verificar autenticação
if ! railway whoami > /dev/null 2>&1; then
    echo -e "${RED}❌ Você não está autenticado no Railway${NC}"
    echo "Execute: railway login"
    exit 1
fi

USER=$(railway whoami 2>/dev/null || echo "unknown")
echo -e "${GREEN}✓ Autenticado como: $USER${NC}"
echo ""

# Tentar obter variáveis
echo -e "${YELLOW}Obtendo variáveis do projeto...${NC}"
echo ""

# Função para checker uma variável
check_var() {
    local VAR_NAME=$1
    local VAR_DESC=$2
    
    VAR_VALUE=$(railway variables get $VAR_NAME 2>/dev/null || echo "")
    
    if [ -n "$VAR_VALUE" ]; then
        # Mostrar apenas alguns caracteres do valor
        VALUE_LENGTH=${#VAR_VALUE}
        if [ $VALUE_LENGTH -gt 20 ]; then
            DISPLAY_VALUE="${VAR_VALUE:0:10}...${VAR_VALUE: -5}"
        else
            DISPLAY_VALUE=$VAR_VALUE
        fi
        echo -e "${GREEN}✅${NC} $VAR_NAME"
        echo -e "   ${GRAY}Valor: $DISPLAY_VALUE (${VALUE_LENGTH} chars)${NC}"
    else
        echo -e "${RED}❌${NC} $VAR_NAME"
        echo -e "   ${GRAY}Status: Não configurado${NC}"
    fi
    echo ""
}

# Check WhatsApp
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  🟢 WHATSAPP${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
check_var "WHATSAPP_ACCESS_TOKEN" "Token de acesso WhatsApp"
check_var "WHATSAPP_PHONE_ID" "ID do número WhatsApp"
check_var "WHATSAPP_BUSINESS_ID" "ID da empresa WhatsApp (opcional)"

# Check Telegram
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  🤖 TELEGRAM${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
check_var "TELEGRAM_BOT_TOKEN" "Token do bot Telegram"

# Check Email
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  📧 EMAIL (SendGrid)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
check_var "SENDGRID_API_KEY" "API Key do SendGrid"
check_var "EMAIL_FROM" "Email de envio"

# Check Meta
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  📸 INSTAGRAM / 🔵 FACEBOOK (Meta)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
check_var "META_BUSINESS_TOKEN" "Token do Meta Business"
check_var "INSTAGRAM_BUSINESS_ID" "ID da conta Instagram (opcional)"
check_var "FACEBOOK_PAGE_ID" "ID da página Facebook (opcional)"

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                           📌 RESUMO                                         ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Contar variáveis configuradas
WHATSAPP_OK=0
TELEGRAM_OK=0
EMAIL_OK=0
META_OK=0

if [ -n "$(railway variables get WHATSAPP_ACCESS_TOKEN 2>/dev/null || echo "")" ]; then
    WHATSAPP_OK=1
fi
if [ -n "$(railway variables get TELEGRAM_BOT_TOKEN 2>/dev/null || echo "")" ]; then
    TELEGRAM_OK=1
fi
if [ -n "$(railway variables get SENDGRID_API_KEY 2>/dev/null || echo "")" ]; then
    EMAIL_OK=1
fi
if [ -n "$(railway variables get META_BUSINESS_TOKEN 2>/dev/null || echo "")" ]; then
    META_OK=1
fi

echo "Status dos Canais:"
echo ""
[ $WHATSAPP_OK -eq 1 ] && echo -e "  ${GREEN}✅ WhatsApp${NC}" || echo -e "  ${RED}❌ WhatsApp${NC}"
[ $TELEGRAM_OK -eq 1 ] && echo -e "  ${GREEN}✅ Telegram${NC}" || echo -e "  ${RED}❌ Telegram${NC}"
[ $EMAIL_OK -eq 1 ] && echo -e "  ${GREEN}✅ Email${NC}" || echo -e "  ${RED}❌ Email${NC}"
[ $META_OK -eq 1 ] && echo -e "  ${GREEN}✅ Instagram/Facebook${NC}" || echo -e "  ${RED}❌ Instagram/Facebook${NC}"

TOTAL=$((WHATSAPP_OK + TELEGRAM_OK + EMAIL_OK + META_OK))
echo ""
echo -e "Canais configurados: ${BLUE}${TOTAL}/4${NC}"
echo ""

if [ $TOTAL -eq 0 ]; then
    echo -e "${YELLOW}Próximo passo:${NC}"
    echo "  1. Leia: GUIA_OBTER_TOKENS.txt"
    echo "  2. Execute: bash setup_railway_tokens.sh"
    echo ""
elif [ $TOTAL -eq 4 ]; then
    echo -e "${GREEN}🎉 Todos os canais configurados!${NC}"
    echo ""
    echo -e "${YELLOW}Teste agora:${NC}"
    echo "  python3 test_crm_complete.py"
    echo ""
else
    echo -e "${YELLOW}${TOTAL}/4 canais configurados. Complete os restantes:${NC}"
    echo "  bash setup_railway_tokens.sh"
    echo ""
fi

echo -e "${BLUE}Para mais informações:${NC}"
echo "  https://api.nexuscrm.tech/integrations/status"
echo ""
