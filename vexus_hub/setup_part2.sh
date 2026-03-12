#!/bin/bash
echo "🚀 Configurando Parte 2: Operação e Vendas..."

# 1. Criar tabelas do sistema de parcerias
docker-compose exec web flask db migrate -m "add_partnership_system"
docker-compose exec web flask db upgrade

# 2. Criar usuários padrão
docker-compose exec web flask shell <from app.models import db, User, Partnership

# Criar gerente de vendas
sales_manager = User(
email='sales@vexus.ai',
name='Gerente de Vendas',
role='sales_manager'
)
sales_manager.password = 'Sales123!'
db.session.add(sales_manager)

# Criar vendedor
sales_rep = User(
email='vendas@vexus.ai',
name='Equipe de Vendas',
role='sales'
)
sales_rep.password = 'Vendas123!'
db.session.add(sales_rep)

# Criar parceiro de marketing exemplo
partner_user = User(
email='marketing@agenciaexemplo.com',
name='Agência Marketing',
role='partner_marketing'
)
partner_user.password = 'Parceiro123!'
db.session.add(partner_user)

db.session.commit()
EOF

# 3. Configurar templates de email
echo "📧 Configurando templates de email..."
cp -r email_templates/* /var/www/vexus/templates/emails/

# 4. Configurar integração Pagar.me
echo "💰 Configurando pagamentos..."
read -p "Informe sua API Key do Pagar.me: " pagarme_key
sed -i "s/PAGARME_API_KEY=.*/PAGARME_API_KEY=$pagarme_key/" .env

# 5. Iniciar serviços adicionais
docker-compose -f docker-compose-part2.yml up -d

echo "✅ Parte 2 configurada com sucesso!"
echo "📊 Acesse:"
echo " - Dashboard Comercial: https://seu-dominio.com/sales"
echo " - Portal de Parceiros: https://seu-dominio.com/partner"
echo " - Painel de Comissões: https://seu-dominio.com/commissions"