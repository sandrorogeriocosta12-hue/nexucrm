#!/bin/bash
echo "🚀 DEPLOY NEXUS CRM - PRODUÇÃO 🚀"
echo "=================================="
echo "🌐 Domínio: api.nexuscrm.tech"
echo "🔒 SSL: Cloudflare"
echo "📊 Ambiente: Produção"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para log
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Verificar se estamos no diretório correto
if [ ! -f "app_server.py" ]; then
    error "Execute este script no diretório raiz do projeto!"
    exit 1
fi

# Ativar ambiente virtual
log "Ativando ambiente virtual..."
if [ -z "$VIRTUAL_ENV" ]; then
    source .venv/bin/activate
fi

# Verificar dependências
log "Verificando dependências..."
pip install -q gunicorn uvicorn[standard]

# Verificar PostgreSQL
log "Verificando PostgreSQL..."
if ! sudo systemctl is-active --quiet postgresql@16-main; then
    warning "PostgreSQL não está rodando. Iniciando..."
    sudo systemctl start postgresql@16-main
fi

# Testar configuração
log "Testando configuração..."
python3 test_production_config.py

if [ $? -ne 0 ]; then
    error "Falha na configuração! Verifique as variáveis de ambiente."
    exit 1
fi

# Configurar Nginx (opcional)
read -p "Deseja configurar Nginx automaticamente? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log "Configurando Nginx..."
    sudo cp nginx.production.conf /etc/nginx/sites-available/api.nexuscrm.tech
    sudo ln -sf /etc/nginx/sites-available/api.nexuscrm.tech /etc/nginx/sites-enabled/
    sudo nginx -t
    if [ $? -eq 0 ]; then
        sudo systemctl reload nginx
        log "Nginx configurado com sucesso!"
    else
        error "Erro na configuração do Nginx!"
    fi
fi

# Criar serviço systemd (opcional)
read -p "Deseja criar serviço systemd para auto-inicialização? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log "Criando serviço systemd..."

    cat > /tmp/nexus-crm.service << EOF
[Unit]
Description=Nexus CRM API
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=exec
User=victor-emanuel
WorkingDirectory=/home/victor-emanuel/PycharmProjects/Vexus Service
Environment=PATH=/home/victor-emanuel/PycharmProjects/Vexus Service/.venv/bin
ExecStart=/home/victor-emanuel/PycharmProjects/Vexus Service/.venv/bin/gunicorn app_server:app --bind 127.0.0.1:8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    sudo mv /tmp/nexus-crm.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable nexus-crm
    log "Serviço systemd criado!"
fi

echo ""
log "🎉 DEPLOY CONCLUÍDO!"
echo ""
echo "🌐 URLs de produção:"
echo "   📍 API: https://api.nexuscrm.tech"
echo "   📊 Docs: https://api.nexuscrm.tech/docs"
echo "   ❤️ Health: https://api.nexuscrm.tech/health"
echo ""
echo "🚀 Para iniciar manualmente:"
echo "   ./start_production.sh"
echo ""
echo "🔄 Para gerenciar serviço:"
echo "   sudo systemctl start nexus-crm"
echo "   sudo systemctl stop nexus-crm"
echo "   sudo systemctl restart nexus-crm"
echo "   sudo systemctl status nexus-crm"
echo ""
echo "📋 Ver logs:"
echo "   sudo journalctl -u nexus-crm -f"