#!/bin/bash

# 🎯 TESTE RÁPIDO DO VEXUS CRM - TODAS AS TELAS
# Script para testar o sistema completo

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         TESTE RÁPIDO - VEXUS CRM AUDITADO              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}✅ STATUS DE CADA TELA:${NC}\n"

# URLs a testar
telas=(
    "login.html|Login"
    "dashboard.html|Dashboard"
    "contacts.html|Contatos"
    "pipeline.html|Pipeline"
    "tasks.html|Tarefas"
    "automations.html|Automações"
    "reports.html|Relatórios"
    "settings.html|Configurações"
)

echo "Servidor rodando em: http://localhost:8080"
echo ""
echo "TELAS DISPONÍVEIS:"
echo "─────────────────────────────────────────────"

for tela in "${telas[@]}"; do
    IFS='|' read -r url nome <<< "$tela"
    echo -e "${GREEN}✅${NC} http://localhost:8080/frontend/$url"
    echo "   → $nome"
done

echo ""
echo "─────────────────────────────────────────────"
echo ""
echo -e "${BLUE}🔧 INSTRUÇÕES:${NC}"
echo ""
echo "1. Abra http://localhost:8080/frontend/login.html"
echo "   Email: seu@email.com"
echo "   Senha: qualquer coisa"
echo ""
echo "2. Após login, teste cada tela pelo sidebar"
echo ""
echo "3. Em cada tela teste:"
echo "   • Navegação (sidebar)"
echo "   • Add novo item (botão +)"
echo "   • Search/Filtro (onde aplicável)"
echo "   • Delete/Edit (onde aplicável)"
echo "   • Logout (bottom left)"
echo ""
echo -e "${YELLOW}✨ TUDO DEVE FUNCIONAR SEM ERROS NO CONSOLE${NC}"
echo ""
echo "Abra DevTools (F12) e vá para 'Console' para ver logs"
echo ""
