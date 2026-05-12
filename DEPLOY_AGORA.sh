#!/bin/bash
# 🚀 COMMAND RÁPIDO PARA DEPLOY EM LOCAWEB
# Execute: bash DEPLOY_AGORA.sh

set -e

echo "════════════════════════════════════════════════════════════════"
echo "🚀 DEPLOY RÁPIDO PARA LOCAWEB - NEXUS CRM"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Variáveis
SERVER="177.53.142.144"
USER="victor-emanuel"
KEY="$HOME/.ssh/id_ed25519"
REMOTE_PATH="/home/victor-emanuel/nexuscrm.tech"

echo "📍 Servidor: $SERVER"
echo "👤 Usuário: $USER"
echo "📁 Diretório: $REMOTE_PATH"
echo ""

# Verificar SSH
if [ ! -f "$KEY" ]; then
    echo "❌ ERRO: Chave SSH não encontrada em $KEY"
    exit 1
fi
echo "✅ Chave SSH encontrada"

# Conectar e fazer deploy
echo ""
echo "🔗 Conectando ao servidor Locaweb..."
echo ""

ssh -i "$KEY" "$USER@$SERVER" << 'EOF'
echo "📥 Atualizando código..."
cd /home/victor-emanuel/nexuscrm.tech
git fetch origin
git reset --hard origin/deploy-production

echo "🛑 Parando containers..."
docker-compose down 2>/dev/null || true

echo "🔨 Building e iniciando..."
docker-compose up -d --build

echo ""
echo "⏳ Aguardando serviços..."
sleep 5

echo "✅ Deploy completo!"
echo ""
echo "📊 Status dos containers:"
docker-compose ps

echo ""
echo "📋 Últimos logs:"
docker-compose logs --tail=5 vexus-backend
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "✅ DEPLOY CONCLUÍDO COM SUCESSO!"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "🌐 Acessar:"
    echo "   API:       https://api.nexuscrm.tech"
    echo "   Dashboard: https://nexuscrm.tech"
    echo "   Swagger:   https://api.nexuscrm.tech/docs"
    echo ""
    echo "📊 Monitorar:"
    echo "   ssh -i ~/.ssh/id_ed25519 $USER@$SERVER"
    echo "   docker-compose logs -f vexus-backend"
    echo ""
else
    echo ""
    echo "❌ ERRO DURANTE DEPLOY!"
    exit 1
fi
