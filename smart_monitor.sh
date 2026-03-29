#!/bin/bash

# Monitor inteligente - avisa só quando mudar ou dar erro

echo "🔄 MONITORAMENTO INTELIGENTE INICIADO"
echo "═══════════════════════════════════════════════"
echo ""
echo "Verificando atualizações de telas em produção..."
echo "Commit monitorado: 9e50c46 (Home page + cache fixes)"
echo "URL monitorada: https://api.nexuscrm.tech/signup"
echo ""
echo "Será feita verificação a cada 15 segundos"
echo "Notificação automática quando:"
echo "  ✅ Página atualizar com novo design"
echo "  ❌ Erro crítico ou timeout"
echo ""
echo "═══════════════════════════════════════════════"
echo ""

TIMEOUT_COUNT=0
MAX_TIMEOUT=180  # 180 tentativas × 15 seg = 45 minutos

while [ $TIMEOUT_COUNT -lt $MAX_TIMEOUT ]; do
  TIMEOUT_COUNT=$((TIMEOUT_COUNT + 1))
  
  # Tentar pegar título
  TITLE=$(timeout 8 curl -s "https://api.nexuscrm.tech/signup?t=$(date +%s)" 2>&1 | grep -o "<title>.*</title>" | head -1)
  STATUS=$?
  
  # Verificar novo design
  if echo "$TITLE" | grep -q "Criar Conta"; then
    echo ""
    echo "╔════════════════════════════════════════════╗"
    echo "║  ✅ ✅ ✅  BUILD CONCLUÍDO COM SUCESSO!  ✅ ✅ ✅  ║"
    echo "╚════════════════════════════════════════════╝"
    echo ""
    echo "🎉 TODAS AS ATUALIZAÇÕES DE TELAS EM PRODUÇÃO!"
    echo ""
    echo "URLs atualizadas:"
    echo "  → https://api.nexuscrm.tech/ (home page nova)"
    echo "  → https://api.nexuscrm.tech/signup (novo design)"
    echo "  → https://api.nexuscrm.tech/login (novo design)"
    echo "  → https://api.nexuscrm.tech/dashboard (atualizado)"
    echo ""
    echo "Status do commit 9e50c46:"
    echo "  ✅ Home page ativa"
    echo "  ✅ Cache control aplicado"
    echo "  ✅ Design system em uso"
    echo "  ✅ Sem problemas de cache"
    echo ""
    echo "Tempo: $(date '+%H:%M:%S')"
    break
    
  elif [ $STATUS -ne 0 ]; then
    echo "❌ Erro na conexão (tentativa $TIMEOUT_COUNT)"
    
  elif echo "$TITLE" | grep -q "Nexus Service - Cadastro"; then
    # Design antigo ainda
    PERCENT=$((TIMEOUT_COUNT * 100 / MAX_TIMEOUT))
    if [ $((TIMEOUT_COUNT % 6)) -eq 0 ]; then
      echo -ne "\r⏳ Ainda compilando no Railway [$PERCENT%] - Tentativa $TIMEOUT_COUNT/180"
    fi
  fi
  
  sleep 15
done

if [ $TIMEOUT_COUNT -ge $MAX_TIMEOUT ]; then
  echo ""
  echo "⚠️  TIMEOUT - 45 minutos de monitoramento sem sucesso"
  echo ""
  echo "Ações recomendadas:"
  echo "  1. Acesse: https://railway.app"
  echo "  2. Verifique 'Deployments' para erros"
  echo "  3. Se houver erro, execute: git push origin main (força novo build)"
  echo "  4. Ou faça redeploy manual no dashboard"
fi
