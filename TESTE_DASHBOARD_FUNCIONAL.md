# 🎉 GUIA DE TESTE - DASHBOARD FUNCIONAL VEXUS CRM

## ✅ STATUS ATUAL

**Dashboard Novo - FUNCIONAL COM TODAS AS FEATURES**

```
✅ Dashboard carrega corretamente
✅ JavaScript integrado e funcional
✅ 25+ funções JavaScript implementadas
✅ 3 Modais de criação (Lead, Campanha, Contato)
✅ APIs integradas (apiFetch)
✅ Sistema de notificações
✅ Autenticação JWT
✅ CRUD completo para Leads, Campanhas e Contatos
✅ Sistema de abas (tabs)
✅ Verificação de saúde do sistema
```

---

## 🌐 ACESSAR O DASHBOARD

### URL Principal:
```
https://api.nexuscrm.tech/
```

---

## 🔑 CREDENCIAIS DE TESTE

**Usuário de Teste:**
- Email: `test@vexus.com`
- Senha: `test123`

---

## 📋 PASSO A PASSO PARA TESTAR

### 1️⃣ ACESSAR O DASHBOARD

1. Abra: `https://api.nexuscrm.tech/`
2. Se não estiver logado, será redirecionado para login
3. Faça login com:
   - Email: `test@vexus.com`
   - Senha: `test123`

**✅ Esperado:** Deve carregar o dashboard com 4 cards de métricas (Leads, Campanhas, Contatos, Sistema)

---

### 2️⃣ TESTAR LEADS

#### **Criar um Lead:**
1. Dashboard → Aba "📊 Leads"
2. Clique em "+ Novo Lead"
3. Preencha:
   - Nome: "João Silva"
   - Email: "joao@empresa.com"
   - Empresa: "Tech Corp"
   - Valor: 5000
   - Status: "Novo"
4. Clique "Salvar"

**✅ Esperado:**
- Toast notification: "✅ Lead criado com sucesso!"
- Lead aparece na tabela
- Contador "Leads" aumenta

#### **Deletar um Lead:**
1. Clique em "🗑️ Deletar" ao lado do lead
2. Confirme a ação

**✅ Esperado:** Lead é removido da tabela, contador diminui

---

### 3️⃣ TESTAR CAMPANHAS

#### **Criar uma Campanha:**
1. Clique na aba "📢 Campanhas"
2. Clique em "+ Nova Campanha"
3. Preencha:
   - Nome: "Campanha Q1 2026"
   - Descrição: "Campanha de vendas primeiro trimestre"
   - Orçamento: 10000
4. Clique "Salvar"

**✅ Esperado:**
- Toast: "✅ Campanha criada com sucesso!"
- Campanha aparece na tabela
- Contador aumenta

#### **Deletar uma Campanha:**
1. Clique em "🗑️ Deletar"
2. Confirme

**✅ Esperado:** Campanha removida

---

### 4️⃣ TESTAR CONTATOS

#### **Criar um Contato:**
1. Clique na aba "👥 Contatos"
2. Clique em "+ Novo Contato"
3. Preencha:
   - Nome: "Maria Santos"
   - Email: "maria@empresa.com"
   - Telefone: "(11) 99999-9999"
   - Empresa: "Consultoria XYZ"
   - Cargo: "Diretora"
4. Clique "Salvar"

**✅ Esperado:**
- Toast: "✅ Contato criado com sucesso!"
- Contato aparece na tabela
- Contador "Contatos" aumenta

#### **Deletar um Contato:**
1. Clique em "🗑️ Deletar"
2. Confirme

**✅ Esperado:** Contato removido

---

### 5️⃣ TESTAR AGENTES

1. Clique na aba "🤖 Agentes"

**✅ Esperado:** Deve mostrar cards com:
- scoring_agent ✅
- pipeline_manager ✅
- conversation_analyzer ✅
- next_best_action ✅
- proposal_generator ✅
- followup_scheduler ✅
- channel_optimizer ✅

---

### 6️⃣ TESTAR NAVEGAÇÃO

#### **Trocar de Abas:**
1. Clique em "📊 Leads" → Deve mostrar seção de Leads
2. Clique em "📢 Campanhas" → Deve mostrar seção de Campanhas
3. Clique em "👥 Contatos" → Deve mostrar seção de Contatos
4. Clique em "🤖 Agentes" → Deve mostrar seção de Agentes

**✅ Esperado:** Cada aba carrega seu conteúdo, border inferior muda de cor

---

### 7️⃣ TESTAR AUTENTICAÇÃO

#### **Logout:**
1. Clique em "Sair" (canto superior direito)

**✅ Esperado:** Redirecionado para página de login

#### **Tentar acessar sem token:**
1. Abra as Developer Tools (F12)
2. Console
3. Execute: `localStorage.removeItem('vexus_token')`
4. Recarregue a página

**✅ Esperado:** Redirecionado para login

---

### 8️⃣ TESTAR MÉTRICAS

#### **Verificar Contadores:**
1. Crie 3 leads, 2 campanhas, 1 contato
2. Verifique os contadores:
   - "Leads" deve mostrar 3
   - "Campanhas" deve mostrar 2
   - "Contatos" deve mostrar 1

**✅ Esperado:** Contadores atualizam em tempo real

#### **System Status:**
1. Verifique o card "🟢 Sistema"
2. Deve mostrar "Sistema Online"
3. Se houver problema com DB, mostrará "🔴 Problemas detectados"

**✅ Esperado:** Status green (🟢)

---

### 9️⃣ TESTAR NOTIFICAÇÕES

#### **Sucesso:**
1. Crie um novo lead
2. Deve aparecer toast verde com mensagem de sucesso

#### **Erro (simular):)**
1. Abra DevTools (F12)
2. Console
3. Execute: `showNotification('Erro de teste', true)`

**✅ Esperado:** Toast vermelho aparece no canto inferior direito

---

### 🔟 TESTAR ATUALIZAÇÕES AUTOMÁTICAS

1. Em uma aba, crie um lead
2. Espere 15 segundos (intervalo de refresh automático)
3. A tabela deve atualizar automaticamente

**✅ Esperado:** Dados sincronizados sem recarregar a página

---

## 🛠️ COMANDOS DE DEBUG

### Verificar se dashboard carrega corretamente:
```bash
curl -s https://api.nexuscrm.tech/ | grep -o "Dashboard Funcional\|apiFetch\|loadLeads"
```

### Testar autenticação:
```bash
curl -X POST https://api.nexuscrm.tech/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test@vexus.com","password":"test123"}'
```

### Verificar Leads via API:
```bash
TOKEN="seu_token_aqui"
curl https://api.nexuscrm.tech/api/leads \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📊 CHECKLIST DE TESTES

- [ ] Dashboard carrega sem erros
- [ ] Login funciona com test@vexus.com / test123
- [ ] Pode criar novo lead
- [ ] Pode deletar lead
- [ ] Pode criar campanha
- [ ] Pode deletar campanha
- [ ] Pode criar contato
- [ ] Pode deletar contato
- [ ] Abas mudam corretamente
- [ ] Agentes carregam (7 agentes)
- [ ] Contadores atualizam
- [ ] Sistema mostra online (🟢)
- [ ] Notificações funcionam
- [ ] Logout funciona
- [ ] Token expira corretamente

---

## 🎯 FUNCIONALIDADES DO NOVO DASHBOARD

| Feature | Status | Teste |
|---------|--------|-------|
| **Carregar Dashboard** | ✅ | URL `/` |
| **Login/Logout** | ✅ | Botão Sair |
| **Criar Leads** | ✅ | + Novo Lead |
| **Listar Leads** | ✅ | Aba Leads |
| **Atualizar Lead** | ⏳ | Próxima versão |
| **Deletar Lead** | ✅ | Botão Deletar |
| **Criar Campanhas** | ✅ | + Nova Campanha |
| **Listar Campanhas** | ✅ | Aba Campanhas |
| **Deletar Campanha** | ✅ | Botão Deletar |
| **Criar Contatos** | ✅ | + Novo Contato |
| **Listar Contatos** | ✅ | Aba Contatos |
| **Deletar Contato** | ✅ | Botão Deletar |
| **Ver Agentes** | ✅ | Aba Agentes |
| **Notificações** | ✅ | Toast alerts |
| **Auto-refresh** | ✅ | A cada 15s |
| **Responsividade** | ✅ | Tailwind CSS |

---

## ⚠️ NOTAS IMPORTANTES

1. **Banco de Dados Limpo**: O banco foi limpo. Comece do zero com testes.
2. **Token JWT**: Válido por 30 minutos. Após expirar, precisa fazer login novamente.
3. **Auto-refresh**: Dashboard atualiza a cada 15 segundos automaticamente.
4. **Modais**: Todos os modais podem ser fechados com "Cancelar" ou clicando fora.
5. **Notificações**: Aparecem por 3 segundos no canto inferior direito.

---

## 🚀 PRÓXIMOS PASSOS

1. **Testar todas as funcionalidades** conforme checklist acima
2. **Relatar problemas** encontrados
3. **Melhorias futuras**:
   - [ ] Editar leads/campanhas/contatos
   - [ ] Filtros e busca
   - [ ] Exportar dados
   - [ ] Mais agentes IA
   - [ ] Integrações WhatsApp

---

**Sistema pronto para testes manuais!** 🎉

Se encontrar algum problema, me informe para corrigir imediatamente.
