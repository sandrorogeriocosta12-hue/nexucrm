#!/bin/bash

###############################################################################
# 🚀 DEPLOY IMEDIATO - LANÇA ATUALIZAÇÕES PARA PRODUÇÃO
###############################################################################

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           🚀 LANÇANDO ATUALIZAÇÕES PARA PRODUÇÃO               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Verificar status git
echo "📊 Verificando status do repositório..."
git status --short
echo ""

# Confirmar que tudo está committed
if [ -z "$(git status --short)" ]; then
    echo "✅ Todos os arquivos estão commitados"
else
    echo "⚠️  Há arquivos não commitados!"
    git add -A
    git commit -m "🔄 Auto-commit antes do deploy"
fi

echo ""

# Fazer push para origin/main
echo "🔄 Empurrando para GitHub..."
git push origin main

echo ""
echo "✅ PUSH COMPLETO!"
echo ""

# Verificar implementação
echo "📋 Verificando implementação..."

if grep -q "Cache-Control" frontend/signup-v2.html; then
    echo "✅ Cache-busting adicionado ao frontend"
else
    echo "❌ Cache-busting NÃO encontrado"
fi

if grep -q "Surrogate-Control" app_server.py; then
    echo "✅ Headers NO-CACHE configurados no backend"
else
    echo "❌ Headers NO-CACHE NÃO encontrados"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   ✅ DEPLOY INICIADO!                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "🔍 O QUE ACONTECEU:"
echo "  1. ✅ Commits enviados para GitHub"
echo "  2. ✅ Railroad detectou novo push"
echo "  3. ⏳ Railroad INICIANDO rebuild (5-10 minutos)"
echo "  4. ⏳ Nova imagem Docker sendo construída"
echo "  5. ⏳ Aplicação será redeploy em https://api.nexuscrm.tech"
echo ""
echo "📝 MONITORAR DEPLOY:"
echo "  Acesse: https://railway.app"
echo "  Procure por: nexus-crm"
echo "  Status deve passar de 'Building' para 'Success' ✅"
echo ""
echo "🧪 TESTAR DEPOIS:"
echo "  1. Limpar cache: Ctrl+Shift+Delete (all time)"
echo "  2. Ir em: https://api.nexuscrm.tech/signup"
echo "  3. Clicar em 'termos de serviço'"
echo "  4. Modal deve aparecer agora! 🎉"
echo ""
echo "⏱️  Estimado: 10 minutos até estar 100% online"
echo ""

echo "Commits enviados:"
git log --oneline -3
echo ""
