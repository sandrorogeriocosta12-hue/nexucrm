#!/bin/bash
# Vexus CRM - Professional Startup Script
# Production-ready initialization with health checks and monitoring

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="Vexus CRM"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$APP_DIR/.venv"
LOG_DIR="$APP_DIR/logs"
PID_FILE="$APP_DIR/vexus_crm.pid"

# Create necessary directories
mkdir -p "$LOG_DIR"

# Logging functions
log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}" | tee -a "$LOG_DIR/startup.log"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARN: $1${NC}" | tee -a "$LOG_DIR/startup.log"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_DIR/startup.log"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}" | tee -a "$LOG_DIR/startup.log"
}

# Check if process is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Stop function
stop_server() {
    log_info "Stopping $APP_NAME..."

    if is_running; then
        pid=$(cat "$PID_FILE")
        kill -TERM "$pid"

        # Wait for graceful shutdown
        for i in {1..30}; do
            if ! ps -p "$pid" > /dev/null 2>&1; then
                log_success "$APP_NAME stopped gracefully"
                rm -f "$PID_FILE"
                return 0
            fi
            sleep 1
        done

        # Force kill if graceful shutdown failed
        log_warn "Graceful shutdown failed, force killing..."
        kill -KILL "$pid" 2>/dev/null || true
        rm -f "$PID_FILE"
        log_success "$APP_NAME force stopped"
    else
        log_warn "$APP_NAME is not running"
    fi
}

# Health check function
health_check() {
    local max_attempts=30
    local attempt=1

    log_info "Performing health checks..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
            log_success "Health check passed on attempt $attempt"
            return 0
        fi

        log_info "Health check failed, attempt $attempt/$max_attempts, waiting..."
        sleep 2
        ((attempt++))
    done

    log_error "Health check failed after $max_attempts attempts"
    return 1
}

# Start function
start_server() {
    if is_running; then
        log_warn "$APP_NAME is already running (PID: $(cat "$PID_FILE"))"
        return 1
    fi

    log_info "Starting $APP_NAME..."

    # Check if virtual environment exists
    if [ ! -d "$VENV_DIR" ]; then
        log_error "Virtual environment not found at $VENV_DIR"
        log_info "Run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi

    # Check if .env file exists
    if [ ! -f ".env" ]; then
        log_warn ".env file not found, using default configuration"
        log_info "Consider copying .env.example to .env and configuring production settings"
    fi

    # Activate virtual environment and start server
    cd "$APP_DIR"
    source "$VENV_DIR/bin/activate"

    # Set environment variables
    export PYTHONPATH="$APP_DIR"
    export ENVIRONMENT="${ENVIRONMENT:-production}"

    # Start server in background
    nohup python -m uvicorn app_server:app \
        --host "${HOST:-0.0.0.0}" \
        --port "${PORT:-8000}" \
        --workers "${WORKERS:-1}" \
        --log-level "${LOG_LEVEL:-info}" \
        > "$LOG_DIR/server.log" 2>&1 &

    echo $! > "$PID_FILE"
    log_info "$APP_NAME started with PID: $(cat "$PID_FILE")"

    # Wait a moment for server to start
    sleep 3

    # Perform health check
    if health_check; then
        log_success "$APP_NAME is running and healthy!"
        log_info "🌐 Frontend: http://localhost:${PORT:-8000}/frontend/app.html"
        log_info "🔌 API: http://localhost:${PORT:-8000}/"
        log_info "💚 Health: http://localhost:${PORT:-8000}/health"
        if [ "${ENABLE_METRICS:-true}" = "true" ]; then
            log_info "📊 Metrics: http://localhost:${METRICS_PORT:-9090}/metrics"
        fi
    else
        log_error "$APP_NAME failed health check"
        stop_server
        exit 1
    fi
}

# Status function
status_server() {
    if is_running; then
        pid=$(cat "$PID_FILE")
        log_success "$APP_NAME is running (PID: $pid)"

        # Show resource usage
        if command -v ps >/dev/null 2>&1; then
            ps -p "$pid" -o pid,ppid,cmd,%cpu,%mem,etime
        fi

        # Quick health check
        if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
            log_success "Health check: PASSED"
        else
            log_error "Health check: FAILED"
        fi
    else
        log_error "$APP_NAME is not running"
        exit 1
    fi
}

# Restart function
restart_server() {
    log_info "Restarting $APP_NAME..."
    stop_server
    sleep 2
    start_server
}

# Main script logic
case "${1:-start}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        status_server
        ;;
    health)
        health_check
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|health}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the $APP_NAME server"
        echo "  stop    - Stop the $APP_NAME server"
        echo "  restart - Restart the $APP_NAME server"
        echo "  status  - Show server status and resource usage"
        echo "  health  - Perform health check"
        exit 1
        ;;
esac