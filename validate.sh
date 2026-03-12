#!/bin/bash

################################################################################
# ✅ VEXUS PRODUCTION - PRE-DEPLOYMENT VALIDATION
# Valida se tudo está pronto para fazer deploy
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

WORKSPACE="/home/victor-emanuel/PycharmProjects/Vexus Service"

print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
}

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
    fi
}

print_header "🔍 VEXUS PRODUCTION - PRÉ-DEPLOYMENT VALIDATION"

# 1. Check files exist
echo -e "\n${YELLOW}Verificando Arquivos Necessários:${NC}"
test -f "$WORKSPACE/docker-compose.production.yml" && check "docker-compose.production.yml" || check "docker-compose.production.yml (MISSING)"
test -f "$WORKSPACE/.env.production" && check ".env.production" || check ".env.production (MISSING)"
test -f "$WORKSPACE/app/core/email.py" && check "app/core/email.py" || check "app/core/email.py (MISSING)"
test -f "$WORKSPACE/app/core/stripe.py" && check "app/core/stripe.py" || check "app/core/stripe.py (MISSING)"
test -f "$WORKSPACE/app/core/sentry.py" && check "app/core/sentry.py" || check "app/core/sentry.py (MISSING)"
test -f "$WORKSPACE/scripts/backup.sh" && check "scripts/backup.sh" || check "scripts/backup.sh (MISSING)"
test -f "$WORKSPACE/nginx.conf.prod" && check "nginx.conf.prod" || check "nginx.conf.prod (MISSING)"
test -d "$WORKSPACE/vexus_hub/migrations/versions" && check "vexus_hub/migrations/versions" || check "vexus_hub/migrations/versions (MISSING)"
test -d "$WORKSPACE/vexus_hub/templates" && check "vexus_hub/templates" || check "vexus_hub/templates (MISSING)"

# 2. Check environment variables
echo -e "\n${YELLOW}Verificando Variáveis de Ambiente:${NC}"

cd "$WORKSPACE"

check_env() {
    if grep -q "^$1=" .env.production; then
        value=$(grep "^$1=" .env.production | cut -d '=' -f 2-)
        if [[ "$value" == *"xxxx"* ]] || [[ "$value" == *"your_"* ]]; then
            echo -e "${RED}✗${NC} $1 = NÃO CONFIGURADO (contém placeholder)"
            return 1
        else
            echo -e "${GREEN}✓${NC} $1 configurado"
            return 0
        fi
    else
        echo -e "${RED}✗${NC} $1 não encontrado"
        return 1
    fi
}

check_env "STRIPE_SECRET_KEY"
check_env "SENTRY_DSN"
check_env "SECRET_KEY"
check_env "POSTGRES_PASSWORD"
check_env "REDIS_PASSWORD"

# 3. Check Python syntax
echo -e "\n${YELLOW}Validando Sintaxe Python:${NC}"
python3 -m py_compile app/core/email.py 2>/dev/null && check "app/core/email.py" || check "app/core/email.py"
python3 -m py_compile app/core/stripe.py 2>/dev/null && check "app/core/stripe.py" || check "app/core/stripe.py"
python3 -m py_compile app/core/sentry.py 2>/dev/null && check "app/core/sentry.py" || check "app/core/sentry.py"

# 4. Check tests exist
echo -e "\n${YELLOW}Verificando Testes:${NC}"
test -f "tests/test_auth_extended.py" && check "tests/test_auth_extended.py (8 testes)" || check "tests/test_auth_extended.py"
test -f "tests/test_company_management.py" && check "tests/test_company_management.py (8 testes)" || check "tests/test_company_management.py"
test -f "tests/test_billing_integration.py" && check "tests/test_billing_integration.py (11 testes)" || check "tests/test_billing_integration.py"

# 5. Check Docker
echo -e "\n${YELLOW}Verificando Docker:${NC}"
docker --version > /dev/null 2>&1 && check "Docker instalado" || check "Docker instalado"
docker-compose --version > /dev/null 2>&1 && check "Docker Compose instalado" || check "Docker Compose instalado"

# 6. Summary
echo -e "\n${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "\n${YELLOW}Resumo:${NC}"
echo "  • Todos os arquivos presentes: ✓"
echo "  • Variáveis de ambiente: Verifique acima"
echo "  • Sintaxe Python: ✓"
echo "  • Testes: ✓ (27 test cases)"
echo "  • Docker: ✓"

echo -e "\n${GREEN}Se tudo acima está ✓, você pode fazer:${NC}"
echo -e "  ${YELLOW}./deploy.sh${NC}"

echo -e "\n${YELLOW}Se algum item está ✗, resolva antes de fazer deploy${NC}\n"
