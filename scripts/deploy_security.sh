#!/bin/bash

# Secure deployment script for Vexus Service
# Usage: ./deploy_security.sh [staging|production]

set -e

ENVIRONMENT=${1:-staging}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔒 Deploying Vexus Service with security checks - Environment: $ENVIRONMENT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Pre-deployment security checks
security_checks() {
    print_status "Running pre-deployment security checks..."

    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        print_error "Do not run deployment as root!"
        exit 1
    fi

    # Check for required environment variables
    required_vars=("SECRET_KEY" "DB_PASSWORD")
    if [[ "$ENVIRONMENT" == "production" ]]; then
        required_vars+=("AWS_ACCESS_KEY_ID" "AWS_SECRET_ACCESS_KEY" "SSL_CERT_PATH")
    fi

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            print_error "Required environment variable $var is not set!"
            exit 1
        fi
    done

    # Check secret key strength
    if [[ ${#SECRET_KEY} -lt 32 ]]; then
        print_error "SECRET_KEY must be at least 32 characters long!"
        exit 1
    fi

    # Run security audit
    print_status "Running security audit..."
    cd "$PROJECT_ROOT"
    python scripts/security_audit.py --quick

    if [[ $? -ne 0 ]]; then
        print_error "Security audit failed! Fix issues before deploying."
        exit 1
    fi

    print_status "Security checks passed!"
}

# Setup environment
setup_environment() {
    print_status "Setting up $ENVIRONMENT environment..."

    cd "$PROJECT_ROOT"

    # Create necessary directories
    mkdir -p logs security-reports ssl

    # Set secure permissions
    chmod 755 scripts/*.sh
    chmod 644 nginx/nginx.conf
    chmod 600 .env* 2>/dev/null || true

    # Generate self-signed certificate for staging
    if [[ "$ENVIRONMENT" == "staging" ]]; then
        if [[ ! -f ssl/server.crt ]]; then
            print_status "Generating self-signed SSL certificate for staging..."
            openssl req -x509 -newkey rsa:4096 -keyout ssl/server.key -out ssl/server.crt -days 365 -nodes -subj "/C=BR/ST=SP/L=Sao Paulo/O=Vexus/CN=localhost"
            chmod 600 ssl/server.key
            chmod 644 ssl/server.crt
        fi
    fi
}

# Deploy application
deploy_app() {
    print_status "Deploying application to $ENVIRONMENT..."

    cd "$PROJECT_ROOT"

    # Pull latest changes (if using git)
    if [[ -d .git ]]; then
        git pull origin main
    fi

    # Build and deploy with docker-compose
    if [[ "$ENVIRONMENT" == "production" ]]; then
        COMPOSE_FILE="docker-compose.production.yml"
    else
        COMPOSE_FILE="docker-compose.yml"
    fi

    # Stop existing containers
    docker-compose -f "$COMPOSE_FILE" down

    # Build images
    docker-compose -f "$COMPOSE_FILE" build --no-cache

    # Run security scan on images (if docker scan is available)
    if command -v docker &> /dev/null && docker scan --version &> /dev/null; then
        print_status "Scanning Docker images for vulnerabilities..."
        docker-compose -f "$COMPOSE_FILE" config | grep "image:" | awk '{print $2}' | while read -r image; do
            docker scan "$image" || true
        done
    fi

    # Start services
    docker-compose -f "$COMPOSE_FILE" up -d

    # Wait for services to be healthy
    print_status "Waiting for services to be healthy..."
    sleep 30

    # Run health checks
    if [[ "$ENVIRONMENT" == "production" ]]; then
        HEALTH_URL="https://localhost/health"
    else
        HEALTH_URL="http://localhost:8000/health"
    fi

    max_attempts=10
    attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -k "$HEALTH_URL" &>/dev/null; then
            print_status "Health check passed!"
            break
        else
            print_warning "Health check failed (attempt $attempt/$max_attempts)"
            sleep 10
            ((attempt++))
        fi
    done

    if [[ $attempt -gt $max_attempts ]]; then
        print_error "Health check failed after $max_attempts attempts!"
        exit 1
    fi
}

# Post-deployment tasks
post_deploy() {
    print_status "Running post-deployment tasks..."

    # Run final security audit
    cd "$PROJECT_ROOT"
    python scripts/security_audit.py

    # Backup configuration
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    cp docker-compose.production.yml "backups/docker-compose.production.$TIMESTAMP.yml" 2>/dev/null || true

    # Log deployment
    echo "$(date): Deployment to $ENVIRONMENT completed successfully" >> logs/deploy.log

    print_status "Deployment completed successfully! 🎉"
    print_status "Application is running at: http://localhost:8000"
    if [[ "$ENVIRONMENT" == "production" ]]; then
        print_status "Production URL: https://your-domain.com"
    fi
}

# Main deployment process
main() {
    security_checks
    setup_environment
    deploy_app
    post_deploy

    print_status "🚀 Deployment completed with security validation!"
}

# Run main function
main "$@"