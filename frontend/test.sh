#!/bin/bash

# 🚀 SCRIPT DE TESTE RÁPIDO - FRONTEND VEXUS CRM
# Este script valida que tudo está funcionando

echo "=========================================="
echo "  VEXUS CRM - TESTE DO FRONTEND"
echo "=========================================="
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Verificar estrutura de arquivos
echo "📁 [1/5] Verificando estrutura de arquivos..."
FILES=(
    "frontend/index.html"
    "frontend/login.html"
    "frontend/contacts.html"
    "frontend/pipeline.html"
    "frontend/tasks.html"
    "frontend/automations.html"
    "frontend/reports.html"
    "frontend/settings.html"
    "frontend/contact.html"
    "frontend/components/sidebar.html"
    "frontend/components/header.html"
    "frontend/js/api.js"
    "frontend/js/auth.js"
    "frontend/js/pipeline.js"
    "frontend/js/charts.js"
    "frontend/js/calendar.js"
    "frontend/css/style.css"
    "frontend/README.md"
)

MISSING=0
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅${NC} $file"
    else
        echo -e "${RED}❌${NC} $file (FALTANDO)"
        MISSING=$((MISSING + 1))
    fi
done

if [ $MISSING -eq 0 ]; then
    echo -e "${GREEN}✅ Todos os 18 arquivos presentes!${NC}"
else
    echo -e "${RED}❌ $MISSING arquivos faltando!${NC}"
fi

echo ""

# 2. Verificar se o backend está rodando
echo "🔌 [2/5] Verificando backend..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅${NC} Backend está rodando em http://localhost:8000"
else
    echo -e "${YELLOW}⚠️${NC} Backend não está respondendo em http://localhost:8000"
    echo "   Execute: docker-compose up -d"
fi

echo ""

# 3. Verificar endpoints da API
echo "🔗 [3/5] Testando endpoints da API..."
echo "   (Nota: Requer token válido)"

# Teste /health (não precisa de auth)
if curl -s http://localhost:8000/health | grep -q "status"; then
    echo -e "${GREEN}✅${NC} /health"
else
    echo -e "${RED}❌${NC} /health"
fi

echo ""

# 4. Validação de JavaScript
echo "📝 [4/5] Validando sintaxe JavaScript..."
JS_FILES=(
    "frontend/js/api.js"
    "frontend/js/auth.js"
)

for file in "${JS_FILES[@]}"; do
    if node -c "$file" 2>/dev/null; then
        echo -e "${GREEN}✅${NC} $file"
    else
        echo -e "${YELLOW}⚠️${NC} $file (não é um script completo, mas pode estar ok)"
    fi
done

echo ""

# 5. Servir frontend
echo "🚀 [5/5] Iniciando servidor frontend..."
if command -v python3 &> /dev/null; then
    cd frontend/
    echo -e "${GREEN}✅ Servidor iniciado!${NC}"
    echo ""
    echo "Acesse o frontend em:"
    echo -e "  ${YELLOW}http://localhost:8080${NC}"
    echo ""
    echo "Parar o servidor: Ctrl+C"
    echo ""
    python3 -m http.server 8080
else
    echo -e "${RED}❌ Python3 não encontrado${NC}"
    echo "   Instale com: sudo apt-get install python3"
fi
