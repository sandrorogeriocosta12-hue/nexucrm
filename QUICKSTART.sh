#!/bin/bash
# QUICKSTART - Vexus Dashboard v2.0
# Execute este script para começar rapidamente

echo "🚀 VEXUS DASHBOARD v2.0 - QUICK START"
echo "======================================"
echo ""

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar Node.js
echo -e "${BLUE}📋 Verificando requisitos...${NC}"
if ! command -v node &> /dev/null; then
    echo "❌ Node.js não encontrado. Instale em: https://nodejs.org"
    exit 1
fi
echo -e "${GREEN}✅ Node.js instalado: $(node --version)${NC}"

# Verificar npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm não encontrado"
    exit 1
fi
echo -e "${GREEN}✅ npm instalado: $(npm --version)${NC}"

echo ""
echo -e "${BLUE}📦 Instalando dependências...${NC}"

# Verificar se package.json existe
if [ ! -f "frontend/package.json" ]; then
    echo "❌ frontend/package.json não encontrado"
    exit 1
fi

cd frontend
npm install

echo -e "${GREEN}✅ Dependências instaladas${NC}"

echo ""
echo -e "${BLUE}🧪 Executando testes...${NC}"

# Rodar testes
npm test -- VexusDashboard.test.jsx --run

echo ""
echo -e "${BLUE}🎨 Building para produção...${NC}"

# Build
npm run build

echo ""
echo -e "${GREEN}✅ Vexus Dashboard v2.0 está pronto!${NC}"
echo ""
echo -e "${YELLOW}📚 Documentação:${NC}"
echo "  - DASHBOARD_IMPROVEMENTS.md       → Features implementadas"
echo "  - DASHBOARD_USER_GUIDE.md         → Guia do usuário"
echo "  - DASHBOARD_IMPLEMENTATION.md     → Detalhes técnicos"
echo ""
echo -e "${YELLOW}🚀 Para iniciar:${NC}"
echo "  npm run dev              → Desenvolvimento (hot reload)"
echo "  npm run build            → Build produção"
echo "  npm test                 → Executar testes"
echo ""
echo -e "${YELLOW}🔧 Backend (FastAPI):${NC}"
echo "  python main.py           → Inicia servidor (localhost:8000)"
echo "  Knowledge Lab funcionando em: http://localhost:8000/api/knowledge-lab/health"
echo ""
echo -e "${YELLOW}🌐 Acessar:${NC}"
echo "  http://localhost:5173   → Frontend"
echo "  http://localhost:8000   → Backend API"
echo ""
echo "======================================"
echo -e "${GREEN}✨ Pronto para criar CRM incrível!${NC}"
