# 🗄️ DATABASE MIGRATIONS COM ALEMBIC

## Instalação

```bash
pip install alembic
alembic init alembic
```

---

## Configuração (alembic/env.py)

```python
from sqlalchemy import engine_from_config, pool
from alembic import context
from vexus_crm.models import Base

config = context.config
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))

target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode"""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
    )
    
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

---

## Criar Migração (Auto-detect)

```bash
# Gerar nova migração detectando mudanças
alembic revision --autogenerate -m "Add user email field"

# Ver antes de aplicar
alembic current

# Aplicar migração
alembic upgrade head

# Voltar migração
alembic downgrade -1
```

---

## Exemplo de Migração Manual

```python
# alembic/versions/001_create_users.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password', sa.String(255), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_active', 'users', ['active'])

def downgrade():
    op.drop_table('users')
```

---

## Rollback de Produção

```bash
# Ver histórico
alembic history

# Voltar para versão específica
alembic downgrade ae1027a6acf

# Voltar N versões
alembic downgrade -3

# Rollback total (cuidado!)
alembic downgrade base
```

---

## Em CI/CD

```yaml
# .github/workflows/migrate.yml
name: Database Migrations

on:
  push:
    branches: [ main, staging ]

jobs:
  migrate:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Run migrations
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          alembic upgrade head
```

