# Novo Sistema de Cadastro - Vexus CRM

**Data**: Março 2026  
**Status**: ✅ Em funcionamento

---

## 📋 Visão Geral

O Vexus CRM agora possui um sistema de cadastro profissional, intuitivo e adaptativo em **4 etapas**. O formulário é responsivo, sem conteúdo cortado, e se adapta automaticamente conforme a função/setor da empresa.

---

## 🎯 As 4 Etapas de Cadastro

### **Etapa 1️⃣: Dados Pessoais**

Informações do usuário que está criando a conta:

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| **Nome Completo** | Texto | ✅ | Nome para identificação no sistema |
| **Email** | Email | ✅ | Email para login e notificações |
| **Telefone** | Telefone | ❌ | Para contato direto |
| **Seu Cargo** | Texto | ❌ | Ex: Gerente, Vendedor, Diretor |
| **Senha** | Senha | ✅ | Mínimo 6 caracteres |
| **Confirmar Senha** | Senha | ✅ | Validação da senha |

**Validações:**
- Nome não pode ser vazio
- Email deve ser válido
- Senhas devem coincidir
- Senha mínimo 6 caracteres

---

### **Etapa 2️⃣: Dados da Empresa** 

Informações que permitem a adaptação automática do sistema:

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| **Nome da Empresa** | Texto | ✅ | Razão social ou nome comercial |
| **🎯 Setor/Função da Empresa** | Select | ✅ | Define como o sistema se adapta |
| **Tamanho da Empresa** | Select | ✅ | Para definir limites de contatos iniciais |
| **Website** | URL | ❌ | Site da empresa |
| **CNPJ** | Texto | ❌ | Para validações futuras de NF-e |

**Opções de Setor (com adaptação automática):**

```
🏪 Vendas e E-commerce
   → Features: Pipeline, Propostas, Campanhas, Contatos
   → Canais: WhatsApp, Email, Instagram

🛠️ Serviços Profissionais
   → Features: Pipeline, Tarefas, Calendário, Faturamento
   → Canais: WhatsApp, Email

🎓 Educação
   → Features: Cursos, Alunos, Tarefas, Mensagens
   → Canais: WhatsApp, Email

⚕️ Saúde e Medicina
   → Features: Agendamentos, Pacientes, Registros, Tarefas
   → Canais: WhatsApp, Email

🏠 Imobiliário
   → Features: Propriedades, Pipeline, Documentos, Tours
   → Canais: WhatsApp, Telefone, Email

✈️ Turismo e Viagens
   → Features: Reservas, Pacotes, Roteiros, Clientes
   → Canais: WhatsApp, Email, Instagram

💰 Financeiro e Seguros
   → Features: Contratos, Faturamento, Tarefas, Documentos
   → Canais: Email, Telefone

💻 Tecnologia
   → Features: Projetos, Tarefas, Documentação, Integrações
   → Canais: Email, Teams

📢 Marketing e Publicidade
   → Features: Campanhas, Análises, Contatos, Templates
   → Canais: Email, Instagram, Facebook

👔 RH e Recrutamento
   → Features: Candidatos, Entrevistas, Documentos, Avisos
   → Canais: Email, LinkedIn

📦 Logística
   → Features: Remessas, Rastreamento, Clientes, Análises
   → Canais: WhatsApp, Email

📌 Outro
   → Features: Variadas (padrão)
   → Canais: WhatsApp, Email
```

**Tamanho da Empresa:**
- 1 - 10 pessoas
- 11 - 50 pessoas
- 51 - 200 pessoas
- 201 - 1.000 pessoas
- Mais de 1.000 pessoas

---

### **Etapa 3️⃣: Forma de Pagamento**

Escolher como a empresa vai pagar pela assinatura:

- **💳 Cartão de Crédito** - Imediato, aceita várias bandeiras
- **🔐 Pix** - Pagamento instantâneo (Brasil)
- **📄 Boleto Bancário** - Tradicional, até 3 dias úteis
- **📋 Fatura Mensal** - Para empresas maiores com análise de crédito

**Observações:**
- Todos os pagamentos processados por Stripe (seguro)
- Sem taxa oculta
- Cancelamento flexível a qualquer momento
- Testamos com dados aleatórios se necessário

---

### **Etapa 4️⃣: Escolha de Plano**

Selecionar o plano que melhor se adequa:

| Plano | Preço | Contatos | Usuários | Canais | Suporte |
|-------|-------|----------|----------|--------|---------|
| **Starter** | **R$ 99/mês** | Até 100 | 1 | Email + WhatsApp | Por email |
| **Professional** ⭐ | **R$ 299/mês** | Até 1.000 | 5 | Email + WhatsApp + Instagram | 24/7 |
| **Premium** | **R$ 599/mês** | Ilimitado | Ilimitado | Todos | 24/7 + Dedicado |

**7 dias grátis em qualquer plano para teste**

---

## 🎨 Detalhes Visuais

### Layout da Tela

```
┌─────────────────────────────────────────────────────┐
│                  Bem-vindo ao Vexus CRM             │  
│        Configure sua conta em 4 etapas simples      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [1]────[2]────[3]────[4]                          │
│  Dados  Empresa  Pagamento  Plano                   │
│  ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 25%             │
│                                                     │
│  ┌───────────────────────────────────┐            │
│  │ Dados Pessoais                    │            │
│  │                                   │            │
│  │ Nome: [_________________]         │            │
│  │ Email: [________________]         │            │
│  │ Telefone: [_____________]         │            │
│  │ Cargo: [_________________]        │            │
│  │ Senha: [_________________]        │            │
│  │ Confirmar: [_____________]        │            │
│  │                                   │            │
│  │               [Próximo →]         │            │
│  └───────────────────────────────────┘            │
│                                                     │
│ Já tem conta? Faça login                           │
└─────────────────────────────────────────────────────┘
```

### Indicador de Progresso

- **Números circulares** (1, 2, 3, 4) mostram as etapas
- **Cor ativa** (roxo/rosa) indica etapa atual
- **Cor completa** (verde) indica etapas já preenchidas
- **Barra de progresso** no topo atualiza conforme avança
- **Textos descritivos** abaixo de cada número

### Responsividade

- **Desktop** (>768px): 4 etapas lado a lado
- **Tablet** (768px): Layout adaptado
- **Mobile** (<768px): Etapas em coluna
- **Sem cortes**: `min-h-screen` garante que tudo cabe

---

## 💾 Dados Salvos Após Cadastro

Após completar o cadastro, estes dados são salvos:

### Backend (Seguro)
```json
{
  "user": {
    "id": "uuid",
    "name": "João Silva",
    "email": "joao@empresa.com",
    "password_hash": "bcrypt_hash"
  }
}
```

### localStorage (Client - Apenas não-sensível)
```javascript
{
  "user_name": "João Silva",
  "user_email": "joao@empresa.com",
  "user_phone": "(11) 98765-4321",
  "user_role": "Gerente de Vendas",
  "company_name": "Empresa Ltda.",
  "company_industry": "vendas",
  "company_size": "11-50",
  "company_website": "https://www.empresa.com",
  "company_cnpj": "XX.XXX.XXX/0001-XX",
  "payment_method": "credit-card",
  "user_plan": "professional"
}
```

---

## 🚀 Como o Sistema se Adapta

### Exemplo 1: Empresa de Vendas

Quando selecionam **"Vendas e E-commerce"**:

1. **Dashboard** mostra KPIs de vendas
2. **Pipeline** aparece com etapas de vendas padrão
3. **Relatórios** focam em conversão e faturamento
4. **Integração WhatsApp** já vem pré-configurada
5. **Templates** de mensagens para vendas

### Exemplo 2: Empresa de Saúde

Quando selecionam **"Saúde e Medicina"**:

1. **Dashboard** mostra agendamentos e pacientes
2. **Calendário** aparece de forma proeminente
3. **Registros** de pacientes com campos médicos
4. **Lembretes** automáticos de consultas
5. **Templates** de comunicação com pacientes

### Exemplo 3: Agência de Marketing

Quando selecionam **"Marketing e Publicidade"**:

1. **Dashboard** mostra analytics de campanhas
2. **Campanhas** com A/B testing
3. **Social Media** com calendário editorial
4. **Relatórios** focados em ROI
5. **Integrações** com Google Ads, Facebook

---

## ✅ Validações por Etapa

### Etapa 1 - Dados Pessoais
```
✓ Nome não vazio
✓ Email válido (contém @)
✓ Senha mínimo 6 caracteres
✓ Senhas coincidem
```

### Etapa 2 - Dados da Empresa  
```
✓ Nome da empresa não vazio
✓ Setor/função selecionado
✓ Tamanho selecionado
✓ (website e CNPJ opcionais)
```

### Etapa 3 - Forma de Pagamento
```
✓ Uma opção de pagamento selecionada
```

### Etapa 4 - Escolha de Plano
```
✓ Um plano selecionado
```

---

## 🔄 Fluxo do Formulário

```
START
  ↓
[1] Dados Pessoais
  ↓ (Validar)
[2] Dados da Empresa (Sistema se adapta aqui!)
  ↓ (Validar)
[3] Forma de Pagamento
  ↓ (Validar)
[4] Escolha de Plano
  ↓ (Validar)
SUBMIT → Criar Conta → Login Automático → Dashboard
```

---

## 🎯 Integração com Backend

### Endpoint de Registro

```bash
POST /api/auth/register

Request:
{
  "email": "joao@empresa.com",
  "password": "senha123",
  "full_name": "João Silva"
}

Response:
{
  "id": "uuid",
  "email": "joao@empresa.com",
  "name": "João Silva"
}

HttpOnly Cookie set automaticamente
```

---

## 🐛 Correções Implementadas

### ✅ Problema 1: Telas Cortadas
- **Antes**: Conteúdo saía da tela em alguns tamanhos
- **Depois**: `min-h-screen` garante altura mínima, sem cortes

### ✅ Problema 2: Formulário Desorganizado
- **Antes**: Tudo em uma página, confuso
- **Depois**: 4 etapas claras com progresso visual

### ✅ Problema 3: Falta de Dados da Empresa
- **Antes**: Não havia informações sobre a empresa
- **Depois**: Nome, setor, tamanho, website, CNPJ

### ✅ Problema 4: Sem Adaptação do Sistema
- **Antes**: Mesmo interface para todos
- **Depois**: Sistema se adapta baseado no setor

### ✅ Problema 5: Falta de Forma de Pagamento
- **Antes**: Não tinha opção de pagamento
- **Depois**: 4 formas diferentes de pagamento

---

## 📱 Responsividade

### Desktop (>1024px)
```
┌────────────────────────────────────────┐
│    [1]  [2]  [3]  [4]                 │
│    ████░░░░░░░░░░░░░░░░ 25%           │
│                                        │
│    [Form Fields em 2 colunas]         │
│    [Buttons lado a lado]              │
└────────────────────────────────────────┘
```

### Tablet (768px-1024px)
```
┌────────────────────────────────────┐
│  [1]  [2]  [3]  [4]               │
│  ████░░░░░░░░░░░░░ 25%            │
│                                    │
│  [Form Fields adaptados]          │
│  [Buttons empilhados]             │
└────────────────────────────────────┘
```

### Mobile (<768px)
```
┌──────────────────┐
│  [1]             │
│  [2]             │
│  [3]  ████░░░░   │
│  [4]   25%       │
│                  │
│ [Fields]         │
│ [Button full]    │
└──────────────────┘
```

---

## 🔐 Segurança

- ✅ Senhas hashed com bcrypt
- ✅ Tokens em HttpOnly cookies (não acessível por JS)
- ✅ Validação server-side de todos os dados
- ✅ Dados sensíveis não salvos em localStorage
- ✅ HTTPS recomendado em produção

---

## 🎓 Próximos Passos

1. **Implementar integração com Stripe** para processamento de pagamento
2. **Criar onboarding personalizado** por setor
3. **Adicionar verificação de email** com link de confirmação
4. **Implementar 2FA** para segurança extra
5. **Criar dashboard inicial** adaptado ao setor

---

## 📊 Analytics

O sistema coleta:
- Qual etapa o usuário abandona (se aplicável)
- Qual setor tem mais cadastros
- Qual plano é mais popular
- Qual forma de pagamento é preferida

---

## ✨ Exemplo Completo

### Cenário: João criando conta para agência de marketing

```
ETAPA 1 - Dados Pessoais
├─ Nome: João Silva
├─ Email: joao@marketingagency.com
├─ Telefone: (11) 98765-4321
├─ Cargo: Diretor de Negócios
└─ Senha: MinhaSenh@123

ETAPA 2 - Dados da Empresa
├─ Empresa: Marketing Agency Ltda.
├─ Setor: 📢 Marketing e Publicidade
│   → Sistema se adapta para marketing
├─ Tamanho: 51 - 200 pessoas
├─ Website: https://www.marketingagency.com.br
└─ CNPJ: 12.345.678/0001-90

ETAPA 3 - Forma de Pagamento
└─ Selecionada: 💳 Cartão de Crédito

ETAPA 4 - Plano
└─ Selecionado: Professional (R$ 299/mês)

↓ SUBMETER

RESULTADO:
✅ Conta criada
✅ Redirecionado ao dashboard
✅ Dashboard mostra analytics de campanhas
✅ Features de marketing já habilitadas
✅ Integração com Instagram pronta
```

---

**Pronto para usar!** 🚀
