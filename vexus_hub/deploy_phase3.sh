#!/bin/bash

# Vexus Hub Phase 3 Deployment Script
# This script deploys the complete marketing and analytics platform

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="vexus_hub"
DOCKER_COMPOSE_FILE="docker-compose-phase3.yml"
ENV_FILE=".env.production"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file $ENV_FILE not found. Please create it with required variables."
        exit 1
    fi

    log_success "Dependencies check passed"
}

setup_environment() {
    log_info "Setting up environment..."

    # Create necessary directories
    mkdir -p logs
    mkdir -p uploads
    mkdir -p ssl
    mkdir -p monitoring/prometheus
    mkdir -p monitoring/grafana/provisioning/datasources
    mkdir -p monitoring/grafana/provisioning/dashboards
    mkdir -p monitoring/grafana/dashboards
    mkdir -p ai_cache
    mkdir -p analytics_cache

    # Set proper permissions
    chmod 755 logs
    chmod 755 uploads
    chmod 700 ssl

    log_success "Environment setup completed"
}

generate_ssl_certificates() {
    log_info "Generating SSL certificates..."

    if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
        # Generate self-signed certificate for development
        openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes \
            -subj "/C=BR/ST=SP/L=Sao Paulo/O=Vexus Hub/CN=localhost"

        log_success "SSL certificates generated"
    else
        log_info "SSL certificates already exist"
    fi
}

create_monitoring_config() {
    log_info "Creating monitoring configuration..."

    # Prometheus configuration
    cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'vexus_web'
    static_configs:
      - targets: ['web:5000', 'web:5001', 'web:5002']
    scrape_interval: 5s

  - job_name: 'vexus_ai'
    static_configs:
      - targets: ['ai_processor:8000', 'ai_processor:8001']
    scrape_interval: 10s

  - job_name: 'vexus_analytics'
    static_configs:
      - targets: ['analytics_engine:9000']
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'postgres'
    static_configs:
      - targets: ['db:5432']
EOF

    # Grafana datasource configuration
    cat > monitoring/grafana/provisioning/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    # Grafana dashboard configuration
    cat > monitoring/grafana/provisioning/dashboards/dashboard.yml << EOF
apiVersion: 1

providers:
  - name: 'Vexus Hub'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF

    log_success "Monitoring configuration created"
}

build_and_deploy() {
    log_info "Building and deploying services..."

    # Use docker-compose or docker compose based on availability
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi

    # Pull latest images
    log_info "Pulling latest images..."
    $COMPOSE_CMD -f $DOCKER_COMPOSE_FILE pull

    # Build custom images
    log_info "Building custom images..."
    $COMPOSE_CMD -f $DOCKER_COMPOSE_FILE build --parallel

    # Start services
    log_info "Starting services..."
    $COMPOSE_CMD -f $DOCKER_COMPOSE_FILE up -d

    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 30

    # Check service health
    check_service_health

    log_success "Deployment completed successfully"
}

check_service_health() {
    log_info "Checking service health..."

    services=("web" "db" "redis" "celery_worker" "ai_processor" "analytics_engine")

    for service in "${services[@]}"; do
        if $COMPOSE_CMD -f $DOCKER_COMPOSE_FILE ps $service | grep -q "Up"; then
            log_success "$service is running"
        else
            log_error "$service failed to start"
            show_service_logs $service
            exit 1
        fi
    done
}

show_service_logs() {
    service=$1
    log_warning "Showing logs for $service:"
    $COMPOSE_CMD -f $DOCKER_COMPOSE_FILE logs $service
}

run_database_migrations() {
    log_info "Running database migrations..."

    # Run migrations through the web service
    $COMPOSE_CMD -f $DOCKER_COMPOSE_FILE exec -T web flask db upgrade

    log_success "Database migrations completed"
}

run_initial_data_setup() {
    log_info "Setting up initial data..."

    # Create admin user and initial marketing campaigns
    $COMPOSE_CMD -f $DOCKER_COMPOSE_FILE exec -T web python -c "
from app import create_app, db
from app.models import User, Clinic
import os

app = create_app()
with app.app_context():
    # Create admin user if not exists
    admin = User.query.filter_by(email='admin@vexushub.com').first()
    if not admin:
        admin = User(
            email='admin@vexushub.com',
            name='Admin',
            password='admin123',
            role='admin'
        )
        db.session.add(admin)

        # Create demo clinic
        clinic = Clinic(
            name='Clínica Demo',
            owner_id=admin.id,
            plan_type='premium'
        )
        db.session.add(clinic)
        db.session.commit()

        print('Admin user and demo clinic created')
    else:
        print('Admin user already exists')
"

    log_success "Initial data setup completed"
}

setup_monitoring() {
    log_info "Setting up monitoring dashboards..."

    # Wait for Grafana to be ready
    sleep 10

    # Import default dashboards (would be done via API in production)
    log_info "Grafana dashboards will be available at http://localhost:3000"
    log_info "Default credentials: admin/admin"

    log_success "Monitoring setup completed"
}

show_deployment_summary() {
    echo
    log_success "🎉 Vexus Hub Phase 3 Deployment Completed!"
    echo
    echo "Services running:"
    echo "  🌐 Web Application: http://localhost"
    echo "  📊 Marketing Dashboard: http://localhost/marketing/dashboard.html"
    echo "  📈 Grafana: http://localhost:3000 (admin/admin)"
    echo "  📋 Kibana: http://localhost:5601"
    echo "  📊 Prometheus: http://localhost:9090"
    echo
    echo "API Endpoints:"
    echo "  📡 REST API: http://localhost/api/"
    echo "  🤖 AI Processing: http://localhost/ai/"
    echo "  📊 Analytics: http://localhost/analytics/"
    echo
    echo "Next steps:"
    echo "  1. Configure your domain and SSL certificates"
    echo "  2. Set up monitoring alerts"
    echo "  3. Configure backup policies"
    echo "  4. Review and customize marketing campaigns"
    echo
}

cleanup() {
    log_info "Cleaning up temporary files..."
    # Add cleanup logic if needed
}

# Main deployment flow
main() {
    echo "🚀 Starting Vexus Hub Phase 3 Deployment"
    echo "========================================"

    check_dependencies
    setup_environment
    generate_ssl_certificates
    create_monitoring_config
    build_and_deploy
    run_database_migrations
    run_initial_data_setup
    setup_monitoring
    show_deployment_summary
    cleanup

    echo
    log_success "Deployment finished successfully! 🎉"
}

# Handle script arguments
case "${1:-}" in
    "stop")
        log_info "Stopping services..."
        $COMPOSE_CMD -f $DOCKER_COMPOSE_FILE down
        log_success "Services stopped"
        ;;
    "restart")
        log_info "Restarting services..."
        $COMPOSE_CMD -f $DOCKER_COMPOSE_FILE restart
        log_success "Services restarted"
        ;;
    "logs")
        service="${2:-}"
        if [ -n "$service" ]; then
            $COMPOSE_CMD -f $DOCKER_COMPOSE_FILE logs -f $service
        else
            $COMPOSE_CMD -f $DOCKER_COMPOSE_FILE logs -f
        fi
        ;;
    "status")
        $COMPOSE_CMD -f $DOCKER_COMPOSE_FILE ps
        ;;
    "cleanup")
        log_warning "This will remove all containers and volumes. Are you sure? (y/N)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            $COMPOSE_CMD -f $DOCKER_COMPOSE_FILE down -v --remove-orphans
            log_success "Cleanup completed"
        fi
        ;;
    *)
        main
        ;;
esac