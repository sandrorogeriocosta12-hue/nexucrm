#!/bin/bash

###############################################################################
# 🧪 TESTE DO MODAL - TERMOS DE SERVIÇO
# Verifica se o modal está implementado corretamente
###############################################################################

echo "🧪 TESTE DO MODAL - TERMOS DE SERVIÇO"
echo "===================================="
echo ""

# 1. Verificar se os arquivos existem
echo "✓ Verificando se arquivos de signup existem..."
if [ -f "frontend/signup-v2.html" ]; then
    echo "  ✅ signup-v2.html ENCONTRADO"
else
    echo "  ❌ signup-v2.html NÃO ENCONTRADO"
    exit 1
fi

if [ -f "frontend/signup-nexus.html" ]; then
    echo "  ✅ signup-nexus.html ENCONTRADO"
else
    echo "  ⚠️  signup-nexus.html não encontrado (opcional)"
fi

echo ""

# 2. Verificar se as funções estão implementadas
echo "✓ Verificando implementação do modal..."

# Check for openTermsModal function
if grep -q "window.openTermsModal" frontend/signup-v2.html; then
    echo "  ✅ window.openTermsModal() - IMPLEMENTADO"
else
    echo "  ❌ window.openTermsModal() - NÃO ENCONTRADO"
fi

# Check for closeTermsModal function
if grep -q "window.closeTermsModal" frontend/signup-v2.html; then
    echo "  ✅ window.closeTermsModal() - IMPLEMENTADO"
else
    echo "  ❌ window.closeTermsModal() - NÃO ENCONTRADO"
fi

# Check for acceptTerms function
if grep -q "window.acceptTerms" frontend/signup-v2.html; then
    echo "  ✅ window.acceptTerms() - IMPLEMENTADO"
else
    echo "  ❌ window.acceptTerms() - NÃO ENCONTRADO"
fi

# Check for modal div
if grep -q "id=\"termsModal\"" frontend/signup-v2.html; then
    echo "  ✅ Modal HTML - IMPLEMENTADO"
else
    echo "  ❌ Modal HTML - NÃO ENCONTRADO"
fi

# Check for link to open modal
if grep -q "onclick=\"event.preventDefault(); openTermsModal()" frontend/signup-v2.html; then
    echo "  ✅ Link para abrir modal - IMPLEMENTADO"
else
    echo "  ❌ Link para abrir modal - NÃO ENCONTRADO"
fi

echo ""

# 3. Verificar headers de no-cache
echo "✓ Verificando headers de cache..."

if grep -q "Cache-Control" frontend/signup-v2.html; then
    echo "  ✅ Meta tag Cache-Control - ADICIONADA"
else
    echo "  ⚠️  Meta tag Cache-Control - não encontrada"
fi

if grep -q "CACHE BUSTING" app_server.py; then
    echo "  ✅ Cache busting em app_server.py - CONFIGURADO"
else
    echo "  ⚠️  Cache busting em app_server.py - não configurado"
fi

if grep -q "no-cache, no-store" app_server.py; then
    echo "  ✅ Headers HTTP no-cache - CONFIGURADOS"
else
    echo "  ⚠️  Headers HTTP no-cache - não configurados"
fi

echo ""
echo "===================================="
echo "✅ TESTE COMPLETO!"
echo ""
echo "Próximos passos:"
echo "1. Fazer push para GitHub: git push origin main"
echo "2. Railway vai fazer rebuild automático"
echo "3. Limpar cache: CTRL+SHIFT+DELETE no navegador"
echo "4. Ir em https://api.nexuscrm.tech/signup"
echo "5. Clicar em 'termos de serviço'"
echo "6. O modal agora deve aparecer! 🎉"
echo ""
echo "⚠️  Se ainda não aparecer, limpar cache do Cloudflare:"
echo "   - Ir em: https://dash.cloudflare.com/"
echo "   - Selecionar domínio"
echo "   - Cache → Purge Everything"
echo ""
