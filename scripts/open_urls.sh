#!/bin/bash
#
# Vexus CRM - Quick Access Guide
# Abre automaticamente as URLs importantes no navegador
#

echo "🚀 Vexus CRM - Abrir URLs"
echo "=================================="
echo ""

# Verificar se o sistema está rodando
echo "Verificando sistema..."
if ! curl -s http://localhost:8080/health > /dev/null; then
    echo "⚠️  Backend não está respondendo na porta 8080"
    echo "Execute: ./scripts/start_system.sh"
    exit 1
fi

echo "✅ Sistema está pronto!"
echo ""

# URLs
DASHBOARD="http://localhost:8081/dashboard.html"
API_DOCS="http://localhost:8080/docs"
HEALTH="http://localhost:8080/health"

echo "📋 URLs Disponíveis:"
echo "  1. Dashboard Principal:  $DASHBOARD"
echo "  2. API Documentation:    $API_DOCS"
echo "  3. Health Check:         $HEALTH"
echo ""

# Tentar abrir em navegadores comuns
echo "Abrindo URLs no navegador padrão..."

# Prioridade: Firefox > Chrome > Chromium > xdg-open
if command -v firefox &> /dev/null; then
    firefox "$DASHBOARD" "$API_DOCS" &
    echo "✅ Aberto com Firefox"
elif command -v google-chrome &> /dev/null; then
    google-chrome "$DASHBOARD" "$API_DOCS" &
    echo "✅ Aberto com Google Chrome"
elif command -v chromium &> /dev/null; then
    chromium "$DASHBOARD" "$API_DOCS" &
    echo "✅ Aberto com Chromium"
elif command -v xdg-open &> /dev/null; then
    xdg-open "$DASHBOARD" &
    xdg-open "$API_DOCS" &
    echo "✅ Aberto com navegador padrão"
else
    echo "⚠️  Nenhum navegador automático encontrado"
    echo "Abra manualmente:"
    echo "  - $DASHBOARD"
    echo "  - $API_DOCS"
fi

echo ""
echo "✨ Para fazer login:"
echo "  Email:    admin@vexus.com"
echo "  Senha:    admin123"
echo ""
echo "🧪 Para executar testes: bash scripts/quickstart_tests.sh"
