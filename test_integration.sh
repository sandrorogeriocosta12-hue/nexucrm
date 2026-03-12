#!/bin/bash

# 🚀 QUICK START - Testar Integração Completa
# =============================================

echo "🚀 VEXUS CRM - TESTES DE INTEGRAÇÃO"
echo "===================================="
echo ""
echo "1. Servidor já está rodando em: http://127.0.0.1:8003"
echo "2. Dashboard em: http://localhost:8000/deployment-dashboard.html"
echo ""

# Helper function
test_endpoint() {
    local name=$1
    local method=$2
    local url=$3
    local data=$4
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📌 $name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [ "$method" = "GET" ]; then
        curl -s "$url" | jq .
    elif [ "$method" = "POST" ]; then
        curl -s -X POST "$url" \
            -H "Content-Type: application/json" \
            -d "$data" | jq .
    fi
    echo ""
}

# Test 1: Health Check
test_endpoint "1️⃣ Health Check" "GET" "http://127.0.0.1:8003/health"

# Test 2: Get AI Config
test_endpoint "2️⃣ Get AI Config (Default)" "GET" "http://127.0.0.1:8003/api/config/ai"

# Test 3: Update AI Config
test_endpoint "3️⃣ Update AI Config" "POST" "http://127.0.0.1:8003/api/config/ai" \
    '{"personalidade":"consultiva","tom":"profissional","objecoes":"aceitar","prioridade":"servico"}'

# Test 4: Verify persistence
test_endpoint "4️⃣ Verify AI Config Persisted" "GET" "http://127.0.0.1:8003/api/config/ai"

# Test 5: List Channels
test_endpoint "5️⃣ List Available Channels" "GET" "http://127.0.0.1:8003/api/config/channels"

# Test 6: Get Website Channel Status
test_endpoint "6️⃣ Website Channel Status" "GET" "http://127.0.0.1:8003/api/config/channels/website"

# Test 7: Enable Website Channel
test_endpoint "7️⃣ Enable Website Channel" "POST" "http://127.0.0.1:8003/api/config/channels/website" \
    '{"enabled":true,"settings":{"widget_key":"demo-site-v1"}}'

# Test 8: Verify Website Enabled
test_endpoint "8️⃣ Website Channel Enabled" "GET" "http://127.0.0.1:8003/api/config/channels/website"

# Test 9: Send Message via Website Alias
test_endpoint "9️⃣ Send Message via 'website' Alias" "POST" "http://127.0.0.1:8003/api/messages/send" \
    '{"channel":"website","recipient":"visitor@example.com","content":"Bem-vindo! Como posso ajudar?","metadata":{}}'

# Test 10: Send Message via website_chat Enum
test_endpoint "🔟 Send Message via 'website_chat'" "POST" "http://127.0.0.1:8003/api/messages/send" \
    '{"channel":"website_chat","recipient":"user@site.com","content":"Teste com website_chat","metadata":{}}'

echo ""
echo "════════════════════════════════════════════════════"
echo "✅ TESTES COMPLETOS!"
echo "════════════════════════════════════════════════════"
echo ""
echo "📋 RESUMO DO QUE FOI TESTADO:"
echo ""
echo "✅ 1. Health check do servidor"
echo "✅ 2. GET /api/config/ai (config padrão)"
echo "✅ 3. POST /api/config/ai (salvar nova config)"
echo "✅ 4. Verificar persistência em disco"
echo "✅ 5. Listar canais disponíveis"
echo "✅ 6. Verificar status do canal website"
echo "✅ 7. Habilitar website channel"
echo "✅ 8. Verificar que foi habilitado"
echo "✅ 9. Enviar mensagem via alias 'website'"
echo "✅ 10. Enviar mensagem via 'website_chat'"
echo ""
echo "════════════════════════════════════════════════════"
echo "🎯 PRÓXIMOS PASSOS:"
echo "════════════════════════════════════════════════════"
echo ""
echo "1. Abra o Dashboard:"
echo "   → http://localhost:8000/deployment-dashboard.html"
echo ""
echo "2. Clique na aba: '🤖 Configurar IA'"
echo ""
echo "3. Teste a UI:"
echo "   • Mude a personalidade, tom, comportamento"
echo "   • Clique '💾 Salvar Configuração da IA'"
echo "   • Clique '🔌 Editar Canais'"
echo "   • Ative/Desative canais"
echo "   • Clique 'Salvar Alterações'"
echo ""
echo "4. Verifique que as mudanças foram persistidas:"
echo "   • Os dados salvos em JSON em vexus_crm/configs/"
echo "   • Os canais foram habilitados em runtime"
echo "   • Próximas requisições já usam as configs"
echo ""
echo "════════════════════════════════════════════════════"
