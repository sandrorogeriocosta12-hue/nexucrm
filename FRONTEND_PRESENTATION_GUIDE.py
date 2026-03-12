"""
╔════════════════════════════════════════════════════════════════════════════╗
║  🎬 GUIA DE APRESENTAÇÃO DO FRONTEND - Nexus Service                      ║
║  Ordem correta das telas para segunda-feira em Campos                     ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

PRESENTATION_GUIDE = """

═══════════════════════════════════════════════════════════════════════════════
📋 TELAS PARA APRESENTAR (Em Ordem)
═══════════════════════════════════════════════════════════════════════════════

TELA 1: Login (login-nexus.html)
  ├─ Tempo: 30 segundos
  ├─ O que mostrar:
  │  ├─ Logo "Nexus Service" profissional
  │  ├─ Frase: "Lead Scoring em Tempo Real"
  │  └─ Input para logar rápido
  └─ Ação: Logar (demo/demo ou user real)

TELA 2: Inbox (inbox-nexus.html)
  ├─ Tempo: 1:30 minutos
  ├─ O que mostrar:
  │  ├─ Conversa chegando em tempo real
  │  ├─ Cada lead com SCORE visível (0.87 🔥, 0.62 ⚠️, etc)
  │  ├─ Cores: Vermelho (HOT), Laranja (WARM), Azul (COLD)
  │  ├─ Mensagem do cliente: "Oi, quero um orçamento"
  │  ├─ Bot respondendo automaticamente < 3 segundos
  │  └─ Score final: 0.87 (HOT) com "Proposta gerada em 45 segundos"
  └─ Ação: Clicar no botão "Ver Proposta Gerada"

TELA 3: KPI Dashboard (kpi-dashboard.html)
  ├─ Tempo: 2:30 minutos
  ├─ O que mostrar (números que impressionam):
  │  ├─ Card 1: 450 leads processados este mês
  │  ├─ Card 2: 12% conversão (era 8%)
  │  ├─ Card 3: R$ 85.000 potencial
  │  ├─ Card 4: < 3 segundos resposta
  │  ├─ Card 5: 87% acurácia ML
  │  ├─ Gráfico: Trending conversão (linha crescente 6% → 12%)
  │  └─ Quick stats: 23 leads quentes, próximas ações
  └─ Ação: Deixar silencioso, apenas mostrar números

TELA 4: Pipeline (pipeline-nexus.html)
  ├─ Tempo: 1:30 minuto
  ├─ O que mostrar:
  │  ├─ Kanban com 4 colunas: Novo, Qualificado, Proposta, Contrato
  │  ├─ Números em cada coluna: 32 novo, 28 qualificado, 18 proposta, 8 contrato
  │  ├─ Cada lead com score e nome
  │  └─ Pipeline visual claro (fluxo dos clientes)
  └─ Ação: "Isto são os leads em cada estágio. Você vê claramente quem converter"

═══════════════════════════════════════════════════════════════════════════════
⏱️  TIMING EXATO DA APRESENTAÇÃO
═══════════════════════════════════════════════════════════════════════════════

TOTAL: 25 MINUTOS DEMO

0:00-0:30   Login + Acessar
0:30-2:00   Inbox (conversa + score + bot automático)
2:00-4:30   KPI Dashboard (números + gráfico)
4:30-6:00   Pipeline (funil de vendas)
6:00-6:30   Buffer (perguntas do CEO)

═══════════════════════════════════════════════════════════════════════════════
💻 SETUP TÉCNICO (SEGUNDA DE MANHÃ)
═══════════════════════════════════════════════════════════════════════════════

1. Abri 4 abas do Chrome/Firefox:
   [ ] Aba 1: login-nexus.html
   [ ] Aba 2: inbox-nexus.html
   [ ] Aba 3: kpi-dashboard.html
   [ ] Aba 4: pipeline-nexus.html

2. Fazer zoom in à 150% (para letras maiores na TV):
   Ctrl/Cmd + (3x)

3. Modo presentation mode (F11 se quiser full screen):
   Tira barra de endereço, fica só as páginas

4. Se internet cair:
   [ ] Tirar screenshots de cada tela (PNG em alta resolução)
   [ ] Salvar no desktop como backup offline

═══════════════════════════════════════════════════════════════════════════════
🎯 SCRIPT PARA CADA TELA
═══════════════════════════════════════════════════════════════════════════════

TELA 1 - LOGIN:
──────────────
"Vamos começar aqui. É a tela de login do Nexus Service.
 Vê? Profissional, seguro, rápido.
 [Logar com demo/demo]"

TELA 2 - INBOX:
──────────────
"Aqui é o coração do sistema: mensagens chegando em tempo real.
 Você vê aqui: um cliente escrevendo 'Oi, quero orçamento'.
 
 Vê esse número aqui? [Aponta para 0.87]
 É o SCORE de quente é esse lead. 
 87% de chance ele converter.
 
 [Scroll down]
 
 Note: o sistema respondeu automaticamente em menos de 3 segundos.
 Nunca dorme, sempre responde.
 
 E olha: gerou uma proposta em 45 segundos.
 O cliente vê exatamente o que ele pediu.
 Personalizado, profissional, automático.
 
 Tudo isso sem seu vendedor fazer nada."

TELA 3 - KPI DASHBOARD:
──────────────────────
"Agora os números finais. Vamos lá:

1. 450 leads processados este mês.
   Apenas qualificados à mão, seu vendedor ficaria preso por 2 semanas.
   O Nexus faz em tempo real.

2. Taxa de conversão: 12%
   Antes era 8%. Gande 4%.
   54 leads convertidos extra por mês.
   
3. Potencial: R$ 85.000
   Apenas em prospects qualificados.
   Seu vendedor trabalha no que importa.

4. Tempo de resposta: < 3 segundos
   24/7. Nunca cansa.
   
5. Acurácia: 87%
   87 de cada 100 leads que o Nexus classifica como HOT viram cliente.
   Você confia nos números.

[Mostrar gráfico]

Vê esse gráfico? Taxa de conversão crescendo de 6% para 12% em 4 semanas.
Isto é tendência. E não é por acaso.
É porque o Nexus qualifica melhor => seu vendedor vende mais."

TELA 4 - PIPELINE:
──────────────────
"Por último, o pipeline visual.

32 leads novos chegando.
28 já qualificados (passaram pelo scoring).
18 com proposta enviada.
8 já com contrato assinado.

Cada um tem um score.
Vermelho (🔥 HOT) = seu vendedor ataca agora.
Laranja (⚠️ WARM) = aguarda complemento.
Azul (❄️ COLD) = avalia depois, se tiver tempo.

É visual, é claro, qualquer vendedor entende.

E note: cada estágio tem um número. Você sabe exatamente quantos leads
cada vendedor tem em cada fase. Sem surpresas."

═══════════════════════════════════════════════════════════════════════════════
⚠️  COISAS QUE NÃO FAZER
═══════════════════════════════════════════════════════════════════════════════

❌ NÃO mostrar:
   • Código-fonte (F12 vai mostrar console limpo mesmo assim)
   • Settings/admin internal
   • Outras telas que não estão 100% prontas
   • Load times lento (tudo deve abrir em < 1 segundo)

❌ NÃO falar sobre:
   • Implementação técnica (código, banco de dados)
   • Problemas que teve no desenvolvimento
   • "A gente ainda tá melhorando..."
   
❌ NÃO erros:
   • Typos nas telas (revisa tudo)
   • Cores quebradas
   • Botões que não funcionam

═══════════════════════════════════════════════════════════════════════════════
✅ CHECKLIST PRÉ-APRESENTAÇÃO
═══════════════════════════════════════════════════════════════════════════════

HOJE (Sexta):
  [ ] Abrir cada tela no navegador (Chrome/Firefox)
  [ ] Verificar se todas as páginas carregam SEM ERROS
  [ ] Verificar se imagens aparecem
  [ ] Testar zoom in (150%)
  [ ] Testar responsividade (se necessário para backup mobile)

DOMINGO À NOITE:
  [ ] Setup: 4 abas abertas no notebook
  [ ] Tirar screenshots de cada tela (backup offline)
  [ ] Testar navegação entre abas rápida (Alt+Tab)
  [ ] Garantir que não tem abas extras abertas
  [ ] Montar projetor com laptop e testar resolução

SEGUNDA (1 hora antes):
  [ ] Abrir todas as 4 abas
  [ ] Testar projetor novo (resolução, cores, brilho)
  [ ] Verificar wi-fi (speed test: mínimo 5Mbps)
  [ ] Fazer print de cada tela (se internet falhar, você tem backup offline)

═══════════════════════════════════════════════════════════════════════════════
📱 PLANO B: Internet Cair
═══════════════════════════════════════════════════════════════════════════════

Se a internet cair during a apresentação (improvável, mas..):

1. Você já tem as páginas abertas (cached pelo navegador)
   → Elas continuam funcionando mesmo sem internet

2. Se o navegador não mostrar (improvável):
   → Você tem screenshots em alta resolução no Powerpoint
   → Pode apresentar as imagens estáticas
   → CEO vai entender igual

3. Se tudo falhar (muito improvável):
   → Você tem o smartphone com versão mobile
   → "Deixa eu mostrar no celular então"
   → Funciona igual

═══════════════════════════════════════════════════════════════════════════════
🎬 RESUMO DO FLUXO
═══════════════════════════════════════════════════════════════════════════════

1. CEO entra na sala → Você está com as 4 abas abertas, zoom 150%

2. Você começa: "Vamos lá. É simples. Mostra 4 telas."

3. Login (30s) → Inbox (1:30) → KPI (2:30) → Pipeline (1:30) = 6 minutos

4. CEO faz perguntas (3 min)

5. Você fecha com: "Custa R$ 1.800/mês. Começa terça-feira."

6. Contrato assinado ✅

═══════════════════════════════════════════════════════════════════════════════
"""

if __name__ == "__main__":
    print(PRESENTATION_GUIDE)

    with open("FRONTEND_PRESENTATION_GUIDE.txt", "w", encoding="utf-8") as f:
        f.write(PRESENTATION_GUIDE)

    print("\n\n✅ Guia salvo em: FRONTEND_PRESENTATION_GUIDE.txt")
