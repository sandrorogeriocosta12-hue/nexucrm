#!/bin/bash

# Script de monitoramento contínuo do Railroad build
# Verifica a cada 30 segundos se a página foi atualizada em produção

echo "🚀 MONITORAMENTO DO RAILWAY BUILD"
echo "═══════════════════════════════════════════════"
echo ""
echo "Monitor iniciado em: $(date '+%d/%m/%Y %H:%M:%S')"
echo "Verificando a cada 30 segundos..."
echo ""

TENTATIVAS=0
MAX_TENTATIVAS=40  # 40 tentativas × 30 seg = 20 minutos

while [ $TENTATIVAS -lt $MAX_TENTATIVAS ]; do
  TENTATIVAS=$((TENTATIVAS + 1))
  
  # Verificar o título da página
  TITLE=$(timeout 10 curl -s "https://api.nexuscrm.tech/signup?v=$(date +%s)" 2>&1 | grep -o "<title>.*</title>" | head -1)
  
  # Verificar se contém o novo design
  if echo "$TITLE" | grep -q "Criar Conta"; then
    echo ""
    echo "✅ ✅ ✅ SUCESSO! ✅ ✅ ✅"
    echo ""
    echo "🎉 BUILD CONCLUÍDO COM SUCESSO!"
    echo "📄 Página de signup atualizada em produção"
    echo ""
    echo "Detalhes:"
    echo "   URL: https://api.nexuscrm.tech/signup"
    echo "   Título: $TITLE"
    echo "   Hora: $(date '+%d/%m/%Y %H:%M:%S')"
    echo "   Tentativa: $TENTATIVAS"
    echo ""
    echo "✨ O novo design está VIVO em produção!"
    exit 0
  fi
  
  # Verificar se está com design antigo
  if echo "$TITLE" | grep -q "Nexus Service - Cadastro"; then
    STATUS_DISPLAY="⏳ Ainda compilando (design antigo)"
  elif [ -z "$TITLE" ]; then
    STATUS_DISPLAY="❌ Erro na conexão"
    TITLE="[SEM RESPOSTA]"
  else
    STATUS_DISPLAY="❓ Status desconhecido"
  fi
  
  # Mostrar progresso
  echo "[$(printf "%02d" $TENTATIVAS)/$MAX_TENTATIVAS] $STATUS_DISPLAY"
  echo "   Título: $TITLE"
  echo "   Hora: $(date '+%H:%M:%S')"
  
  # Se chegou a 10 tentativas (5 min), mostrar status de servidor
  if [ $TENTATIVAS -eq 10 ]; then
    echo ""
    echo "📊 Verificando saúde do servidor..."
    STATUS_API=$(timeout 10 curl -s https://api.nexuscrm.tech/status 2>&1 | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    if [ ! -z "$STATUS_API" ]; then
      echo "   Server status: $STATUS_API"
    fi
    echo ""
  fi
  
  # Aguardar 30 segundos
  if [ $TENTATIVAS -lt $MAX_TENTATIVAS ]; then
    sleep 30
  fi
done

echo ""
echo "❌ TIMEOUT ATINGIDO"
echo "═══════════════════════════════════════════════"
echo ""
echo "⏰ Monitoramento expirou após 20 minutos"
echo "📝 Possíveis razões:"
echo "   1. Build ainda em progresso (tome mais tempo do esperado)"
echo "   2. Build falhou com erro"
echo "   3. Problema de conectividade"
echo ""
echo "🔍 Próximos passos:"
echo "   1. Acesse: https://railway.app"
echo "   2. Procure por 'Deployments' ou 'Build Log'"
echo "   3. Verifique se há erros"
echo "   4. Se falhou, faça redeploy manual"
echo ""
echo "Monitored até: $(date '+%d/%m/%Y %H:%M:%S')"
exit 1
