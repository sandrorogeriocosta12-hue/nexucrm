# Makefile para Vexus Service

.PHONY: help install test lint format clean docker-up docker-down

# Cores
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m

help:
@echo "$(GREEN)Vexus Service - Comandos disponíveis:$(NC)"
@echo ""
@echo "$(YELLOW)Desenvolvimento:$(NC)"
@echo " make install Instala dependências e configura ambiente"
@echo " make dev Inicia servidor de desenvolvimento"
@echo " make shell Abre shell interativo"
@echo ""
@echo "$(YELLOW)Testes:$(NC)"
@echo " make test Executa todos os testes"
@echo " make test-unit Executa testes unitários"
@echo " make test-integration Executa testes de integração"
@echo " make test-e2e Executa testes end-to-end"
@echo " make coverage Executa testes com cobertura"
@echo " make test-report Gera relatório de testes"
@echo ""
@echo "$(YELLOW)Qualidade:$(NC)"
@echo " make lint Executa linting"
@echo " make format Formata código com black"
@echo " make type-check Verifica tipos com mypy"
@echo " make quality Executa todas as verificações de qualidade"
@echo ""
@echo "$(YELLOW)Docker:$(NC)"
@echo " make docker-up Inicia serviços com Docker"
@echo " make docker-down Para serviços Docker"
@echo " make docker-test Executa testes em container Docker"
@echo ""
@echo "$(YELLOW)Banco de dados:$(NC)"
@echo " make db-migrate Executa migrações"
@echo " make db-upgrade Atualiza banco para última versão"
@echo " make db-downgrade Reverte última migração"
@echo " make db-reset Reseta banco de dados"
@echo ""
@echo "$(YELLOW)Limpeza:$(NC)"
@echo " make clean Limpa arquivos temporários"
@echo " make clean-all Limpa tudo (incluindo dados Docker)"

install:
@echo "$(GREEN)Instalando dependências...$(NC)"
python -m pip install --upgrade pip
pip install -e ".[dev]"
pre-commit install
@echo "$(GREEN)✅ Ambiente configurado$(NC)"

dev:
@echo "$(GREEN)Iniciando servidor de desenvolvimento...$(NC)"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

shell:
@echo "$(GREEN)Abrindo shell interativo...$(NC)"
python -m ipython

test:
@echo "$(GREEN)Executando todos os testes...$(NC)"
./scripts/run_tests.sh --coverage

test-unit:
@echo "$(GREEN)Executando testes unitários...$(NC)"
./scripts/run_tests.sh --unit --coverage

test-integration:
@echo "$(GREEN)Executando testes de integração...$(NC)"
./scripts/run_tests.sh --integration --coverage

test-e2e:
@echo "$(GREEN)Executando testes end-to-end...$(NC)"
./scripts/run_tests.sh --e2e

coverage:
@echo "$(GREEN)Executando testes com cobertura...$(NC)"
pytest --cov=app --cov-report=html --cov-report=term-missing

test-report:
@echo "$(GREEN)Gerando relatório de testes...$(NC)"
python tests/reports/generate_coverage_report.py

lint:
@echo "$(GREEN)Executando linting...$(NC)"
flake8 app/ tests/
@echo "$(GREEN)✅ Linting concluído$(NC)"

format:
@echo "$(GREEN)Formatando código...$(NC)"
black app/ tests/
isort app/ tests/
@echo "$(GREEN)✅ Formatação concluída$(NC)"

type-check:
@echo "$(GREEN)Verificando tipos...$(NC)"
mypy app/ --config-file pyproject.toml
@echo "$(GREEN)✅ Verificação de tipos concluída$(NC)"

quality: lint format type-check
@echo "$(GREEN)✅ Todas as verificações de qualidade concluídas$(NC)"

docker-up:
@echo "$(GREEN)Iniciando serviços Docker...$(NC)"
docker-compose up -d
@echo "$(GREEN)✅ Serviços iniciados$(NC)"

docker-down:
@echo "$(GREEN)Parando serviços Docker...$(NC)"
docker-compose down
@echo "$(GREEN)✅ Serviços parados$(NC)"

docker-test:
@echo "$(GREEN)Executando testes em container Docker...$(NC)"
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
@echo "$(GREEN)✅ Testes concluídos$(NC)"

db-migrate:
@echo "$(GREEN)Criando nova migração...$(NC)"
alembic revision --autogenerate -m "$(message)"

db-upgrade:
@echo "$(GREEN)Aplicando migrações...$(NC)"
alembic upgrade head
@echo "$(GREEN)✅ Migrações aplicadas$(NC)"

db-downgrade:
@echo "$(GREEN)Revertendo última migração...$(NC)"
alembic downgrade -1
@echo "$(GREEN)✅ Migração revertida$(NC)"

db-reset:
@echo "$(RED)Atenção: Isso irá resetar o banco de dados!$(NC)"
@read -p "Tem certeza? (s/n): " confirm; \
if [ $$confirm = "s" ]; then \
alembic downgrade base && \
alembic upgrade head && \
echo "$(GREEN)✅ Banco de dados resetado$(NC)"; \
else \
echo "$(YELLOW)Operação cancelada$(NC)"; \
fi

clean:
@echo "$(GREEN)Limpando arquivos temporários...$(NC)"
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*~" -delete
find . -type f -name "*.swp" -delete
rm -rf .coverage
rm -rf htmlcov
rm -rf .pytest_cache
rm -rf .mypy_cache
@echo "$(GREEN)✅ Limpeza concluída$(NC)"

clean-all: clean docker-down
@echo "$(GREEN)Limpando dados Docker...$(NC)"
docker system prune -f
docker volume prune -f
@echo "$(GREEN)✅ Limpeza completa concluída$(NC)"