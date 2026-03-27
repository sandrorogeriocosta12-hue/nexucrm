# ✅ ROADMAP DE IMPLEMENTAÇÃO - VEXUS SERVICE CRM

**Documento de Rastreamento:** Prioridades e Status de Implementação  
**Data:** 27 de Março de 2026  
**Gerado por:** GitHub Copilot  

---

## 🔴 FASE 1: CRÍTICO (Implementar HOJE)

### [ ] 1. Configurar Variáveis de Ambiente no Railway
- **Arquivo:** Railway Dashboard
- **Tempo:** 30 min
- **Checklist:**
  - [ ] Ir para https://railway.app
  - [ ] Acessar projeto Vexus CRM
  - [ ] Adicionar `DATABASE_URL`
  - [ ] Adicionar `SECRET_KEY`
  - [ ] Adicionar `ENVIRONMENT=production`
  - [ ] Clicar "Restart"
  - [ ] Verificar logs em "Deployments"

**Status:** ⏳ PENDENTE  
**Responsável:** Victor  
**Data-target:** Hoje

---

### [ ] 2. Upload/Import de CSV e Excel
- **Arquivo:** `frontend/js/utils.js` + nova página `frontend/import.html`
- **Tempo:** 3-4 horas
- **Checklist:**
  - [ ] Copiar snippets de CSV/Excel parser para `utils.js`
  - [ ] Criar `frontend/import.html` com interface de upload
  - [ ] Adicionar mapeamento automático de colunas
  - [ ] Implementar validação de dados antes de importar
  - [ ] Testar com arquivo CSV de exemplo
  - [ ] Testar com arquivo XLSX
  - [ ] Adicionar mensagens de erro user-friendly
  - [ ] Commit + Deploy em Railway

**Status:** ⏳ PENDENTE  
**Responsável:** Victor  
**Data-target:** Hoje + Amanhã  
**Notas:** `papaparse` já incluído em requirements.txt?

---

### [ ] 3. Visualizações com Recharts (Gráficos)
- **Arquivo:** `frontend/reports.html` + `frontend/js/charts.js`
- **Tempo:** 3-4 horas
- **Checklist:**
  - [ ] Instalar `recharts` via CDN ou npm
  - [ ] Criar `frontend/js/charts.js` com funções de gráficos
  - [ ] Adicionar AreaChart (últimos 30 dias)
  - [ ] Adicionar BarChart (pipeline por estágio)
  - [ ] Adicionar PieChart (status dos negócios)
  - [ ] Adicionar LineChart (performance por período)
  - [ ] Integrar cores do design-system
  - [ ] Testar responsividade
  - [ ] Commit + Deploy em Railway

**Status:** ⏳ PENDENTE  
**Responsável:** Victor  
**Data-target:** Amanhã  
**Nota:** Recharts melhor que Chart.js para React-like code

---

## 🟠 FASE 2: ALTO (Implementar esta semana)

### [ ] 4. Toast System (Notificações Elegantes)
- **Arquivo:** `frontend/css/design-system.css` + `frontend/js/utils.js`
- **Tempo:** 1.5 horas
- **Checklist:**
  - [ ] Copiar CSS para toasts em design-system.css
  - [ ] Copiar funções de toast em utils.js
  - [ ] Substituir `alert()` por `toastError()` em contacts.html
  - [ ] Substituir `alert()` por `toastSuccess()` em pipeline.html
  - [ ] Substituir `alert()` por `toastWarning()` em tasks.html
  - [ ] Testar todos os tipos (success, error, warning, info)
  - [ ] Testar auto-dismiss (3s padrão)
  - [ ] Commit + Deploy

**Status:** ⏳ PENDENTE  
**Responsável:** Victor  
**Data-target:** Quarta-feira  
**Estimado:** ~1.5h

---

### [ ] 5. Busca Avançada com Filtros Multi-Critério
- **Arquivo:** `frontend/contacts.html` + `frontend/js/utils.js`
- **Tempo:** 2 horas
- **Checklist:**
  - [ ] Adicionar filter bar em contacts.html
  - [ ] Filtro por Status (prospect, client, inactive)
  - [ ] Filtro por Data de Criação (24h, 7d, 30d)
  - [ ] Filtro por Valor de Pipeline (ranges)
  - [ ] Filtro por Tags (multi-select)
  - [ ] Botão "Limpar Filtros"
  - [ ] Testar combinações de filtros
  - [ ] Testar com 100+ contatos
  - [ ] Commit + Deploy

**Status:** ⏳ PENDENTE  
**Responsável:** Victor  
**Data-target:** Quinta-feira  
**Estimado:** ~2h

---

### [ ] 6. Drag-and-Drop Avançado no Pipeline
- **Arquivo:** `frontend/pipeline.html` + `frontend/js/utils.js`
- **Tempo:** 2-3 horas
- **Checklist:**
  - [ ] Fazer cards draggable (`draggable="true"`)
  - [ ] Implementar visual feedback (opacity 0.5)
  - [ ] Detectar drop zone (coluna de destino)
  - [ ] Atualizar status do deal após drop
  - [ ] Adicionar animação de slide
  - [ ] Testar em desktop
  - [ ] Testar em mobile (touch)
  - [ ] Persistir mudança em localStorage
  - [ ] Commit + Deploy

**Status:** ⏳ PENDENTE  
**Responsável:** Victor  
**Data-target:** Quinta-feira  
**Estimado:** ~2-3h

---

### [ ] 7. PDF Export de Relatórios
- **Arquivo:** `frontend/reports.html` + `frontend/js/pdf-export.js`
- **Tempo:** 2 horas
- **Checklist:**
  - [ ] Instalar `html2pdf.js` via CDN
  - [ ] Criar função `exportReportPDF()`
  - [ ] Configurar orientação (portrait/landscape)
  - [ ] Testar exportação de tabelas
  - [ ] Testar exportação de gráficos
  - [ ] Nomear arquivo com data
  - [ ] Adicionar botão "Exportar PDF" em reports.html
  - [ ] Testar em Firefox, Chrome, Safari
  - [ ] Commit + Deploy

**Status:** ⏳ PENDENTE  
**Responsável:** Victor  
**Data-target:** Sexta-feira  
**Estimado:** ~2h

---

### [ ] 8. Testes Automatizados
- **Arquivo:** `frontend/tests/` (novo diretório)
- **Tempo:** 4-6 horas
- **Checklist:**
  - [ ] Criar diretório `frontend/tests/`
  - [ ] Instalar Vitest: `npm install -D vitest`
  - [ ] Criar `tests/api.test.js` (5 testes)
  - [ ] Criar `tests/utils.test.js` (5 testes)
  - [ ] Criar `tests/auth.test.js` (3 testes)
  - [ ] Criar `tests/pipeline.test.js` (2 testes)
  - [ ] Rodar testes: `npm test` (mínimo 15 passing)
  - [ ] Adicionar `npm test` ao GitHub Actions (CI/CD)
  - [ ] Commit + Deploy

**Status:** ⏳ PENDENTE  
**Responsável:** Victor  
**Data-target:** Próxima semana  
**Estimado:** ~4-6h

---

## 🟡 FASE 3: MÉDIO (Implementar próximas 2 semanas)

### [ ] 9. Light Mode / Theme Toggle
- **Arquivo:** `frontend/css/design-system.css` + `frontend/js/utils.js`
- **Tempo:** 1.5 horas
- **Checklist:**
  - [ ] Adicionar `.light-theme` em design-system.css
  - [ ] Criar função `toggleTheme()` em utils.js
  - [ ] Adicionar botão toggle no sidebar
  - [ ] Persistir escolha em localStorage
  - [ ] Testar em todas as páginas
  - [ ] Verificar contraste (WCAG AA)
  - [ ] Commit + Deploy

**Status:** ⏳ PENDENTE  
**Data-target:** Próximo fim de semana  

---

### [ ] 10. Service Workers (PWA - Funciona Offline)
- **Arquivo:** `frontend/service-worker.js` (novo)
- **Tempo:** 2-3 horas
- **Checklist:**
  - [ ] Criar `frontend/service-worker.js`
  - [ ] Implementar cache strategy (Cache-first para assets)
  - [ ] Implementar network-first para API calls
  - [ ] Registrar em main pages
  - [ ] Testar offline (DevTools > Offline)
  - [ ] Testar que API chama falham gracefully
  - [ ] Testar que assets servem do cache
  - [ ] Adicionar manifest.json (PWA)
  - [ ] Commit + Deploy

**Status:** ⏳ PENDENTE  
**Data-target:** Próximas 2 semanas  

---

### [ ] 11. Mobile Responsive Aprimorado
- **Arquivo:** `frontend/css/design-system.css` + todas as páginas
- **Tempo:** 2 horas
- **Checklist:**
  - [ ] Testar viewport 375px (iPhone SE)
  - [ ] Testar viewport 768px (iPad)
  - [ ] Testar viewport 1200px (Desktop)
  - [ ] Ajustar sidebar para collapse em mobile
  - [ ] Ajustar grid de cards para 1-2-4 colunas
  - [ ] Testar menu hamburger em mobile
  - [ ] Testar touch interactions
  - [ ] Testar landscape vs portrait
  - [ ] Commit + Deploy

**Status:** ⏳ PENDENTE  
**Data-target:** Próximas 2 semanas  

---

## 🔵 FASE 4: INTEGRAÇÕES (Próximo mês)

### [ ] 12. Integração OpenAI (Nexus Brain)
- **Prioridade:** 🔴 CRÍTICA (se usar IA)
- **Arquivo:** `app_server.py` + `frontend/insights.html`
- **Tempo:** 3-4 horas
- **Checklist:**
  - [ ] Obter `OPENAI_API_KEY` (https://platform.openai.com)
  - [ ] Adicionar em Railway Dashboard
  - [ ] Implementar endpoint `/api/insights` em FastAPI
  - [ ] Criar página `frontend/insights.html`
  - [ ] Adicionar análise de trends
  - [ ] Adicionar recomendações de ações
  - [ ] Testar com dados reais
  - [ ] Commit + Deploy

**Status:** ⏳ ESPERANDO API KEY  
**Data-target:** Quando tiver chave  

---

### [ ] 13. Integração WhatsApp Business API
- **Prioridade:** 🔴 CRÍTICA (se vender para empresas)
- **Arquivo:** `app_server.py` + `frontend/messages.html`
- **Tempo:** 3-4 horas
- **Checklist:**
  - [ ] Obter `WHATSAPP_BUSINESS_API_KEY`
  - [ ] Adicionar em Railway Dashboard
  - [ ] Implementar endpoint POST `/api/send-whatsapp`
  - [ ] Criar página de mensagens
  - [ ] Testar envio de mensagem
  - [ ] Testar webhook de recebimento
  - [ ] Commit + Deploy

**Status:** ⏳ ESPERANDO API KEY  
**Data-target:** Quando tiver chave  

---

### [ ] 14. Integração Google Calendar
- **Prioridade:** 🟡 MÉDIA
- **Arquivo:** Novo módulo `frontend/calendar.html`
- **Tempo:** 2-3 horas
- **Checklist:**
  - [ ] Criar app no Google Cloud Console
  - [ ] Obter `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET`
  - [ ] Implementar OAuth flow
  - [ ] Sincronizar eventos com tarefas
  - [ ] Mostra calendário em sidebar
  - [ ] Testar sincronização bidirecional

**Status:** ⏳ PENDENTE  
**Data-target:** Próximo mês  

---

### [ ] 15. Integração Slack
- **Prioridade:** 🟡 MÉDIA
- **Arquivo:** `app_server.py` 
- **Tempo:** 1.5 horas
- **Checklist:**
  - [ ] Criar App em Slack API
  - [ ] Obter `SLACK_BOT_TOKEN`
  - [ ] Implementar notificações de deals
  - [ ] Implementar notificações de tarefas
  - [ ] Testar em workspace Slack

**Status:** ⏳ PENDENTE  
**Data-target:** Próximo mês  

---

## 📊 RESUMO DE STATUS

| Fase | Item | Status | Prioridade | Tempo |
|------|------|--------|-----------|-------|
| 1 | Env vars Railway | ⏳ | 🔴 | 30 min |
| 1 | CSV/Excel Import | ⏳ | 🔴 | 3-4h |
| 1 | Recharts | ⏳ | 🔴 | 3-4h |
| 2 | Toast System | ⏳ | 🟠 | 1.5h |
| 2 | Busca Avançada | ⏳ | 🟠 | 2h |
| 2 | Drag-and-Drop | ⏳ | 🟠 | 2-3h |
| 2 | PDF Export | ⏳ | 🟠 | 2h |
| 2 | Testes | ⏳ | 🟠 | 4-6h |
| 3 | Light Mode | ⏳ | 🟡 | 1.5h |
| 3 | Service Workers | ⏳ | 🟡 | 2-3h |
| 3 | Mobile Responsive | ⏳ | 🟡 | 2h |
| 4 | OpenAI | ⏳ | 🔴\* | 3-4h |
| 4 | WhatsApp | ⏳ | 🔴\* | 3-4h |
| 4 | Google Calendar | ⏳ | 🟡 | 2-3h |
| 4 | Slack | ⏳ | 🟡 | 1.5h |

**TOTAL HORAS (TODOS OS ITENS):** ~45-60 horas  
**TOTAL (FASE 1-2 APENAS):** ~18-25 horas  
**TOTAL (FASE 1-3):** ~25-33 horas  

---

## 🚦 TIMELINE RECOMENDADA

### **SEMANA 1 (Hoje até Domingo)**
```
MON: Env vars (0.5h) + CSV Import Início (2h)
TUE: CSV Import Conclusão (2h) + Recharts (3h)
WED: Toast (1.5h) + Busca Avançada (2h)
THU: Drag-Drop (2.5h) + Final Semana 1
FRI: Deploy + Testes Manuais
```
**Horas:** ~14-16h  
**Output:** Sistema com importação de dados, gráficos, busca avançada

---

### **SEMANA 2 (Próxima semana)**
```
MON: PDF Export (2h) + Testes (2h)
TUE: Testes Continuação (2h) + Light Mode (1.5h)
WED: Service Workers (2.5h)
THU: Mobile Responsive (2h)
FRI: Deploy + Testes Completos
```
**Horas:** ~12-14h  
**Output:** Sistema completo com PWA, tests passando

---

### **SEMANA 3-4 (Próximas 2 semanas)**
```
Integrações (se houver API keys):
- OpenAI Insights
- WhatsApp
- Google Calendar (opcional)
- Slack (opcional)
```

---

## ✅ CRITÉRIOS DE CONCLUSÃO

### Fase 1 ✅ PRONTA PARA VENDA
- [x] Sistema verde em produção
- [x] Env vars configuradas
- [ ] Importação de contatos em massa
- [ ] Gráficos no dashboard
- [ ] Funciona em mobile

### Fase 2 ✅ PRONTO PARA ESCALABILIDADE
- [ ] Todos testes passando
- [ ] Notificações polidas
- [ ] PDF export funciona
- [ ] Drag-drop intuitivo

### Fase 3 ✅ PRONTO PARA COMPETIÇÃO
- [ ] Light mode implementado
- [ ] PWA (offline support)
- [ ] Mobile 100% responsivo

### Fase 4 ✅ PRONTO PARA DIFERENCIAÇÃO
- [ ] AI insights funcionando
- [ ] WhatsApp integrado
- [ ] Calendário sincronizado

---

## 🎯 PRÓXIMOS PASSOS IMEDIATOS

**AGORA (em 5 minutos):**
1. [ ] Ir para Railway Dashboard
2. [ ] Configurar `DATABASE_URL` e `SECRET_KEY`
3. [ ] Clicar "Restart"

**HOJE (próximas 2 horas):**
1. [ ] Copiar snippets do CSV import
2. [ ] Criar `frontend/import.html`
3. [ ] Testar com CSV de exemplo

**AMANHÃ (próximas 4 horas):**
1. [ ] Implementar Recharts em reports.html
2. [ ] Testar gráficos com dados reais
3. [ ] Deploy em Railway

---

**Gerado em:** 27 de Março de 2026  
**Documento:** ROADMAP Executivo  
**Status:** 🟢 PRONTO PARA COMEÇAR  
**Próxima revisão:** 03 de Abril de 2026
