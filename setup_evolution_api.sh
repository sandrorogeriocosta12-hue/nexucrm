#!/bin/bash
# 🐳 EVOLUTION API - SETUP PARA WHATSAPP UM CLIQUE
# Instala Evolution API em Docker para gerar QR Codes

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🐳 SETUP: Evolution API + Docker                          ║"
echo "║  Para WhatsApp QR Code (Um Clique)                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# ═══════════════════════════════════════════════════════════════════════
# PASSO 1: Verificar Docker
# ═══════════════════════════════════════════════════════════════════════

echo "📦 Passo 1: Verificar Docker instalado..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado. Instale em: https://docker.com"
    exit 1
fi
echo "✅ Docker encontrado: $(docker --version)"
echo ""

# ═══════════════════════════════════════════════════════════════════════
# PASSO 2: Baixar imagem Evolution API
# ═══════════════════════════════════════════════════════════════════════

echo "⬇️  Passo 2: Baixar imagem Evolution API..."
if ! docker pull atendaiw/evolution-api:latest; then
    echo "❌ Falha ao baixar a imagem atendaiw/evolution-api:latest"
    echo "   Verifique acesso ao registry ou credenciais Docker."
    echo "   Se o repositório for privado, faça login com 'docker login'."
    exit 1
fi

echo "✅ Imagem baixada"
echo ""

# ═══════════════════════════════════════════════════════════════════════
# PASSO 3: Criar pasta de dados
# ═══════════════════════════════════════════════════════════════════════

echo "📁 Passo 3: Criar pasta de dados..."
mkdir -p ~/evolution-api/data
echo "✅ Pasta criada em ~/evolution-api/data"
echo ""

# ═══════════════════════════════════════════════════════════════════════
# PASSO 4: Criar arquivo .env para Evolution API
# ═══════════════════════════════════════════════════════════════════════

echo "⚙️  Passo 4: Criar arquivo .env..."

cat > ~/evolution-api/.env << 'EOF'
# 🔐 Evolution API Configuration

# Porta
SERVER_PORT=3000

# Database (SQLite é padrão)
DATABASE_TYPE=sqlite
DATABASE_PATH=/data/evolution.db

# API Key (mude para algo seguro!)
API_KEY=sua_chave_super_secreta_aqui_123

# JWT
JWT_SECRET=jwt_secret_super_seguro_123

# Rate limit
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX_REQUESTS=100
RATE_LIMIT_WINDOW_MS=60000

# Logs
LOG_LEVEL=debug

# Redis (opcional, para cache)
# REDIS_URL=redis://redis:6379

# Webhook baseado
WEBHOOK_BASE_URL=https://api.nexuscrm.tech

EOF

echo "✅ .env criado"
echo ""

# ═══════════════════════════════════════════════════════════════════════
# PASSO 5: Iniciar container
# ═══════════════════════════════════════════════════════════════════════

echo "🚀 Passo 5: Iniciando container..."

docker run -d \
  --name evolution-api \
  -p 3000:3000 \
  --env-file ~/evolution-api/.env \
  --volume ~/evolution-api/data:/data \
  --restart unless-stopped \
  atendaiw/evolution-api:latest

sleep 3

echo "✅ Container iniciado"
echo ""

# ═══════════════════════════════════════════════════════════════════════
# PASSO 6: Teste de conexão
# ═══════════════════════════════════════════════════════════════════════

echo "🔍 Passo 6: Testando conexão..."

RESPONSE=$(curl -s -X GET \
  http://localhost:3000 \
  -H "apikey: sua_chave_super_secreta_aqui_123")

if [[ $RESPONSE == *"success"* ]] || [[ $RESPONSE == *"welcome"* ]]; then
    echo "✅ Evolution API respondendo corretamente!"
else
    echo "⚠️  Aguardando Evolution API iniciar completely..."
    sleep 5
fi

echo ""

# ═══════════════════════════════════════════════════════════════════════
# RESUMO
# ═══════════════════════════════════════════════════════════════════════

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ✅ SETUP CONCLUÍDO                                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Evolution API URL: http://localhost:3000"
echo "🔑 API Key: sua_chave_super_secreta_aqui_123"
echo ""
echo "📚 Documentação: https://docs.evolution.bot"
echo ""
echo "🚀 PRÓXIMO PASSO:"
echo "   1. Adicionar Evolution API URL ao .env do Nexus CRM:"
echo "      EVOLUTION_API_URL=http://localhost:3000"
echo "      EVOLUTION_API_KEY=sua_chave_super_secreta_aqui_123"
echo ""
echo "   2. Restart Nexus CRM:"
echo "      git push origin main"
echo ""
echo "   3. Cliente vai para: Configurações > Integração > WhatsApp"
echo "   4. Clica 'Gerar QR Code'"
echo "   5. Escaneia com celular"
echo "   6. Pronto! ✅"
echo ""

# ═══════════════════════════════════════════════════════════════════════
# Comandos úteis
# ═══════════════════════════════════════════════════════════════════════

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  📝 COMANDOS ÚTEIS                                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Ver logs do Docker:"
echo "  $ docker logs -f evolution-api"
echo ""
echo "Parar container:"
echo "  $ docker stop evolution-api"
echo ""
echo "Iniciar container:"
echo "  $ docker start evolution-api"
echo ""
echo "Remover tudo:"
echo "  $ docker stop evolution-api && docker rm evolution-api"
echo ""
