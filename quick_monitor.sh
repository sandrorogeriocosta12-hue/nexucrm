#!/bin/bash

# Monitoramento rápido e discreto - verifica a cada 20 segundos
# Avisa só quando encontrar o novo design ou erro crítico

echo "🔄 Monitoramento de rebuild iniciado em background"
echo "   Verificando a cada 20 segundos..."
echo "   Será exibido uma notificação quando atualizar ou após timeout"
echo ""

TENTATIVAS=0
while [ $TENTATIVAS -lt 60 ]; do
  TENTATIVAS=$((TENTATIVAS + 1))
  
  TITLE=$(timeout 10 curl -s "https://api.nexuscrm.tech/signup?v=$(date +%s)" 2>&1 | grep -o "<title>.*</title>" | head -1)
  
  if echo "$TITLE" | grep -q "Criar Conta"; then
    echo ""
    echo "════════════════════════════════════════════"
    echo "✅ ✅ ✅ BUILD CONCLUÍDO COM SUCESSO! ✅ ✅ ✅"
    echo "════════════════════════════════════════════"
    echo ""
    echo "📄 Página atualizada em produção!"
    echo "   URL: https://api.nexuscrm.tech/signup"
    echo "   Novo design está VIVO"
    echo "   Tentativa: $TENTATIVAS de 60"
    echo "   Tempo: $(date '+%H:%M:%S')"
    echo ""
    break
  fi
  
  # Mostrar barra de progresso simples
  PERCENT=$((TENTATIVAS * 100 / 60))
  echo -ne "\r⏳ Build ainda processando... [$PERCENT%] [$(printf '%-20s' $(head -c $((PERCENT/5)) <<< '####################'))] Tentativa $TENTATIVAS/60"
  
  sleep 20
done

if [ $TENTATIVAS -ge 60 ]; then
  echo ""
  echo ""
  echo "⚠️  TIMEOUT ATINGIDO - Build ainda não completou após 20 minutos"
  echo ""
  echo "Próximos passos:"
  echo "  1. Acesse: https://railway.app"
  echo "  2. Procure por erros em 'Deployments'"
  echo "  3. Se falhou, faça redeploy manual"
  echo ""
fi

echo "Monitoramento finalizado: $(date '+%H:%M:%S')"
