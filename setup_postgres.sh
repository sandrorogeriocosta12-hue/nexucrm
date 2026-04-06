#!/bin/bash
echo "🔧 CONFIGURANDO POSTGRESQL PARA VEXUS CRM 🔧"
echo "=============================================="

# Verificar se PostgreSQL está rodando
echo "📊 Verificando status do PostgreSQL..."
if sudo systemctl is-active --quiet postgresql@16-main; then
    echo "✅ PostgreSQL está rodando"
else
    echo "❌ PostgreSQL não está rodando. Iniciando..."
    sudo systemctl start postgresql@16-main
fi

echo ""
echo "👤 Criando usuário 'vexus'..."
sudo -u postgres psql -c "CREATE USER vexus WITH PASSWORD 'password';" 2>/dev/null || echo "Usuário já existe"

echo ""
echo "🗄️  Criando banco de dados 'vexus_crm'..."
sudo -u postgres psql -c "CREATE DATABASE vexus_crm OWNER vexus;" 2>/dev/null || echo "Banco já existe"

echo ""
echo "🔑 Concedendo permissões..."
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE vexus_crm TO vexus;"

echo ""
echo "🧪 Testando conexão..."
PGPASSWORD=password psql -h localhost -U vexus -d vexus_crm -c "SELECT 'Conexão PostgreSQL funcionando!' as status;" 2>/dev/null || echo "❌ Falha na conexão - pode ser necessário ajustar pg_hba.conf"

echo ""
echo "✅ CONFIGURAÇÃO CONCLUÍDA!"
echo "📝 DATABASE_URL: postgresql://vexus:password@localhost/vexus_crm"