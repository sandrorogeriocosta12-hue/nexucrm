# 🧪 Guia Rápido de Teste - Novo Cadastro

## ✅ Verificar Tudo em 2 Minutos

### 1. Servidor Rodando?
```bash
curl http://localhost:8000/frontend/app.html | grep "signup-screen" | head -1
```

Se ver isso = ✅ OK:
```html
<div id="signup-screen" class="hidden flex items-center justify-center min-h-screen
```

### 2. Abrir o Cadastro
```
http://localhost:8000/frontend/app.html
```

Depois clique: **"Criar Conta"**

---

## 🎯 Teste Manual (Passo a Passo)

### Etapa 1: Dados Pessoais ✅
```
✓ Nome: João Silva
✓ Email: joao@exemple.com
✓ Telefone: (11) 99999-8888 (opcional)
✓ Cargo: Gerente de Vendas (opcional)
✓ Senha: Senha@123
✓ Confirmar Senha: Senha@123

Depois: Clique "Próximo"
```

✅ **Validação esperada:**
- Se senha < 6 chars → erro "Mínimo 6 caracteres"
- Se senhas diferentes → erro "As senhas não coincidem"
- Se email inválido → erro "Email inválido"

---

### Etapa 2: Dados da Empresa ✅
```
✓ Empresa: Vendas LTDA
✓ Setor: Vendas e E-commerce ← **IMPORTANTE**: Selecione um
✓ Tamanho: 10-50 pessoas (ou outra)
✓ Website: vendas.com.br (opcional)
✓ CNPJ: 12.345.678/0001-00 (opcional)

Depois: Clique "Próximo"
```

✅ **Validação esperada:**
- Se empresa vazia → erro "Nome da empresa obrigatório"
- Se não selecionar setor → erro "Selecione um setor"
- Se tamanho não selecionado → erro "Selecione o tamanho"

**IMPORTANTE**: Observe se o formulário mudou visuamente quando selecionou o setor (fundo, cores, etc)

---

### Etapa 3: Forma de Pagamento ✅
```
Escolha uma (eles são clicáveis):
○ Cartão de Crédito
○ Pix
● Boleto Bancário  ← Selecionado
○ Fatura Mensal

Depois: Clique "Próximo"
```

✅ **Validação esperada:**
- Se não selecionar nada → erro "Selecione uma forma de pagamento"
- O circulozinho fica preenchido quando clica

---

### Etapa 4: Plano ✅
```
╔════════════════════════════════════╗
║  Starter          Professional    Premium  ║
║  R$ 99/mês    ✓ R$ 299/mês    R$ 599/mês║
║  10 contatos     100 contatos   Ilimitado ║
║  ────────────────────────────────────╗
║       [Finalizar Cadastro]          ║
╚════════════════════════════════════╝
```

Clique no card de plano (muda cor) depois:

**Clique: "✓ Finalizar Cadastro"**

---

## 🔍 Verificações Visuais

### ✅ Layout Responsivo
- [ ] Nenhum conteúdo cortado lateralmente
- [ ] Botões completamente visíveis
- [ ] Campos de texto cabem na tela
- [ ] Títulos legíveis
- [ ] Espaçamento consistente

### ✅ Indicadores de Progresso
```
[1]  [2]  [3]  [4]
███░░░░░░░░░░░░░░░░ 25%
```

- [ ] Números e círculos aparecem
- [ ] Progress bar funciona (aumenta de 25% → 50% → 75% → 100%)
- [ ] Cores mudam (roxo = ativo, cinza = não visitado, verde = completo)

### ✅ Validação
```
Nome: [________]
Email: [________]
Senha: [________]

Clique Próximo SEM preencher
↓
Deve aparecer: "Nome obrigatório"
```

- [ ] Mensagens de erro aparecem
- [ ] Mensagens são claras
- [ ] Cores de erro são visíveis (geralmente vermelho)

### ✅ Navegação
- [ ] "Próximo" só funciona quando preenche
- [ ] "Anterior" volta sem perder dados
- [ ] Último botão diz "Finalizar Cadastro"
- [ ] Botões desabilitados aparecem cinzas

---

## 🚀 Teste Automático (Console)

### Script para Preencher Tudo
Abra o Console do navegador (F12) e cole:

```javascript
// Etapa 1 - Dados Pessoais
document.getElementById('signup-fullname').value = 'João Silva';
document.getElementById('signup-email').value = 'joao@teste.com';
document.getElementById('signup-phone').value = '(11) 99999-8888';
document.getElementById('signup-role').value = 'Vendedor';
document.getElementById('signup-password').value = 'Senha@123';
document.getElementById('signup-confirm').value = 'Senha@123';

// Simular clique em "Próximo"
document.querySelector('[data-step="1"] .next-btn')?.click();

// Aguardar 500ms
setTimeout(() => {
  // Etapa 2 - Dados da Empresa
  document.getElementById('signup-company').value = 'Empresa LTDA';
  document.getElementById('signup-industry').value = 'vendas';
  document.getElementById('signup-size').value = '10-50';
  document.getElementById('signup-website').value = 'empresa.com.br';
  document.getElementById('signup-cnpj').value = '12.345.678/0001-00';
  
  // Simular clique em "Próximo"
  document.querySelector('[data-step="2"] .next-btn')?.click();
}, 500);

// Aguardar 500ms
setTimeout(() => {
  // Etapa 3 - Forma de Pagamento
  document.getElementById('payment-pix').checked = true;
  document.getElementById('payment-pix').dispatchEvent(new Event('change', { bubbles: true }));
  
  // Simular clique em "Próximo"
  document.querySelector('[data-step="3"] .next-btn')?.click();
}, 1000);

// Aguardar 500ms
setTimeout(() => {
  // Etapa 4 - Plano
  document.querySelector('[data-plan="professional"]')?.click();
  
  // Tudo pronto para submeter
  console.log('✅ Todos os campos preenchidos!');
  console.log('Dados em localStorage:', localStorage);
}, 1500);
```

**Resultado esperado:**
```
✅ Todos os campos preenchidos!
Dados em localStorage: Storage {
  signup_email: 'joao@teste.com',
  signup_company: 'Empresa LTDA',
  signup_industry: 'vendas',
  signup_plan: 'professional',
  ...
}
```

---

## 🐛 Debug

### Ver dados salvos no localStorage
```javascript
// No console:
localStorage

// Ou mais detalhado:
Object.keys(localStorage).forEach(key => {
  console.log(`${key}: ${localStorage.getItem(key)}`);
});
```

**Dados esperados:**
```
signup_email: joao@teste.com
signup_fullname: João Silva
signup_company: Empresa LTDA
signup_industry: vendas
signup_size: 10-50
signup_payment: pix
signup_plan: professional
```

### Ver etapa atual
```javascript
console.log('Etapa atual:', currentSignupStep);
console.log('Total de etapas:', totalSignupSteps);
```

### Verificar validação
```javascript
// Tentar validar etapa 1
console.log('Válida etapa 1?', validateCurrentSignupStep());

// Tentar validar etapa 2 (sem preencher)
currentSignupStep = 2;
console.log('Válida etapa 2 (vazia)?', validateCurrentSignupStep());
// Deve retornar false
```

### Reset do formulário
```javascript
// Volta para etapa 1 e limpa
currentSignupStep = 1;
updateSignupUI();

// Limpar localStorage
localStorage.clear();

// Recarregar página
location.reload();
```

---

## 📊 Checklist de Teste

| Teste | Status | Observações |
|-------|--------|-------------|
| Servidor rodando | ☐ | Porta 8000 acessível |
| HTML carrega | ☐ | Sem erros de console |
| Signup screen visível | ☐ | Clicou "Criar Conta" |
| Etapa 1 preenche e valida | ☐ | Próximo funciona apenas completo |
| Etapa 2 mostra setor | ☐ | Seletor com 12 opções |
| Etapa 2 valida indústria | ☐ | Erro se não seleciona |
| Etapa 3 mostra pagamentos | ☐ | 4 opções de pagamento |
| Etapa 4 mostra planos | ☐ | 3 cards com valores |
| Progress bar avança | ☐ | 25% → 50% → 75% → 100% |
| Anterior funciona | ☐ | Volta sem perder dados |
| Nenhuma tela cortada | ☐ | Tudo visível em mobile/desktop |
| Validação funciona | ☐ | Erros claros por campo |
| localStorage salva | ☐ | Dados persistem entre recargas |
| Submit envia para API | ☐ | check /api/auth/register |

---

## 📱 Teste Responsivo

### Desktop (1920px)
```bash
# Chrome DevTools → F12 → Ctrl+Shift+M → Set 1920x1080
```
- [ ] Tudo a lado a lado
- [ ] Sem scroll horizontal

### Tablet (768px)
```bash
# Chrome DevTools → Set 768x1024
```
- [ ] Layout ajusta
- [ ] Ainda legível

### Mobile (375px)
```bash
# Chrome DevTools → Set 375x667 (iPhone X)
```
- [ ] Stack vertical
- [ ] Botões clicáveis
- [ ] Sem cortes

---

## 🔌 Teste de Integração Backend

### Submeter de Verdade
```javascript
// No console, após preencher tudo:

const formData = {
  email: document.getElementById('signup-email').value,
  password: document.getElementById('signup-password').value,
  full_name: document.getElementById('signup-fullname').value,
  phone: document.getElementById('signup-phone').value,
  company_name: document.getElementById('signup-company').value,
  company_industry: document.getElementById('signup-industry').value,
  company_size: document.getElementById('signup-size').value,
  payment_method: document.querySelector('input[name="payment"]:checked')?.value,
  plan: document.querySelector('input[name="plan"]:checked')?.value
};

console.log('Enviando:', formData);

fetch('/api/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(formData)
})
  .then(r => r.json())
  .then(data => {
    console.log('Respostas:', data);
    if (data.success) console.log('✅ Cadastro criado!');
    else console.log('❌ Erro:', data.error);
  })
  .catch(e => console.error('❌ Erro na requisição:', e));
```

---

## 💡 Dicas

1. **Não fechar console** - Ajuda a ver erros em tempo real
2. **Usar data real** - email único para cada teste
3. **Limpar localStorage** entre testes - `localStorage.clear()`
4. **Verificar DevTools** - Network tab para ver requisições
5. **Mobile first** - Teste sempre em 375px primeiro
6. **F12 → Ctrl+Shift+Delete** - Limpar cache/cookies entre testes

---

## 🎬 Cenários de Teste

### Cenário 1: Usuário Normal
```
João Silva → Vendedor → Empresa LTDA (Vendas) 
→ Pix → Professional → ✅ Cadastro
```

### Cenário 2: Usuário Completo
```
Maria Santos → Médica → Clínica Geral (Saúde)
→ Detalhes → Boleto → Premium → ✅ Cadastro
```

### Cenário 3: Campo Vazio (Erro)
```
[Vazio] → Clique Próximo 
→ ❌ Erro "Nome obrigatório" → Preenche → ✅ Próximo
```

### Cenário 4: Email Inválido
```
"emailinvalido" → Clique Próximo
→ ❌ Erro "Email inválido" → Corrigi → ✅ Próximo
```

### Cenário 5: Senhas Diferentes
```
Senha: Abc123
Confirmar: Abc124
→ Clique Próximo → ❌ Erro "Senhas não coincidem"
```

---

## ✨ Resultado Final Esperado

Depois de clicar "Finalizar Cadastro":

```
✅ Cadastro criado com sucesso!
✅ Entre em sua conta
✅ Dashboard carregado
✅ Sistema se adaptou ao setor da empresa
🎉 Bem-vindo!
```

---

**Status**: 🟢 PRONTO PARA TESTE  
**Tempo estimado**: 5-10 minutos  
**Dificuldade**: ⭐ Fácil
