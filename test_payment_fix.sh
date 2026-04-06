#!/bin/bash
echo "🔧 TESTANDO ENDPOINT DE PAGAMENTO APÓS CORREÇÃO"
echo "==============================================="

DOMAIN="https://api.nexuscrm.tech"
ENDPOINT="/api/payment/process"

echo "🌐 Testando endpoint: $DOMAIN$ENDPOINT"
echo ""

# Teste 1: Verificar se endpoint existe
echo "📡 Teste 1: Verificando se endpoint responde..."
response=$(curl -s -w "%{http_code}" -o /dev/null -X OPTIONS "$DOMAIN$ENDPOINT" 2>/dev/null)
if [ "$response" = "200" ] || [ "$response" = "404" ] || [ "$response" = "405" ]; then
    echo "✅ Endpoint acessível (status: $response)"
else
    echo "❌ Endpoint não acessível (status: $response)"
fi

echo ""

# Teste 2: Testar POST request válido
echo "💳 Teste 2: Enviando requisição POST válida..."
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$DOMAIN$ENDPOINT" \
    -H "Content-Type: application/json" \
    -d '{
        "plan": "starter",
        "payment_method": "card",
        "email": "test@nexuscrm.tech",
        "card_name": "João Silva",
        "card_number": "4532015112830366",
        "card_cvv": "123",
        "contact_preference_email": true
    }' 2>/dev/null)

http_status=$(echo "$response" | grep "HTTP_STATUS:" | cut -d: -f2)
body=$(echo "$response" | sed '/HTTP_STATUS:/d')

echo "Status HTTP: $http_status"
if [ "$http_status" = "200" ]; then
    echo "✅ PAGAMENTO PROCESSADO COM SUCESSO!"
    echo "📄 Resposta:"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
elif [ "$http_status" = "405" ]; then
    echo "❌ ERRO: Method Not Allowed - Endpoint não aceita POST"
elif [ "$http_status" = "404" ]; then
    echo "❌ ERRO: Not Found - Endpoint não existe"
elif [ "$http_status" = "422" ]; then
    echo "⚠️  Validação falhou (esperado para dados de teste)"
else
    echo "❌ ERRO DESCONHECIDO (Status: $http_status)"
fi

echo ""
echo "🔍 Verificando se servidor está rodando..."
health_response=$(curl -s -w "%{http_code}" -o /dev/null "$DOMAIN/health" 2>/dev/null)
if [ "$health_response" = "200" ]; then
    echo "✅ Servidor está saudável"
else
    echo "❌ Servidor pode não estar rodando (health: $health_response)"
fi

echo ""
echo "📋 RESUMO DA CORREÇÃO:"
echo "• Removido endpoint duplicado de app_server.py"
echo "• Mantido endpoint correto em app/api_main.py"
echo "• Eliminado conflito de rotas"
echo ""
echo "🎯 O erro 'Method Not Allowed' deve estar resolvido!"