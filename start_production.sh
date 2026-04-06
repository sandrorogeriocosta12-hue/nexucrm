#!/bin/bash
echo "🚀 INICIANDO NEXUS CRM - PRODUÇÃO 🚀"
echo "======================================"
echo "🌐 Domínio: https://api.nexuscrm.tech"
echo "🔒 SSL: Cloudflare"
echo "📊 Ambiente: Produção"
echo ""

# Verificar se estamos no ambiente virtual
if [ -z "$VIRTUAL_ENV" ]; then
    echo "🔧 Ativando ambiente virtual..."
    source .venv/bin/activate
fi

# Verificar PostgreSQL
echo "🗄️  Verificando PostgreSQL..."
if sudo systemctl is-active --quiet postgresql@16-main; then
    echo "✅ PostgreSQL está rodando"
else
    echo "❌ PostgreSQL não está rodando. Iniciando..."
    sudo systemctl start postgresql@16-main
fi

# Testar conexão com banco
echo "🔍 Testando conexão com banco de dados..."
python3 -c "
import os
from sqlalchemy import create_engine, text

try:
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://vexus:password@localhost/vexus_crm')
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('✅ Banco de dados conectado com sucesso!')
except Exception as e:
    print(f'❌ Erro na conexão com banco: {e}')
    exit(1)
"

echo ""
echo "🌟 Iniciando servidor FastAPI..."
echo "📍 URL: https://api.nexuscrm.tech"
echo "📊 Porta: 8000 (interna)"
echo "🔄 Workers: 4"
echo ""

# Iniciar com Gunicorn para produção
gunicorn app_server:app \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --timeout 120 \
    --keep-alive 10