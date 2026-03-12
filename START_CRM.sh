#!/bin/bash

# 🚀 SCRIPT RÁPIDO PARA INICIAR VEXUS CRM AGÊNTICO

echo "╔════════════════════════════════════════════════════════╗"
echo "║  VEXUS CRM AGÊNTICO - INICIALIZAÇÃO                   ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Verificar se estamos no diretório correto
if [ ! -f "vexus_crm/main.py" ]; then
    echo "❌ Erro: Execute este script na raiz do projeto Vexus Service"
    exit 1
fi

echo "✅ Projeto encontrado"
echo ""

# Menu de opções
echo "Escolha uma opção:"
echo ""
echo "1) Iniciar com Docker (RECOMENDADO)"
echo "2) Instalar dependências Python"
echo "3) Rodar testes"
echo "4) Rodar exemplos"
echo "5) Ver documentação"
echo "6) Limpar containers Docker"
echo ""
read -p "Digite a opção (1-6): " opcao

case $opcao in
    1)
        echo ""
        echo "🐳 Iniciando com Docker Compose..."
        echo ""
        cd vexus_crm
        
        # Verificar se .env existe
        if [ ! -f ".env" ]; then
            echo "⚠️  Arquivo .env não encontrado. Criando a partir do exemplo..."
            cp .env.example .env
            echo "📝 Edite o arquivo .env com suas credenciais"
        fi
        
        echo ""
        echo "Iniciando stack (PostgreSQL + Redis + API + Nginx)..."
        docker-compose up --build
        ;;
    
    2)
        echo ""
        echo "📦 Instalando dependências Python..."
        pip install -r vexus_crm/requirements.txt
        echo "✅ Dependências instaladas!"
        ;;
    
    3)
        echo ""
        echo "🧪 Rodando testes..."
        pytest tests/test_crm_agentico.py -v
        ;;
    
    4)
        echo ""
        echo "📚 Rodando exemplos..."
        python3 vexus_crm/examples.py
        ;;
    
    5)
        echo ""
        echo "📖 Documentação disponível:"
        echo ""
        echo "  • README.md - Overview do projeto"
        echo "  • GETTING_STARTED.md - Passo-a-passo"
        echo "  • examples.py - 6 exemplos práticos"
        echo "  • CONFIGURACOES_EMPRESA.md - Roadmap 6 meses"
        echo ""
        echo "Abrir README.md? (s/n)"
        read -p "> " resp
        if [ "$resp" = "s" ]; then
            cat vexus_crm/README.md | less
        fi
        ;;
    
    6)
        echo ""
        echo "🧹 Limpando containers Docker..."
        cd vexus_crm
        docker-compose down -v
        echo "✅ Containers removidos!"
        ;;
    
    *)
        echo "❌ Opção inválida"
        exit 1
        ;;
esac

echo ""
echo "✨ Pronto!"
