# Guia Técnico - Sistema de Cadastro Multi-Etapas

---

## 📐 Arquitetura

### Estrutura de Dados

```javascript
// Estado Global
let currentSignupStep = 1;          // Etapa atual (1-4)
const totalSignupSteps = 4;          // Total de etapas

// Configuração por Indústria
const industryAdaptations = {
  'vendas': {
    label: 'Vendas e E-commerce',
    features: ['pipeline', 'proposals', 'campaigns', 'contacts'],
    channels: ['whatsapp', 'email', 'instagram']
  },
  // ... mais indústrias
}
```

---

## 🔄 Funções Principais

### 1. **goToSignupStep(step)**
Navega diretamente para uma etapa específica.

```javascript
goToSignupStep(2);  // Vai para etapa 2
```

---

### 2. **nextSignupStep()**
Valida etapa atual e avança.

```javascript
nextSignupStep();
// 1. Valida currentSignupStep
// 2. Se válido, incrementa
// 3. Atualiza UI
```

---

### 3. **prevSignupStep()**
Volta uma etapa (sem validação).

```javascript
prevSignupStep();
// Decrementa etapa e atualiza UI
```

---

### 4. **validateCurrentSignupStep()**
Valida todos os campos da etapa atual.

```javascript
if (validateCurrentSignupStep()) {
  // Etapa válida, pode avançar
}
```

**Retorna**: `true` se válido, ou exibe erro e retorna `false`.

---

### 5. **updateSignupUI()**
Atualiza a interface conforme a etapa.

```javascript
updateSignupUI();
// - Atualiza indicadores
// - Atualiza barra de progresso
// - Mostra/oculta etapas
// - Atualiza botões
```

**O que altera:**
- Classe `active` no indicador atual
- Classe `completed` nos anteriores
- Largura da `.step-progress`
- Visibilidade das `.signup-step` (add/remove `hidden`)
- Estados dos botões Anterior/Próximo/Enviar

---

### 6. **setupSignupStepListeners()**
Configura todos os event listeners do formulário.

```javascript
setupSignupStepListeners();
// Adiciona listeners a:
// - Botão Anterior
// - Botão Próximo
// - Seleção de Planos
// - Seleção de Indústria
```

---

### 7. **handleSignup(e)**
Função final que submete o formulário.

```javascript
handleSignup(e);
// 1. Valida etapa 4
// 2. Coleta dados de todas as etapas
// 3. POST /api/auth/register
// 4. Salva dados em localStorage
// 5. Redireciona ao dashboard
```

---

## 📝 Fluxo Completo de Validação

```
User clica "Próximo"
    ↓
nextSignupStep() é chamada
    ↓
validateCurrentSignupStep()
    ├─ Se ETAPA 1:
    │  ├─ Valida nome (não vazio)
    │  ├─ Valida email (formato válido)
    │  ├─ Valida senha (min 6 chars)
    │  └─ Valida confirmação de senha
    │
    ├─ Se ETAPA 2:
    │  ├─ Valida empresa (não vazio)
    │  ├─ Valida indústria (selecionada)
    │  └─ Valida tamanho (selecionado)
    │
    ├─ Se ETAPA 3:
    │  └─ Valida forma de pagamento (selecionada)
    │
    └─ Se ETAPA 4:
       └─ Valida plano (selecionado)
    ↓
if (válido) {
    currentSignupStep++
    updateSignupUI()
} else {
    Mostra mensagem de erro
}
```

---

## 🎨 Estrutura HTML

### Indicador de Etapas
```html
<div class="step-indicator active" data-step="1">
  <div class="step-circle">1</div>
  <p class="step-label">Dados Pessoais</p>
</div>
```

**Classes dinâmicas:**
- `.active` - Etapa atual (roxo/rosa)
- `.completed` - Etapa completa (verde)
- (sem classe) - Etapa não visitada (cinza)

---

### Etapas do Formulário
```html
<div class="signup-step" data-step="1">
  <!-- Conteúdo da etapa 1 -->
</div>

<div class="signup-step hidden" data-step="2">
  <!-- Conteúdo da etapa 2 -->
</div>
```

**Classe dinâmica:** `.hidden` (display: none)

---

### Seleção de Planos
```html
<div class="plan-card" data-plan="professional">
  <!-- Plano Professional -->
  <input type="radio" name="selected-plan" 
         value="professional" class="hidden plan-radio">
</div>
```

**Click Handler:**
```javascript
.plan-card.addEventListener('click', function() {
  document.querySelectorAll('.plan-card').forEach(c => 
    c.classList.remove('selected')
  );
  this.classList.add('selected');
  this.querySelector('.plan-radio').checked = true;
});
```

---

## 🔐 Integração com Backend

### POST /api/auth/register

**Request:**
```json
{
  "email": "joao@empresa.com",
  "password": "senha123",
  "full_name": "João Silva"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "email": "joao@empresa.com",
  "name": "João Silva"
}
```

**Implementação:**
```javascript
const response = await fetch('/api/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    email, 
    password, 
    full_name: name 
  }),
  credentials: 'include'  // HttpOnly cookies
});
```

---

## 💾 localStorage Keys

Após cadastro bem-sucedido, estes dados são salvos:

| Key | Tipo | Obrigatório | Descrição |
|-----|------|-------------|-----------|
| `user_name` | String | ✅ | Nome do usuário |
| `user_email` | String | ✅ | Email login |
| `user_phone` | String | ❌ | Telefone de contato |
| `user_role` | String | ❌ | Cargo/posição |
| `company_name` | String | ✅ | Nome da empresa |
| `company_industry` | String | ✅ | Setor/indústria |
| `company_size` | String | ✅ | Tamanho empresa |
| `company_website` | String | ❌ | Website |
| `company_cnpj` | String | ❌ | CNPJ |
| `payment_method` | String | ✅ | Forma pagamento |
| `user_plan` | String | ✅ | Plano selecionado |

---

## 🎯 Adaptação por Indústria

### Como Funciona

**1. Usuário seleciona indústria:**
```javascript
const industrySelect = document.getElementById('signup-industry');
industrySelect.addEventListener('change', function() {
  const industry = this.value;
  const config = industryAdaptations[industry];
  localStorage.setItem('company_industry', industry);
});
```

**2. Sistema salva seleção:**
```
localStorage.company_industry = 'vendas'  // ou qualquer outro
```

**3. Dashboard carrega features customizadas:**
```javascript
// Após login
const industry = localStorage.getItem('company_industry');
const config = industryAdaptations[industry];
// Carregar features conforme config.features
// Ativar canais conforme config.channels
```

---

## 📧 Exemplo: Integração com Email

### Adaptar por Indústria

```javascript
// industryAdaptations.js
const industryAdaptations = {
  'marketing': {
    emailTemplates: [
      'campanha_newsletter',
      'ab_testing',
      'follow_up_cliente'
    ],
    defaultVariables: {
      'nome_campanha': 'Nova Campanha',
      'audiencia_alvo': '5000 contatos'
    }
  },
  'vendas': {
    emailTemplates: [
      'follow_up_vendas',
      'proposta_seguimento',
      'agradecimento_compra'
    ],
    defaultVariables: {
      'valor_proposta': 'R$ 0,00',
      'prazo_resposta': '7 dias'
    }
  }
};
```

---

## 🚀 Implementação de Nova Indústria

### Passo 1: Adicionar à Config
```javascript
const industryAdaptations = {
  'nova_industria': {
    label: 'Nome Indústria',
    features: ['feature1', 'feature2'],
    channels: ['whatsapp', 'email']
  }
};
```

### Passo 2: Adicionar Option no Select
```html
<select id="signup-industry">
  <!-- ... outras opções ... -->
  <option value="nova_industria">
    🎯 Nome Indústria
  </option>
</select>
```

### Passo 3: Criar Dashboard Customizado
```javascript
function loadDashboardForIndustry(industry) {
  const config = industryAdaptations[industry];
  if (!config) return;
  
  // Carregar features
  config.features.forEach(feature => {
    // Ativar widget para feature
  });
}
```

---

## 🧪 Teste de Fluxo Completo

### Script de Teste
```javascript
// Abrir console e rodar:

// 1. Preencher etapa 1
document.getElementById('signup-name').value = 'João';
document.getElementById('signup-email').value = 'joao@test.com';
document.getElementById('signup-password').value = '123456';
document.getElementById('signup-confirm').value = '123456';
nextSignupStep();  // → Etapa 2

// 2. Preencher etapa 2
document.getElementById('signup-company').value = 'Empresa Ltda';
document.getElementById('signup-industry').value = 'vendas';
document.getElementById('signup-size').value = '11-50';
nextSignupStep();  // → Etapa 3

// 3. Etapa 3 (pagamento)
document.querySelector('input[name="payment-method"]').checked = true;
nextSignupStep();  // → Etapa 4

// 4. Etapa 4 (plano)
document.querySelector('input[name="selected-plan"]').checked = true;

// 5. Enviar
document.getElementById('signup-form').submit();
```

---

## 🐛 Debug

### Verificar Estado Atual
```javascript
console.log('Etapa atual:', currentSignupStep);
console.log('Total:', totalSignupSteps);
console.log('Dados:', {
  name: document.getElementById('signup-name').value,
  email: document.getElementById('signup-email').value,
  industry: document.getElementById('signup-industry').value,
  plan: document.querySelector('input[name="selected-plan"]:checked')?.value
});
```

### Resetar Formulário
```javascript
document.getElementById('signup-form').reset();
currentSignupStep = 1;
updateSignupUI();
```

---

## ⚡ Performance

### Otimizações Aplicadas

1. **Event Delegation** - Listeners no container principal
2. **classList vs className** - Mais rápido para múltiplas classes
3. **Lazy Loading** - Etapas ocultas não renderizam
4. **Validação Local** - Antes de chamar API
5. **sessionStorage** - Para dados temporários (se necessário)

---

## 🔒 Segurança

### O que NÃO ir para localStorage

❌ Token
❌ Senha
❌ API Keys
❌ Secrets
❌ PII sensível

### O que PODE ir para localStorage

✅ Preferências de UI
✅ ID da empresa
✅ Nome de usuário (público)
✅ Email (público)
✅ Plano selecionado

---

## 📚 Referências

- [localStorage MDN](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage)
- [Form Validation](https://developer.mozilla.org/en-US/docs/Learn/Forms/Form_validation)
- [Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)

---

**Desenvolvido com ❤️ para Vexus CRM**
