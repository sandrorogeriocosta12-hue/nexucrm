# ⚡ NEXUS CRM - CHECKLIST DE EXECUÇÃO "UM CLIQUE"

**Objetivo:** Implementar integração "um clique" que permite conectar 4 canais (WhatsApp, Telegram, Instagram) sem entrar uma única credencial manualmente.

**Timeline:** Quinta-Segunda (5 dias)  
**Status:** 🟢 **TODOS OS ARQUIVOS PRONTOS - COMECE AQUI**

---

## 📋 QUINTA (Hoje) - SETUP INICIAL

### Fase 1: Verificações Básicas
```
[ ] Verificar se Docker está instalado
    $ docker --version
    
    Se NÃO estiver:
    └─ Windows: bajajbaixe Docker Desktop
    └─ Mac: brew install docker
    └─ Linux: sudo apt install docker.io

[ ] Verificar se Python 3.8+ está instalado
    $ python3 --version
    
    Se NÃO estiver:
    └─ Windows: https://www.python.org/downloads/
    └─ Mac: brew install python3
    └─ Linux: sudo apt install python3

[ ] Verificar pip instalado
    $ pip3 --version
```

### Fase 2: Setup Automático
```
[ ] Navegar para diretório do projeto
    $ cd ~/PycharmProjects/Vexus\ Service

[ ] Rodar script de setup
    $ python3 setup_integrations.py
    
    Este script vai:
    ✅ Conferir dependências
    ✅ Criar .env com variáveis
    ✅ Iniciar Evolution API (Docker)
    ✅ Criar database SQLite
    ✅ Gerar relatório

[ ] Aguardar conclusão (2-3 minutos)
    └─ Deve terminar com: "✨ Setup finalizado!"

[ ] Verificar se Evolution API está rodando
    $ curl http://localhost:3000/health
    
    Deve retornar: {"status":"ok"}
```

### Fase 3: Editar Credenciais
```
[ ] Abrir arquivo .env
    $ nano .env (ou seu editor favorito)

[ ] Editar FACEBOOK_APP_ID
    ├─ Vá para: https://developers.facebook.com/apps
    ├─ Crie uma "App"
    ├─ Copie "App ID"
    └─ Cole em: FACEBOOK_APP_ID=seu_id_aqui

[ ] Editar FACEBOOK_APP_SECRET
    ├─ Na mesma página do app
    ├─ Vá para "Settings" → "Basic"
    ├─ Copie "App Secret"
    └─ Cole em: FACEBOOK_APP_SECRET=seu_secret_aqui

[ ] Editar INSTAGRAM_VERIFY_TOKEN
    ├─ Gere uma string aleatória de 32 caracteres
    ├─ Pode usar: $(openssl rand -hex 16)
    └─ Cole em: INSTAGRAM_VERIFY_TOKEN=gerado_aqui

[ ] Salvar arquivo .env
    └─ Atalho: CTRL+X (nano), depois Y, Enter
```

### Fase 4: Iniciar Servidor
```
[ ] Terminal novo: Navegar para projeto
    $ cd ~/PycharmProjects/Vexus\ Service

[ ] Rodar servidor
    $ python app_server.py
    
    Deve mostrar:
    ├─ "INFO: Uvicorn running on http://0.0.0.0:8000"
    ├─ "✅ Webhook router incluído"
    ├─ "✅ Integration router incluído"
    └─ "✅ Evolution API (WhatsApp) disponível"

[ ] Manter esse terminal aberto (servidor rodando)
```

### Fase 5: Testar Localmente
```
[ ] Abrir navegador
    → http://localhost:8000/integrations-ui

[ ] Deve ver:
    ├─ Título: "⚡ Integrar Seus Canais"
    ├─ 4 cards grandes (WhatsApp, Telegram, Instagram, Email)
    ├─ Cada um com botão de ação
    └─ Status dashboard no topo

[ ] Se não vê nada:
    └─ Verificar console (F12) por erros
    └─ Verificar se servidor está rodando
    └─ Tentar http://localhost:8000/ (deve retornar JSON)
```

### ✅ QUINTA - CONCLUSÃO

```
Você deve ter:
✅ Docker rodando
✅ Evolution API em http://localhost:3000
✅ Database SQLite criado
✅ .env com credenciais Meta
✅ Servidor FastAPI em http://localhost:8000
✅ Interface em http://localhost:8000/integrations-ui

Próximo: IR PARA FASE SEXTA
```

---

## 📱 SEXTA - TESTE DE CANAL WHATSAPP

### Fase 1: Testar QR Code
```
[ ] Ir para http://localhost:8000/integrations-ui

[ ] Card "WhatsApp":
    ├─ Clique em botão "Gerar QR Code"
    └─ Deve aparecer código QR na tela

[ ] Se QR não aparecer:
    ├─ Verificar console (F12)
    ├─ Procurar erro em vermelho
    ├─ Verificar se Evolution API está UP:
    │   $ curl http://localhost:3000/health
    └─ Se falhar, recomeçar Docker:
        $ docker restart evolution-api

[ ] Se QR apareceu:
    ├─ Pegar celular com WhatsApp instalado
    ├─ Abrir câmera nativa (não o app do WhatsApp)
    ├─ Apontar para QR code na tela
    ├─ Aguardar 3-5 segundos
    ├─ Link "Abrir com WhatsApp" deve aparecer
    ├─ Clique no link
    └─ WhatsApp abre e pede confirmação

[ ] Na confirmação do WhatsApp:
    ├─ Clique em "Linked Device" ou "Dispositvo Vinculado"
    └─ Pronto! Deve conectar

[ ] Volte para navegador:
    └─ Card "WhatsApp" deve agora mostrar "✅ Conectado!"
```

### Fase 2: Testar Recebimento
```
[ ] Smartphone com WhatsApp vinculado:
    ├─ Abra qualquer chat (seu próprio número, grupo, etc)
    ├─ Envie uma mensagem teste: "Olá Nexus!"
    └─ Aperte enviar

[ ] Volta para servidor terminal:
    ├─ Deve aparecer em logs:
    │   "✅ Mensagem recebida: Olá Nexus!"
    │   "AI Score: 45.5"
    │   "Status: processed"
    └─ Se não aparecer:
        └─ Verificar se está observando terminal correto

[ ] Database check:
    $ sqlite3 nexus_crm.db "SELECT * FROM messages LIMIT 1;"
    
    Deve retornar a mensagem que enviou
```

### ✅ SEXTA PM - CONCLUSÃO

```
Você pode agora:
✅ Gerar QR Code do WhatsApp
✅ Escanear com celular
✅ Receber mensagens em tempo real
✅ Mensagens aparecem no database

Próximo: IR PARA FASE SÁBADO
```

---

## 🤖 SÁBADO MANHÃ - TESTE TELEGRAM

### Fase 1: Criar Bot no BotFather
```
[ ] Smartphone com Telegram:
    ├─ Procurar por: @BotFather
    ├─ Clicar em "Start"
    └─ Deve mostrar menu com comandos

[ ] Enviar comando ao BotFather
    └─ /newbot

[ ] BotFather pede nome:
    ├─ Digite: "NexusTestBot"
    ├─ Enter
    └─ BotFather pede username

[ ] BotFather pede username:
    ├─ Digite: "nexus_test_seu_nome_bot" (deve ser único)
    ├─ Enter
    └─ BotFather envia TOKEN

[ ] Copiar TOKEN:
    ├─ Deve parecer: 123456:ABCdefGHIjklMNOpqrsTUVwxyz-1
    ├─ Copiar EXATAMENTE
    └─ Guardar em lugar seguro
```

### Fase 2: Conectar Token no Nexus
```
[ ] Navegador: http://localhost:8000/integrations-ui

[ ] Card "Telegram":
    ├─ Campo de entrada "Cole o token do seu bot aqui"
    ├─ Colar o token (CTRL+V)
    ├─ Apareça um botão "✓" ao lado
    └─ Clique no botão "✓"

[ ] Deve mostrar:
    └─ "✅ NexusTestBot Conectado!"
    └─ Card muda de cor (vermelho → verde)

[ ] Se não conecta:
    ├─ Verificar se token está completo (sem espaços)
    ├─ Verificar console (F12) por erro
    ├─ Tentar novamente (pode ser delay)
    └─ Se persistir, revisar token no BotFather
```

### Fase 3: Testar Recebimento
```
[ ] Telegram smartphone:
    ├─ Procurar pelo bot "NexusTestBot" que acabou de criar
    ├─ Clique em "Start"
    └─ Escreva mensagem: "Teste do Nexus"

[ ] Servidor terminal:
    ├─ Deve aparecer:
    │   "✅ Mensagem Telegram recebida"
    │   "De: seu_usuario_telegram"
    │   "Texto: Teste do Nexus"
    └─ Verificar AI Score nos logs

[ ] Database:
    $ sqlite3 nexus_crm.db "SELECT * FROM messages 
      WHERE channel='telegram' ORDER BY id DESC LIMIT 1;"
    
    Deve retornar a mensagem
```

### ✅ SÁBADO MANHÃ - CONCLUSÃO

```
Você pode agora:
✅ Conectar bot Telegram
✅ Receber mensagens via Telegram
✅ Mensagens aparecem no database

WhatsApp + Telegram trabalhando!
Próximo: INSTAGRAM SÁBADO À TARDE
```

---

## 📸 SÁBADO TARDE - TESTE INSTAGRAM

### Fase 1: OAuth Setup
```
[ ] Navegador: http://localhost:8000/integrations-ui

[ ] Card "Instagram":
    ├─ Botão "Conectar com Facebook"
    ├─ Clique no botão
    └─ Será redirecionado para Meta/Facebook

[ ] Se não redirecionou:
    ├─ Verificar console (F12)
    ├─ Conferir FACEBOOK_APP_ID em .env
    └─ Conferir FACEBOOK_REDIRECT_URI

[ ] Página de Login Meta:
    ├─ Faça login com conta Facebook/Meta
    ├─ (Se não tiver, criar: www.facebook.com/signup)
    └─ Clique "Próximo" ou "Next"

[ ] Página de Permissões:
    ├─ Meta pedirá autorização para:
    │   - "Ler seus Direct Messages"
    │   - "Gerenciar contas Instagram"
    └─ Clique em "Autorizar" ou "Allow"

[ ] Redirecionado de volta:
    └─ Voltará para http://localhost:8000/integrations-ui
    └─ Card "Instagram" deve mostrar "✅ Conectado!"
```

### Fase 2: Verificar Status
```
[ ] Dashboard de Status:
    └─ Deve mostrar 3 canais conectados:
        ✅ WhatsApp
        ✅ Telegram
        ✅ Instagram
        ⏳ Email (em breve)

[ ] Se falta status:
    ├─ Recarregar página (F5)
    ├─ Se ainda não aparecer:
    │   └─ Testar endpoint:
    │       $ curl http://localhost:8000/integrations/status/demo_client
    │       └─ Deve retornar JSON com 3 canais
    └─ Se erro, revisar OAut setup
```

### ✅ SÁBADO TARDE - CONCLUSÃO

```
Você TEM AGORA:
✅ WhatsApp conectado (QR)
✅ Telegram conectado (Token)
✅ Instagram conectado (OAuth)

TODOS 3 CANAIS FUNCIONANDO!

Próximo: TESTES DE PONTA-A-PONTA (DOMINGO)
```

---

## 🔄 DOMINGO - TESTES PONTA-A-PONTA

### Fase 1: Testar Fluxo Completo
```
[ ] Terminal 1: Servidor rodando
    $ python app_server.py

[ ] Terminal 2: Monitorar logs
    $ tail -f server.log (se existir)

[ ] Enviar mensagens nos 3 canais:
    
    WhatsApp:
    ├─ Smartphone com WhatsApp vinculado
    ├─ Qualquer chat: "Processo automático funcionando?"
    └─ Enviar
    
    Telegram:
    ├─ Procurar bot criado: @NexusTestBot
    ├─ Enviar: "Teste Telegram completo"
    └─ Enviar
    
    Instagram:
    ├─ Enviar DM para conta com Instagram Business
    ├─ Qualquer mensagem
    └─ Enviar

[ ] Verificar database:
    $ sqlite3 nexus_crm.db "SELECT channel, sender, message_text FROM messages 
      ORDER BY id DESC LIMIT 3;"
    
    Deve retornar 3 linhas (uma de cada canal)
```

### Fase 2: Verificar AI Scoring
```
[ ] Mensagens com scores diferentes:
    
    Telegram: "Gostaria de comprar seu produto"
    └─ Score deve ser alto (~80-100) = LEAD
    
    WhatsApp: "Oi tudo bem?"
    └─ Score deve ser médio (~40-60) = INTERESSADO
    
    Instagram: "xyz"
    └─ Score deve ser baixo (~10-20) = RUÍDO

[ ] Verificar scores no database:
    $ sqlite3 nexus_crm.db "SELECT * FROM messages 
      WHERE ai_score IS NOT NULL ORDER BY id DESC LIMIT 5;"
    
    Todos devem ter coluna ai_score preenchida

[ ] Se scores todos zerados:
    ├─ AI engine pode não estar integrado
    ├─ Verificar arquivo webhook_receiver.py
    ├─ Função: async get_ai_prediction()
    └─ Pode estar retornando 0 de forma fake
```

### Fase 3: Testar Auto-Response
```
[ ] Enviar mensagem HIGH-QUALITY no Telegram:
    
    Mensagem: "Olá, sou Victor, interessado em sua solução"
    └─ Score deve ser > 80 (hot lead)

[ ] Verificar se resposta automática foi enviada:
    
    No database:
    $ sqlite3 nexus_crm.db "SELECT response_sent, response_text 
      FROM messages ORDER BY id DESC LIMIT 1;"
    
    Deve mostrar:
    ├─ response_sent = 1 (TRUE)
    └─ response_text = "Obrigado! Vamos analisar sua demanda"

[ ] Telegram - Verificar se recebeu:
    ├─ Abra bot @NexusTestBot
    └─ Deve ter mensagem automática de novo!
```

### ✅ DOMINGO - CONCLUSÃO

```
Você pode COMPROVAR:
✅ 3 canais recebem mensagens
✅ AI scoring funciona (scores 0-100)
✅ Auto-responses disparadas (score > 0.8)
✅ Database armazena tudo
✅ Sistema é confiável

Próximo: PREPARAR PARA SEGUNDA (GO-LIVE)
```

---

## 🚀 SEGUNDA-FEIRA - PRODUÇÃO

### Pré-Deploy Checklist
```
[ ] Revisar arquivo .env
    ├─ Não committar secrets em Git
    ├─ Railway/Render lê de environment variables
    └─ Configurar secrets no painel após deploy

[ ] Revisar firewall/rede
    ├─ Porta 8000 acessível externamente? (HTTPS na frente)
    ├─ HTTPS certificado Let's Encrypt
    └─ SSL validation ativo

[ ] Database fazer backup
    $ sqlite3 nexus_crm.db ".backup backup.db"

[ ] Testar como cliente novo
    ├─ Abrir navegador incógnito
    ├─ Acessar: https://api.nexuscrm.tech/integrations-ui
    ├─ Simular onboarding do zero
    └─ Tudo deve funcionar
```

### Deploy em Staging
```
[ ] Commit to git + push
    $ git add . && git commit -m "Deploy integrations UI"
    $ git push origin main

[ ] Aguardar auto-build (Railroad/Render)
    └─ (~2-5 min)

[ ] Testar em staging URL
    $ curl https://staging.nexuscrm.tech/integrations-ui
    
    Deve retornar HTML do UI

[ ] Full E2E test em staging
    ├─ Gerar QR Code
    ├─ Conectar Telegram
    ├─ Fazer OAuth Instagram
    ├─ Enviar mensagens nos 3
    └─ Verificar se chegam no dashboard
```

### Deploy em Produção
```
[ ] Se staging passou em todos testes:
    
    Option 1 (Manual):
    └─ Fazer release/tag no Github
        $ git tag -a v2.0-integrations -m "UI One-click deployment"
        $ git push origin v2.0-integrations

    Option 2 (Railway/Render):
    └─ Promover deploy de staging → production

[ ] Aguardar confirmação (2-5 min)

[ ] Testar em produção
    $ curl https://api.nexuscrm.tech/integrations-ui
    
    Deve retornar pagina HTML

[ ] Smoke tests
    ├─ [ ] Página carrega rápido (< 2s)
    ├─ [ ] QR Code gera em < 3s
    ├─ [ ] Telegram box aparece
    ├─ [ ] Instagram oauth redireciona
    └─ [ ] Dashboard atualiza em tempo real
```

### Notificações
```
[ ] Enviar para time:
    ✅ Sistema em produção!
    ✅ URL: https://api.nexuscrm.tech/integrations-ui
    ✅ Todos 3 canais (WhatsApp, Telegram, Instagram) ativos
    ✅ Auto-responses funcionando
    ✅ Dashboard em tempo real

[ ] Enviar para primeiros clientes testadores:
    ✅ Link para acessar UI
    ✅ Tutorial curto (5 min)
    ✅ Email de suporte
```

### Monitoramento
```
[ ] Dashboard de monitoring
    ├─ [ ] Uptime: > 99.9%
    ├─ [ ] Webhook latency: < 500ms
    ├─ [ ] Error rate: < 0.1%
    ├─ [ ] CPU usage: < 50%
    └─ [ ] Memory: < 70%

[ ] Alertas configurados para:
    ├─ Quando uptime cair < 99%
    ├─ Quando latency > 1000ms
    ├─ Quando error rate > 1%
    └─ Contato: seu_email@nexuscrm.tech
```

### ✅ SEGUNDA - CONCLUSÃO

```
VOCÊ CONSEGUIU! 🎉

✅ Sistema em PRODUÇÃO
✅ 3 canais funcionando
✅ Clientes onboarding "um clique"
✅ Mensagens chegando em tempo real
✅ AI scoring automático
✅ Auto-responses funcional
✅ Time celebrando sucesso!

TIMELINE CUMPRIDA:
├─ Quinta: Setup ✅
├─ Sexta: WhatsApp + Telegram ✅
├─ Sábado: Instagram ✅
├─ Domingo: Testes ✅
└─ Segunda: PRODUÇÃO ✅
```

---

## 📞 Se Algo Não Funcionar

### Geral
```
❌ Servidor não inicia
   → Verificar porta 8000 em uso
   → Matar: lsof -ti:8000 | xargs kill -9
   → Reiniciar: python app_server.py

❌ Erro de import
   → pip3 install -r requirements.txt
   → Verificar se webpack_receiver.py + one_click_integrations.py existem

❌ Database não criado
   → sqlite3 nexus_crm.db ".schema"
   → Se vazio, rodar setup novamente
```

### WhatsApp (QR Code)
```
❌ QR não aparece
   → Verificar Evolution API: curl http://localhost:3000/health
   → Restart container: docker restart evolution-api
   → Logs: docker logs evolution-api

❌ QR não reconhece
   → Tentar em aplicativo de câmera de outro celular
   → Aumentar iluminação
   → Aumentar zoom da tela
```

### Telegram
```
❌ Token inválido
   → Verificar no BotFather: /mybots → selecionar bot → API Token
   → Copiar token EXATAMENTE (sem espaços)
   → Cole novamente

❌ Bot não responde
   → Verificar /mybots → selecionar → Edit → edit commands
   → Webhook deve estar ativo
```

### Instagram
```
❌ OAuth não redireciona
   → Verificar FACEBOOK_APP_ID em .env
   → Verificar FACEBOOK_REDIRECT_URI correto
   → Tester account precisa estar em app admin

❌ DM não chega
   → Account deve ser Instagram Business
   → Meta webhook talvez demore 5 min para ativar
```

---

## 📞 CONTATO DE SUPORTE

Se travou em alguma fase:

1️⃣ Consultar: INTEGRATION_GUIDE.md  
2️⃣ Consultar: QUICK_START_INTEGRATIONS.md  
3️⃣ Abrir issue: support@nexuscrm.tech  
4️⃣ Chat: [Slack/Discord do team]

---

## ✨ Você está pronto!

**Aqui está seus próximos passos em ordem:**

```
👉 AGORA:       python3 setup_integrations.py
👉 DEPOIS:      Editar .env com credenciais Meta
👉 DEPOIS:      python app_server.py
👉 DEPOIS:      http://localhost:8000/integrations-ui
👉 DEPOIS:      Testar 3 canais
👉 DEPOIS:      Commit + Deploy
👉 DEPOIS:      PRODUÇÃO!!!

Tempo total: 4-6 horas para primeira release
```

---

**🎯 Nexus CRM - Integration One-Click**  
*Timeline: Quinta → Segunda (Entrega)*  
*Status: 🟢 READY TO GO*
