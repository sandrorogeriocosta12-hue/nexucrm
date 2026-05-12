#!/bin/bash
# 🚀 Deploy Automático para Locaweb
# ════════════════════════════════════════════════════════════════

set -e

echo "🚀 INICIANDO DEPLOY PARA LOCAWEB"
echo "════════════════════════════════════════════════════════════════"
date

# Configurações
SERVER_IP="177.53.142.144"
SERVER_USER="victor-emanuel"
REMOTE_PATH="/home/victor-emanuel/nexuscrm.tech"
SSH_KEY="$HOME/.ssh/id_ed25519"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ════════════════════════════════════════════════════════════════
# 1. VALIDAR MUDANÇAS LOCAIS
# ════════════════════════════════════════════════════════════════

echo -e "${YELLOW}✓${NC} Validando estado local..."

if [ -z "$(git status --porcelain)" ]; then
    echo "  ✅ Não há mudanças pendentes"
else
    echo -e "  ${RED}❌ Há mudanças não commitadas!${NC}"
    git status
    exit 1
fi

# ════════════════════════════════════════════════════════════════
# 2. PULL DO REPOSITÓRIO REMOTO
# ════════════════════════════════════════════════════════════════

echo -e "\n${YELLOW}✓${NC} Atualizando repositório..."
git fetch origin
echo "  ✅ Repositório atualizado"

# ════════════════════════════════════════════════════════════════
# 3. FAZER DEPLOY VIA SSH
# ════════════════════════════════════════════════════════════════

echo -e "\n${YELLOW}✓${NC} Iniciando deploy no servidor Locaweb..."

ssh -i "${SSH_KEY}" "${SERVER_USER}@${SERVER_IP}" << 'EOFSERVER'
cd /home/victor-emanuel/nexuscrm.tech

# Atualizar código
echo "  📥 Pulling código do GitHub..."
git fetch origin
git reset --hard origin/deploy-production

# Verificar .env
if [ ! -f .env ]; then
    echo "  ⚠️ Arquivo .env não encontrado!"
    echo "  ℹ️ Copiar .env da configuração de produção"
    exit 1
fi

# Parar containers antigos
echo "  🛑 Parando containers..."
docker-compose down 2>/dev/null || true

# Build e start
echo "  🔨 Building images..."
docker-compose -f docker-compose.yml up -d --build

# Aguardar inicialização
echo "  ⏳ Aguardando serviços iniciarem..."
sleep 10

# Verificar saúde
echo "  🔍 Verificando saúde do sistema..."
if curl -f http://localhost:8080/docs > /dev/null 2>&1; then
    echo "  ✅ Servidor respondendo"
else
    echo "  ⚠️ Servidor pode não estar pronto ainda"
fi

# Logs
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ Deploy concluído com sucesso!"
echo "════════════════════════════════════════════════════════════════"
docker-compose logs --tail=10
EOFSERVER

RESULT=$?

if [ $RESULT -eq 0 ]; then
    echo -e "\n${GREEN}✅ DEPLOY CONCLUÍDO COM SUCESSO!${NC}"
    echo "════════════════════════════════════════════════════════════════"
    echo "📍 Servidor: https://api.nexuscrm.tech"
    echo "📍 Dashboard: https://nexuscrm.tech"
    echo ""
    echo "💡 Próximos passos:"
    echo "   1. Verificar logs: ssh -i ~/.ssh/id_ed25519 ${SERVER_USER}@${SERVER_IP} 'docker-compose logs -f'"
    echo "   2. Testar webhooks: curl http://localhost:8080/docs"
    echo ""
    exit 0
else
    echo -e "\n${RED}❌ ERRO DURANTE DEPLOY!${NC}"
    exit 1
fi
