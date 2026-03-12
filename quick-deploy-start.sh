#!/bin/bash

# 🚀 VEXUS SERVICE - QUICK DEPLOY STARTER
# Script interativo para começar deployment

set -e

clear

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║                   🚀 VEXUS CRM - DEPLOYMENT RÁPIDO                          ║"
echo "║                                                                              ║"
echo "║              Seu sistema será lançado em 3 DIAS - Começamos AGORA!          ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step counter
STEP=1

step() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}[PASSO $STEP]${NC} $1"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    STEP=$((STEP+1))
}

success() {
    echo -e "${GREEN}✅${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠️ ${NC} $1"
}

info() {
    echo -e "${BLUE}ℹ️ ${NC} $1"
}

# STEP 1: Apresentação
step "PRÉ-DEPLOYMENT - VERIFICAÇÕES INICIAIS"
echo ""
echo "Sistema: Vexus Service (3 módulos)"
echo "├─ Vexus Core (Fase 1)"
echo "├─ Vexus Hub (Fases 2-3)"
echo "└─ Vexus CRM Agêntico (Fase 4 MVP)"
echo ""
echo "Funcionalidades:"
echo "├─ 7 AI Agents"
echo "├─ Visual Flow Builder"
echo "├─ Visual Pipeline"
echo "├─ Omnichannel (7 canais)"
echo "└─ 81 Funções + 20 BD Models"
echo ""

read -p "Pressione ENTER para continuar..." confirm

# STEP 2: Validar sistema
step "VALIDANDO SISTEMA"
echo ""

if command -v python3 &> /dev/null; then
    success "Python 3 instalado: $(python3 --version)"
else
    echo -e "${RED}❌${NC} Python 3 não encontrado"
    exit 1
fi

if command -v docker &> /dev/null; then
    success "Docker instalado: $(docker --version | cut -d' ' -f3 | tr -d ',')"
else
    echo -e "${RED}❌${NC} Docker não encontrado"
    exit 1
fi

if command -v git &> /dev/null; then
    success "Git instalado"
else
    echo -e "${RED}❌${NC} Git não encontrado"
    exit 1
fi

success "Todos os pré-requisitos OK"
echo ""
read -p "Pressione ENTER para continuar..." confirm

# STEP 3: Escolher cloud provider
step "ESCOLHER CLOUD PROVIDER"
echo ""
echo "Opções:"
echo "  1) DigitalOcean App Platform (RECOMENDADO - $50/mês, 15 min setup)"
echo "  2) Railway.app (Rápido - 10 min setup, custo flexível)"
echo "  3) AWS ECS (Poderoso - 2h setup, $200+/mês)"
echo "  4) Pular esta etapa (configurar depois)"
echo ""
read -p "Escolha uma opção (1-4): " cloud_choice

case $cloud_choice in
    1)
        info "DigitalOcean App Platform escolhido"
        info "Próximos passos:"
        echo "  1. Abra: https://www.digitalocean.com"
        echo "  2. Faça signup ou login"
        echo "  3. Vá para App Platform"
        echo "  4. Clique 'Create App'"
        echo "  5. Conecte seu repositório GitHub"
        echo "  6. Configure variáveis de ambiente"
        echo "  7. Deploy!"
        echo ""
        warning "Anote sua DATABASE_URL e REDIS_URL após criar os serviços"
        ;;
    2)
        info "Railway.app escolhido"
        info "Próximos passos:"
        echo "  1. Abra: https://railway.app"
        echo "  2. Faça login com GitHub"
        echo "  3. Clique 'Create New Project'"
        echo "  4. Selecione 'Deploy from GitHub repo'"
        echo "  5. Escolha este repositório"
        echo "  6. Configure variáveis de ambiente"
        echo "  7. Deploy automático!"
        echo ""
        warning "Railway é mais rápido para MVP"
        ;;
    3)
        info "AWS ECS escolhido"
        warning "AWS requer mais configuração. Recomendamos DigitalOcean para MVP"
        info "Documentação: Ver DEPLOYMENT_ROADMAP.md seção AWS"
        ;;
    4)
        info "OK, você configurará depois"
        ;;
esac

echo ""
read -p "Pressione ENTER para continuar..." confirm

# STEP 4: API Keys
step "GERAR API KEYS"
echo ""
echo "Você precisa gerar as seguintes chaves:"
echo ""
echo "🔑 OBRIGATÓRIAS:"
echo "  1. OpenAI API Key"
echo "     └─ Ir para: https://platform.openai.com/api/keys"
echo "     └─ Criar nova chave"
echo "     └─ Copiar valor (começa com sk-proj-)"
echo ""
echo "  2. WhatsApp Business API Key"
echo "     └─ Ir para: https://business.facebook.com"
echo "     └─ Criar app WhatsApp"
echo "     └─ Copiar: API Key e Phone Number ID"
echo ""
echo "📧 OPCIONAIS:"
echo "  3. SendGrid API Key (para email)"
echo "  4. Twilio Keys (para SMS)"
echo "  5. Meta/Instagram Keys (para Instagram)"
echo ""
warning "Tempo estimado: 20 minutos"
echo ""
read -p "Pressione ENTER para continuar..." confirm

# STEP 5: Variáveis de Ambiente
step "CONFIGURAR VARIÁVEIS DE AMBIENTE"
echo ""

if [ -f ".env.production" ]; then
    warning ".env.production já existe"
    read -p "Deseja sobrescrever? (s/n): " overwrite
    if [ "$overwrite" == "s" ]; then
        cp .env.production.example .env.production
        success "Arquivo .env.production criado"
    fi
else
    cp .env.production.example .env.production
    success "Arquivo .env.production criado a partir do template"
fi

echo ""
echo "Próximos passos:"
echo "  1. Abra o arquivo: .env.production"
echo "  2. Preencha os valores:"
echo "     - OPENAI_API_KEY"
echo "     - WHATSAPP_BUSINESS_API_KEY"
echo "     - WHATSAPP_PHONE_NUMBER_ID"
echo "     - DATABASE_URL (após criar DB no cloud)"
echo "     - REDIS_URL (após criar Redis no cloud)"
echo "     - Outras opcionais"
echo ""
warning "NUNCA fazer commit de .env.production!"
warning "Usar GitHub Secrets para valores sensíveis em CI/CD"
echo ""
read -p "Pressione ENTER para continuar..." confirm

# STEP 6: Próximos passos
step "PRÓXIMOS PASSOS"
echo ""
echo "Você completou a FASE 1 do Quick Deploy! 🎉"
echo ""
echo "Timeline para go-live:"
echo "  🟢 HOJE (5 fev):     Setup infraestrutura (2h)"
echo "  🟡 AMANHÃ (6 fev):   Deploy staging (2h)"
echo "  🔴 SEXTA (7 fev):    Deploy produção (1h)"
echo ""
echo "Checklist para completar hoje:"
echo "  [ ] Escolher cloud provider"
echo "  [ ] Criar conta"
echo "  [ ] Gerar API keys"
echo "  [ ] Preencher .env.production"
echo "  [ ] Criar PostgreSQL gerenciado"
echo "  [ ] Criar Redis gerenciado"
echo "  [ ] Conectar repositório GitHub"
echo ""
echo "Arquivos importantes:"
echo "  📄 QUICK_DEPLOY.md          - Checklist detalhado"
echo "  📄 DEPLOYMENT_ROADMAP.md    - Guia completo"
echo "  📄 DEPLOYMENT_CHECKLIST.md  - Progresso do seu deployment"
echo "  📄 .env.production.example  - Template de variáveis"
echo ""
info "Salvar este arquivo: DEPLOYMENT_CHECKLIST.md para acompanhar progresso"
echo ""

# STEP 7: Confirmação final
step "PRONTO PARA COMEÇAR?"
echo ""
echo -e "${GREEN}✅${NC} Sistema validado"
echo -e "${GREEN}✅${NC} Documentação preparada"
echo -e "${GREEN}✅${NC} Template de configuração criado"
echo ""
echo -e "${YELLOW}Próxima ação:${NC}"
echo "  1. Abrir .env.production e preencher chaves"
echo "  2. Criar conta no cloud provider escolhido"
echo "  3. Seguir QUICK_DEPLOY.md para infraestrutura"
echo ""
read -p "Pressione ENTER para finalizar..." confirm

clear
echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║                      ✅ QUICK DEPLOY INICIADO!                              ║"
echo "║                                                                              ║"
echo "║         Seu CRM Production-Ready está pronto para conquistar o mercado!      ║"
echo "║                                                                              ║"
echo "║                    🚀 BORA LANÇAR! 🚀 (em 3 dias)                           ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Referências rápidas:"
echo "  • QUICK_DEPLOY.md - Leia isso agora!"
echo "  • DEPLOYMENT_CHECKLIST.md - Acompanhe progresso"
echo "  • .env.production - Preencha com seus valores"
echo ""
echo "Contato de suporte:"
echo "  📧 victor@vexus.com.br"
echo "  📋 Documentação: DEPLOYMENT_ROADMAP.md"
echo ""

exit 0
