#!/bin/bash
#
# Inicia o complete sistema Vexus com backend e frontend
# Backend (FastAPI): porta 8080
# Frontend (HTML/JS): porta 8081
#

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Cores para output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🚀 Iniciando Sistema Vexus CRM${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Verificar se a venv existe
if [ ! -d "vexus_core/venv" ]; then
    echo -e "${YELLOW}⚠️  Venv não encontrada. Criando...${NC}"
    python3 -m venv vexus_core/venv
    source vexus_core/venv/bin/activate
    pip install --upgrade pip setuptools wheel
    pip install -r requirements-dev.txt
else
    source vexus_core/venv/bin/activate
fi

# Instalar pydantic-settings se necessário
pip install pydantic-settings --quiet 2>/dev/null || true

echo -e "${GREEN}✅ Ambiente Python configurado${NC}"

# Matar processos anteriores nas portas
echo -e "${YELLOW}🛑 Limpando processos anteriores...${NC}"
lsof -ti:8080 | xargs kill -9 2>/dev/null || true
lsof -ti:8081 | xargs kill -9 2>/dev/null || true
sleep 1

# Iniciar FastAPI backend em background
echo -e "${YELLOW}▶️  Iniciando backend FastAPI na porta 8080...${NC}"
cd "$PROJECT_ROOT"
./vexus_core/venv/bin/uvicorn app.api:app --host 0.0.0.0 --port 8080 > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend iniciado (PID: $BACKEND_PID)${NC}"

# Aguardar backend ficar pronto
echo -e "${YELLOW}⏳ Aberto backend estabeleça...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend respondendo${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}⚠️  Backend ainda não está respondendo, mas continuando...${NC}"
    fi
    sleep 1
done

# Iniciar servidor HTTP para telas estáticas na porta 8081
echo -e "${YELLOW}▶️  Iniciando frontend HTTP na porta 8081...${NC}"
cd "$PROJECT_ROOT/vexus_core"
./venv/bin/python -m http.server 8081 --directory templates > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✅ Frontend inicado (PID: $FRONTEND_PID)${NC}"

# Aguardar frontend
sleep 2

# Exibir resumo
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✨ Sistema Vexus iniciado com sucesso!${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "${BLUE}📋 Endpoints disponiveis:${NC}"
echo -e "  🌐 Frontend (Dashboard):    ${YELLOW}http://localhost:8081/index.html${NC}"
echo -e "  🔌 Backend API:              ${YELLOW}http://localhost:8080${NC}"
echo -e "  📊 Docs API (Swagger):       ${YELLOW}http://localhost:8080/docs${NC}"
echo -e "  🏥 Health Check:             ${YELLOW}http://localhost:8080/health${NC}"

echo -e "\n${BLUE}📝 Testes rápidos:${NC}"
echo -e "  Criar conta: ${YELLOW}curl -X POST http://localhost:8080/auth/signup -H 'Content-Type: application/json' -d '{\"email\": \"test@vexus.com\", \"password\": \"teste123\", \"name\": \"Test\"}'${NC}"
echo -e "  Fazer login:  ${YELLOW}curl -X POST http://localhost:8080/auth/login -H 'Content-Type: application/json' -d '{\"email\": \"admin@vexus.com\", \"password\": \"admin123\"}'${NC}"

echo -e "\n${BLUE}🛑 Para parar:${NC}"
echo -e "  Pressione CTRL+C ou execute: kill $BACKEND_PID $FRONTEND_PID"

# Salvar PIDs em arquivo
mkdir -p logs
echo "$BACKEND_PID" > logs/pids.backend
echo "$FRONTEND_PID" > logs/pids.frontend

# Aguardar sinais de término
trap "echo -e '\n${YELLOW}Parando sistema...${NC}'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM

wait
