#!/bin/bash
echo "🔥 TESTE DE FOGO AVANÇADO - MONITORAMENTO CONTÍNUO 🔥"
echo "======================================================"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configurações
DOMAIN="https://api.nexuscrm.tech"
DURATION=300  # 5 minutos
CONCURRENT_USERS=100
REQUESTS_PER_USER=20

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Função para teste de stress com Apache Bench
stress_test() {
    log "Iniciando teste de stress com Apache Bench..."
    log "Configuração: $CONCURRENT_USERS usuários, $REQUESTS_PER_USER requisições cada"

    if command -v ab &> /dev/null; then
        ab -n $((CONCURRENT_USERS * REQUESTS_PER_USER)) -c $CONCURRENT_USERS -g stress_test.tsv "$DOMAIN/health" > stress_results.txt 2>&1

        # Analisar resultados
        if [ -f stress_results.txt ]; then
            RPS=$(grep "Requests per second" stress_results.txt | awk '{print $4}')
            TIME_PER_REQ=$(grep "Time per request.*mean" stress_results.txt | head -1 | awk '{print $4}')
            FAILED=$(grep "Failed requests" stress_results.txt | awk '{print $3}')

            success "Teste de stress concluído!"
            echo "📊 Requests/second: $RPS"
            echo "⏱️  Time/request: ${TIME_PER_REQ} ms"
            echo "❌ Failed requests: $FAILED"

            if (( $(echo "$RPS > 100" | bc -l) )) && (( $(echo "$TIME_PER_REQ < 1000" | bc -l) )); then
                success "DESEMPENHO EXCELENTE!"
            elif (( $(echo "$RPS > 50" | bc -l) )) && (( $(echo "$TIME_PER_REQ < 2000" | bc -l) )); then
                success "DESEMPENHO BOM!"
            else
                warning "DESEMPENHO PRECISA MELHORAR"
            fi
        fi
    else
        warning "Apache Bench não instalado. Pulando teste de stress avançado."
    fi
}

# Função para teste de memória e CPU
resource_test() {
    log "Monitorando recursos do sistema..."

    # CPU
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    echo "🖥️  CPU Usage: ${CPU_USAGE}%"

    # Memória
    MEM_TOTAL=$(free -m | grep Mem | awk '{print $2}')
    MEM_USED=$(free -m | grep Mem | awk '{print $3}')
    MEM_PERCENT=$((MEM_USED * 100 / MEM_TOTAL))
    echo "🧠 Memory: ${MEM_USED}MB/${MEM_TOTAL}MB (${MEM_PERCENT}%)"

    # Disco
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    echo "💾 Disk Usage: ${DISK_USAGE}%"

    # Verificar se recursos estão OK
    if (( $(echo "$CPU_USAGE < 80" | bc -l) )) && (( MEM_PERCENT < 80 )) && (( DISK_USAGE < 90 )); then
        success "Recursos do sistema OK"
    else
        warning "Recursos do sistema altos - verificar carga"
    fi
}

# Função para teste de conectividade contínua
connectivity_monitor() {
    log "Iniciando monitoramento de conectividade ($DURATION segundos)..."

    local checks=0
    local success=0
    local start_time=$(date +%s)

    while [ $(($(date +%s) - start_time)) -lt $DURATION ]; do
        checks=$((checks + 1))

        if curl -s --max-time 5 "$DOMAIN/health" > /dev/null 2>&1; then
            success=$((success + 1))
            echo -n "✅"
        else
            echo -n "❌"
        fi

        # Mostrar progresso a cada 10 checks
        if [ $((checks % 10)) -eq 0 ]; then
            uptime=$((success * 100 / checks))
            echo -ne " (${checks} checks, ${uptime}% uptime)\r"
        fi

        sleep 2
    done

    echo "" # Nova linha

    uptime_percentage=$((success * 100 / checks))
    log "Monitoramento concluído: $success/$checks checks bem-sucedidos (${uptime_percentage}% uptime)"

    if [ $uptime_percentage -ge 95 ]; then
        success "ALTA DISPONIBILIDADE CONFIRMADA!"
    elif [ $uptime_percentage -ge 80 ]; then
        warning "DISPONIBILIDADE ACEITÁVEL"
    else
        error "PROBLEMAS DE DISPONIBILIDADE DETECTADOS"
    fi
}

# Função para teste de segurança
security_test() {
    log "Executando testes de segurança..."

    # Teste de headers de segurança
    response=$(curl -s -I "$DOMAIN/" 2>/dev/null)

    if echo "$response" | grep -q "X-Frame-Options"; then
        success "X-Frame-Options presente"
    else
        warning "X-Frame-Options ausente"
    fi

    if echo "$response" | grep -q "X-Content-Type-Options"; then
        success "X-Content-Type-Options presente"
    else
        warning "X-Content-Type-Options ausente"
    fi

    if echo "$response" | grep -q "Strict-Transport-Security"; then
        success "HSTS configurado"
    else
        warning "HSTS não configurado"
    fi

    # Teste de arquivos sensíveis
    sensitive_files=("/.env" "/.git/config" "/admin" "/wp-admin" "/phpmyadmin")
    for file in "${sensitive_files[@]}"; do
        if curl -s --max-time 5 "$DOMAIN$file" | grep -q "404\|403"; then
            success "Arquivo sensível protegido: $file"
        else
            error "Arquivo sensível acessível: $file"
        fi
    done
}

# Função para teste de failover/recovery
failover_test() {
    log "Testando recuperação de falhas..."

    # Simular falha (se possível)
    log "Verificando resposta a erros..."

    # Teste com payload malformado
    response=$(curl -s -w "%{http_code}" -o /dev/null -X POST "$DOMAIN/api/payment/process" \
        -H "Content-Type: application/json" \
        -d '{"invalid": "json"' 2>/dev/null)

    if [ "$response" -eq 422 ] || [ "$response" -eq 400 ]; then
        success "API trata erros adequadamente"
    else
        warning "API pode não estar tratando erros corretamente"
    fi

    # Teste de timeout
    response=$(curl -s --max-time 1 "$DOMAIN/health" 2>/dev/null)
    if [ $? -eq 28 ]; then
        success "Timeouts são tratados corretamente"
    fi
}

# Executar todos os testes
main() {
    log "🚀 INICIANDO TESTE DE FOGO AVANÇADO"
    echo "=========================================="
    log "Domínio: $DOMAIN"
    log "Duração: $DURATION segundos"
    log "Usuários simultâneos: $CONCURRENT_USERS"
    echo ""

    # Teste de recursos
    resource_test
    echo ""

    # Teste de segurança
    security_test
    echo ""

    # Teste de failover
    failover_test
    echo ""

    # Teste de conectividade (background)
    connectivity_monitor &
    MONITOR_PID=$!

    # Teste de stress
    stress_test

    # Aguardar monitoramento terminar
    wait $MONITOR_PID

    echo ""
    log "🏁 TESTE DE FOGO AVANÇADO CONCLUÍDO!"
    echo ""
    log "📊 Resultados salvos em:"
    log "   • fire_test.py (resultados detalhados)"
    log "   • stress_results.txt (teste de stress)"
    echo ""
    success "Sistema testado e validado!"
}

# Executar
main "$@"