#!/bin/bash

# Script para monitorar se a API foi atualizada em produção
# Este script verifica a página de signup no domínio api.nexuscrm.tech
# e compara com o código local

echo "🔍 Verificando atualização do domínio api.nexuscrm.tech..."
echo ""

# Fazer download da página atual em produção
echo "📥 Baixando página de signup de produção..."
curl -s https://api.nexuscrm.tech/signup > /tmp/production_signup.html

# Comparar com arquivo local
echo "📊 Comparando com versão local..."

# Verificar se contém novo design (design-system.css)
if grep -q "design-system.css" /tmp/production_signup.html; then
    echo "✅ ATUALIZADO! Novo design encontrado em produção"
    echo "   api.nexuscrm.tech está rodando a versão mais recente"
else
    echo "⏳ AINDA EM ATUALIZAÇÃO..."
    echo "   Railway está compilando o novo código"
    echo "   Aguarde 2-3 minutos para o build terminar"
    
    # Mostrar progresso
    echo ""
    echo "Verificando novamente em 30 segundos..."
    sleep 30
    
    # Tentar novamente
    curl -s https://api.nexuscrm.tech/signup > /tmp/production_signup.html
    
    if grep -q "design-system.css" /tmp/production_signup.html; then
        echo "✅ ATUALIZADO! Novo design encontrado em produção"
        echo "   api.nexuscrm.tech foi atualizado com sucesso!"
    else
        echo "⏳ Ainda compilando..."
        echo "   Verifique novamente em alguns momentos"
        echo ""
        echo "   Você pode monitorar o deployment em:"
        echo "   https://railway.app"
    fi
fi

echo ""
echo "📝 Informações técnicas:"
curl -s -I https://api.nexuscrm.tech/signup | grep -E "(Server|Railway|Cache)" | head -5

