#!/bin/bash

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           🖥️  TESTADOR DE TELAS VEXUS CRM 🖥️              ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 não encontrado!${NC}"
    exit 1
fi

echo -e "${YELLOW}✓ Iniciando servidor local...${NC}"
echo ""

# Ir para diretório
cd "$(dirname "$0")" || exit

echo -e "${GREEN}📁 Diretório: $(pwd)${NC}"
echo ""

# Exibir telas disponíveis
echo -e "${YELLOW}📍 Telas Disponíveis:${NC}"
echo "  1. Landing Page:      http://localhost:8080/vexus_core/templates/index.html"
echo "  2. Admin Dashboard:   http://localhost:8080/vexus_core/templates/admin.html"
echo "  3. Sales Dashboard:   http://localhost:8080/vexus_hub/app/templates/dashboard.html"
echo "  4. User Dashboard:    http://localhost:8080/vexus_hub/templates/marketing/dashboard.html"
echo "  5. Full CRM (⭐️):     http://localhost:8080/frontend/vexus-crm-full.html"
echo ""

echo -e "${GREEN}🚀 Servidor iniciado na porta 8080...${NC}"
echo -e "${YELLOW}⏸️  Pressione CTRL+C para parar${NC}"
echo ""

# Iniciar servidor
python3 -m http.server 8080

