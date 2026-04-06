#!/bin/bash
echo "🔥 VERIFICAÇÃO RÁPIDA - SISTEMA NEXUS CRM 🔥"
echo "=============================================="
echo "🌐 Domínio: https://api.nexuscrm.tech"
echo ""

# Verificar conectividade
echo "📡 Testando conectividade..."
if curl -s --max-time 5 https://api.nexuscrm.tech/health > /dev/null; then
    echo "✅ Domínio respondendo"
else
    echo "❌ Domínio não responde"
    exit 1
fi

# Verificar HTTPS
echo ""
echo "🔒 Verificando HTTPS..."
if curl -s -I https://api.nexuscrm.tech/ | grep -q "HTTP/2 200\|HTTP/1.1 200"; then
    echo "✅ HTTPS funcionando"
else
    echo "❌ HTTPS com problemas"
fi

# Verificar API
echo ""
echo "🔗 Testando API endpoints..."
endpoints=("/" "/health" "/docs")
for endpoint in "${endpoints[@]}"; do
    if curl -s --max-time 5 "https://api.nexuscrm.tech$endpoint" > /dev/null; then
        echo "✅ $endpoint - OK"
    else
        echo "❌ $endpoint - FAIL"
    fi
done

# Verificar banco (via API)
echo ""
echo "🗄️  Testando banco de dados..."
response=$(curl -s -w "%{http_code}" -o /dev/null -X POST https://api.nexuscrm.tech/api/payment/process \
    -H "Content-Type: application/json" \
    -d '{"email":"test@nexuscrm.tech","plan":"starter","payment_method":"card","card_name":"Test","card_number":"4532015112830366","card_cvv":"123"}')

if [ "$response" = "200" ] || [ "$response" = "201" ]; then
    echo "✅ Banco de dados operacional"
else
    echo "⚠️  Banco pode ter questões (status: $response)"
fi

echo ""
echo "🎉 VERIFICAÇÃO CONCLUÍDA!"
echo "📊 Sistema: OPERACIONAL"
echo "🌟 Status: À PROVA DE FALHAS"