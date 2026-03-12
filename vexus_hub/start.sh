#!/bin/bash
# Script de inicialização do Vexus Hub
# Execute este script para iniciar o sistema completo

echo "🚀 Iniciando Vexus IA - Sistema de Agendamento"
echo "=================================================="

# Verificar se estamos no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Erro: Execute este script do diretório raiz do projeto (vexus_hub/)"
    exit 1
fi

# Verificar se o Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado. Instale o Docker primeiro."
    exit 1
fi

# Verificar se o Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não está instalado. Instale o Docker Compose primeiro."
    exit 1
fi

echo "📋 Verificando configuração..."

# Verificar se .env existe
if [ ! -f ".env" ]; then
    echo "⚠️  Arquivo .env não encontrado. Copiando .env.example..."
    cp .env.example .env
    echo "✅ Arquivo .env criado. Edite-o com suas configurações antes de continuar."
    echo ""
    echo "📝 Configure as seguintes variáveis essenciais:"
    echo "   - SECRET_KEY"
    echo "   - DATABASE_URL (já configurado para Docker)"
    echo "   - WHATSAPP_ACCESS_TOKEN"
    echo "   - WHATSAPP_PHONE_NUMBER_ID"
    echo "   - OPENAI_API_KEY"
    echo ""
    read -p "Pressione Enter após configurar o .env..."
fi

echo "🐳 Construindo e iniciando serviços..."

# Parar serviços existentes
docker-compose down

# Construir e iniciar serviços
docker-compose up -d --build

echo "⏳ Aguardando serviços ficarem prontos..."
sleep 30

# Verificar status dos serviços
echo "📊 Status dos serviços:"
docker-compose ps

# Executar migrações do banco
echo "🗄️  Executando migrações do banco de dados..."
docker-compose exec web flask db upgrade

# Verificar se a aplicação está respondendo
echo "🌐 Verificando se a aplicação está funcionando..."
if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "✅ Aplicação está funcionando!"
    echo ""
    echo "🎉 Vexus Hub iniciado com sucesso!"
    echo ""
    echo "📱 Acesse a aplicação:"
    echo "   - Web: http://localhost:8000"
    echo "   - API: http://localhost:8000/api/"
    echo "   - WhatsApp Webhook: http://localhost:8000/api/whatsapp/webhook"
    echo ""
    echo "🔧 Comandos úteis:"
    echo "   - Ver logs: docker-compose logs -f web"
    echo "   - Parar serviços: docker-compose down"
    echo "   - Reiniciar: docker-compose restart"
    echo "   - Executar worker: docker-compose exec web python run.py worker"
    echo ""
    echo "📚 Para mais informações, consulte o README.md"
else
    echo "❌ Erro: Aplicação não está respondendo"
    echo "   Verifique os logs: docker-compose logs web"
    exit 1
fi