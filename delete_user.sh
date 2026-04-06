#!/bin/bash
echo "🗑️  DELETANDO USUÁRIO: victor226942@gmail.com"
echo "=============================================="

# Definir as credenciais
EMAIL="victor226942@gmail.com"
DB="vexus_crm"
USER="vexus"
PASS="password"
HOST="localhost"

# Exportar senha
export PGPASSWORD=$PASS

echo "📊 Listando tabelas de usuários..."
psql -h $HOST -U $USER -d $DB -c "
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE '%user%'
    ORDER BY table_name;
" 2>&1

echo ""
echo "🔍 Procurando por usuário com email: $EMAIL"
echo ""

# Array de possíveis tabelas de usuários
tables=("user" "users" "account" "accounts" "customer" "customers" "auth_user")

deleted=false

for table in "${tables[@]}"; do
    echo -n "  Verificando tabela '$table'... "
    
    # Tentar deletar
    result=$(psql -h $HOST -U $USER -d $DB -c "
        DELETE FROM \"$table\" 
        WHERE email = '$EMAIL' OR user_email = '$EMAIL' OR email_address = '$EMAIL'
        RETURNING *;
    " 2>&1)
    
    # Verificar se houve sucesso
    if echo "$result" | grep -q "DELETE"; then
        lines=$(echo "$result" | grep -c "^")
        if [ $lines -gt 0 ]; then
            echo "✅ Deletado ($lines linha(s))"
            deleted=true
        else
            echo "⚠️  Tabela existe mas usuário não encontrado"
        fi
    else
        echo "⏭️  Tabela não existe"
    fi
done

echo ""
if [ "$deleted" = true ]; then
    echo "✅ USUÁRIO DELETADO COM SUCESSO!"
else
    echo "ℹ️  Usuário não foi encontrado em nenhuma tabela"
fi

echo ""
echo "✨ Verificação final..."
psql -h $HOST -U $USER -d $DB -c "
    SELECT 'Tabelas no banco:' as info;
    SELECT COUNT(*) || ' usuários' FROM \"user\" LIMIT 1;
" 2>&1