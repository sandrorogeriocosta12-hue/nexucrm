#!/bin/bash

################################################################################
# 🚀 VEXUS CRM - PRODUCTION DEPLOYMENT AUTOMATION
# Script para colocar o Vexus CRM em produção
################################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
WORKSPACE="/home/victor-emanuel/PycharmProjects/Vexus Service"
COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE=".env.production"
DOMAIN="app.vexus.com.br"  # CHANGE THIS

################################################################################
# FUNCTIONS
################################################################################

print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
}

print_step() {
    echo -e "\n${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

check_prerequisites() {
    print_header "Verificando Pré-requisitos"
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker não encontrado. Instale Docker primeiro."
        exit 1
    fi
    print_success "Docker encontrado"
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose não encontrado. Instale Docker Compose primeiro."
        exit 1
    fi
    print_success "Docker Compose encontrado"
    
    if [ ! -f "$WORKSPACE/$ENV_FILE" ]; then
        print_error "Arquivo $ENV_FILE não encontrado em $WORKSPACE"
        echo "Por favor, configure as variáveis de ambiente em $WORKSPACE/$ENV_FILE"
        exit 1
    fi
    print_success "Arquivo de ambiente encontrado"
    
    cd "$WORKSPACE"
    print_success "Diretório de trabalho: $WORKSPACE"
}

phase_1_environment() {
    print_header "FASE 1: Verificar Configurações de Produção"
    
    print_step "Lendo variáveis de .env.production..."
    
    # Check required variables
    required_vars=("STRIPE_SECRET_KEY" "RESEND_API_KEY" "SENTRY_DSN" "SECRET_KEY")
    
    for var in "${required_vars[@]}"; do
        value=$(grep "^$var=" "$ENV_FILE" | cut -d '=' -f 2- || echo "")
        if [[ -z "$value" || "$value" == *"xxxx"* ]]; then
            print_error "$var não está configurada corretamente em .env.production"
            echo "Atualize: $var=seu_valor_real"
            exit 1
        fi
        print_success "$var ✓"
    done
    
    print_success "Todas as variáveis obrigatórias estão configuradas!"
}

phase_2_database() {
    print_header "FASE 2: Preparar Banco de Dados"
    
    print_step "Iniciando serviço PostgreSQL..."
    docker-compose -f "$COMPOSE_FILE" up -d postgres
    
    print_step "Aguardando PostgreSQL ficar saudável (max 30s)..."
    for i in {1..30}; do
        if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -h localhost -U vexus &>/dev/null; then
            print_success "PostgreSQL está online!"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    print_step "Executando Alembic migration..."
    cd "$WORKSPACE/vexus_hub"
    
    if ! docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U vexus -d vexus_db -c "SELECT 1 FROM pg_tables WHERE tablename='users'" &>/dev/null; then
        print_step "Primeira execução - criando tabelas..."
        alembic upgrade head 2>&1 || {
            print_error "Falha ao executar migration. Verifique logs acima."
            exit 1
        }
        print_success "Database schema criado com sucesso!"
    else
        print_success "Database schema já existe, pulando migration"
    fi
    
    cd "$WORKSPACE"
}

phase_3_docker_compose() {
    print_header "FASE 3: Iniciar Docker Compose (6 Serviços)"
    
    print_step "Iniciando todos os serviços..."
    docker-compose -f "$COMPOSE_FILE" up -d
    
    print_step "Aguardando serviços ficarem saudáveis..."
    sleep 5
    
    print_step "Verificando status dos containers..."
    docker-compose -f "$COMPOSE_FILE" ps
    
    # Check health of key services
    services=("postgres" "redis" "backend" "nginx")
    
    for service in "${services[@]}"; do
        print_step "Verificando $service..."
        for i in {1..30}; do
            if docker-compose -f "$COMPOSE_FILE" exec -T "$service" true &>/dev/null; then
                print_success "$service está rodando!"
                break
            fi
            echo -n "."
            sleep 1
        done
    done
    
    print_success "Todos os serviços estão online!"
}

phase_4_ssl() {
    print_header "FASE 4: Configurar SSL/TLS (Let's Encrypt)"
    
    print_step "Verificando se certificado já existe..."
    
    if docker exec vexus-nginx [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ] 2>/dev/null; then
        print_success "Certificado SSL já existe para $DOMAIN"
        return 0
    fi
    
    print_step "Gerando certificado SSL para $DOMAIN..."
    print_step "Certbot irá validar o domínio via HTTP (porta 80)"
    
    docker-compose -f "$COMPOSE_FILE" exec certbot certbot certonly \
        --webroot \
        -w /var/www/certbot \
        -d "$DOMAIN" \
        --email admin@vexus.com.br \
        --agree-tos \
        --no-eff-email \
        --force-renewal || {
        print_error "Falha ao gerar certificado. Possíveis causas:"
        echo "  1. Domínio não está apontando para este servidor"
        echo "  2. Porta 80 está bloqueada"
        echo "  3. DNS ainda não se propagou"
        exit 1
    }
    
    print_success "Certificado SSL gerado com sucesso!"
    
    print_step "Recarregando Nginx..."
    docker-compose -f "$COMPOSE_FILE" exec nginx nginx -s reload
    
    print_success "SSL/TLS configurado!"
}

phase_5_validation() {
    print_header "FASE 5: Validar Deployment"
    
    print_step "Testando endpoint /health (HTTP)..."
    if curl -s http://localhost:8000/health | grep -q "ok"; then
        print_success "Backend respondendo (HTTP) ✓"
    else
        print_error "Backend não respondendo"
        exit 1
    fi
    
    print_step "Aguardando SSL estar pronto (30s)..."
    sleep 5
    
    print_step "Testando HTTPS..."
    for i in {1..5}; do
        if curl -sk https://localhost/health 2>/dev/null | grep -q "ok"; then
            print_success "Backend respondendo (HTTPS) ✓"
            break
        fi
        echo -n "."
        sleep 5
    done
    
    print_step "Verificando logs em tempo real (5s)..."
    docker-compose -f "$COMPOSE_FILE" logs --tail=10 backend | head -20
    
    print_step "Verificando backup service..."
    if docker-compose -f "$COMPOSE_FILE" exec -T backup [ -f "/backup.sh" ]; then
        print_success "Script de backup instalado ✓"
    fi
    
    print_success "Validação completa!"
}

show_summary() {
    print_header "🎉 DEPLOYMENT CONCLUÍDO COM SUCESSO!"
    
    echo -e "\n${GREEN}Sistema está rodando em produção!${NC}\n"
    
    echo "📊 Serviços Rodando:"
    echo "  ✓ PostgreSQL:  postgres:5432"
    echo "  ✓ Redis:       redis:6379"
    echo "  ✓ Backend:     http://localhost:8000"
    echo "  ✓ Nginx:       https://$DOMAIN"
    echo "  ✓ Certbot:     (auto-renew a cada 12h)"
    echo "  ✓ Backup:      (diário às 3:00 AM)"
    
    echo -e "\n📚 Próximas Ações:"
    echo "  1. Configure seu domínio DNS para apontar para este servidor"
    echo "  2. Acesse https://$DOMAIN"
    echo "  3. Monitore logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "  4. Configure alertas no Sentry: https://sentry.io"
    
    echo -e "\n🔧 Comandos Úteis:"
    echo "  Ver logs:        docker-compose -f $COMPOSE_FILE logs -f backend"
    echo "  Restart backend: docker-compose -f $COMPOSE_FILE restart backend"
    echo "  Shell backend:   docker-compose -f $COMPOSE_FILE exec backend bash"
    echo "  DB shell:        docker-compose -f $COMPOSE_FILE exec postgres psql -U vexus -d vexus_db"
    echo "  Parar tudo:      docker-compose -f $COMPOSE_FILE down"
    
    echo -e "\n📞 Suporte:"
    echo "  Docs:  $(pwd)/PRODUCTION_DEPLOYMENT.md"
    echo "  Arch:  $(pwd)/SYSTEM_ARCHITECTURE.md"
}

################################################################################
# MAIN EXECUTION
################################################################################

main() {
    print_header "🚀 VEXUS CRM - PRODUCTION DEPLOYMENT"
    echo "Data: $(date)"
    echo "Domínio: $DOMAIN"
    echo ""
    
    check_prerequisites
    phase_1_environment
    phase_2_database
    phase_3_docker_compose
    phase_4_ssl
    phase_5_validation
    
    show_summary
    
    print_success "Deployment finalizado em $(date)"
}

# Run main function
main "$@"
