#!/bin/bash

# Script para configurar ambiente de desenvolvimento do Vexus Service
set -e

echo "🚀 Configurando ambiente de desenvolvimento do Vexus Service..."

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Função para exibir mensagens
print_msg() {
echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
echo -e "${YELLOW}📝 $1${NC}"
}

# Verifica Python
print_info "Verificando Python..."
if ! command -v python3.11 &> /dev/null; then
print_info "Python 3.11 não encontrado. Instalando..."
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
fi

# Cria virtual environment
print_info "Criando virtual environment..."
python3.11 -m venv venv

# Ativa virtual environment
print_info "Ativando virtual environment..."
source venv/bin/activate

# Atualiza pip
print_info "Atualizando pip..."
pip install --upgrade pip setuptools wheel

# Instala dependências
print_info "Instalando dependências..."
pip install -e ".[dev]"

# Configura pre-commit hooks
print_info "Configurando pre-commit hooks..."
pre-commit install
pre-commit autoupdate

# Cria arquivo .env
if [ ! -f ".env" ]; then
print_info "Criando arquivo .env..."
cp .env.example .env
print_info "Por favor, configure as variáveis no arquivo .env"
fi

# Cria diretórios necessários
print_info "Criando diretórios..."
mkdir -p logs tests/reports

# Executa testes iniciais
print_info "Executando testes iniciais..."
pytest tests/unit/ -v

print_msg "🎉 Ambiente configurado com sucesso!"
print_msg "Para ativar o ambiente: source venv/bin/activate"
print_msg "Para executar testes: ./scripts/run_tests.sh"
print_msg "Para iniciar a aplicação: docker-compose up"