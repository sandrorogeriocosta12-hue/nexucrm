    """
    Templates de email para automação de vendas.
    """

    from string import Template
    from typing import Dict, Any

class EmailTemplate:
    """Classe base para templates de email."""

def __init__(self, name: str, subject: str, html_template: str, text_template: str = None):
        self.name = name
        self.subject = subject
        self.html_template = html_template
        self.text_template = text_template or self._generate_text_template(html_template)

def _generate_text_template(self, html_template: str) -> str:
        """Gera template de texto a partir do HTML."""
# Remove tags HTML e converte para texto
        import re
        text = re.sub(r'<[^>]+>', '', html_template)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

def render(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Renderiza template com contexto."""
        html = Template(self.html_template).safe_substitute(context)
        text = Template(self.text_template).safe_substitute(context)

        return {
            "subject": Template(self.subject).safe_substitute(context),
            "html": html,
            "text": text
        }

# Templates padrão do sistema
    TEMPLATES = {
    "onboarding_welcome": EmailTemplate(
    name="onboarding_welcome",
    subject="🎉 Bem-vindo(a) ao Vexus Service, ${lead_name}!",
    html_template="""









    🎉 Bem-vindo(a) ao Vexus!

    Sua jornada para vendas mais inteligentes começa agora



    Olá, ${lead_name}!

    É um prazer ter você conosco no Vexus Service! Estamos muito animados em fazer parte do crescimento do seu negócio.


    📍 Primeiros Passos:


    Complete seu perfil - Adicione informações da sua empresa

    Conecte suas ferramentas - Integre com CRM, email, etc.

    Configure seu primeiro funil - Crie sequências automáticas

    Importe seus contatos - Comece a nutrir seus leads




    👉 Acessar Meu Dashboard


    🎯 O que você pode fazer agora:


    Automatize follow-ups - Nunca perca um lead

    Personalize comunicações - Email com nome e contexto

    Analise performance - Veja o que está funcionando

    Escale suas vendas - Faça mais com menos esforço



    🤝 Suporte Dedicado:

    Nossa equipe está aqui para ajudar! Se tiver qualquer dúvida:


    Email: suporte@vexus.com

    WhatsApp: (11) 99999-9999

    Horário: Seg-Sex, 9h-18h




    💡 Dica Rápida: Clientes que completam o setup em 48h têm 3x mais chances de sucesso!



    Vexus Service - Transformando vendas com inteligência artificial

    Este é um email automático. Para ajustar preferências, clique aqui.





    """
    ),

    "onboarding_setup": EmailTemplate(
    name="onboarding_setup",
    subject="Configuração Inicial do Vexus - Primeiros Passos",
    html_template="""









    ⚙️ Configuração Inicial

    Vamos configurar seu Vexus para máximo desempenho



    Olá, ${lead_name}!

    Espero que esteja gostando do Vexus! Agora vamos configurar tudo para você começar a automatizar suas vendas.


    📋 Checklist de Configuração (15 minutos):



    1. Perfil da Empresa ✅


    Logo da empresa

    Cores da marca

    Assinatura de email

    Domínio personalizado





    2. Integrações 🔗


    CRM (HubSpot, Salesforce, Pipedrive)

    Email (Gmail, Outlook)

    Calendário (Google, Outlook)

    WhatsApp Business





    3. Primeira Sequência 🎯


    Template de boas-vindas

    Follow-up automático

    Segmentação de leads

    Gatilhos personalizados





    🚀 Iniciar Configuração


    🎥 Tutorial Rápido:

    Assista este vídeo de 5 minutos para ver como configurar:


    ▶️ Assistir Tutorial


    📞 Precisa de Ajuda?

    Nossa equipe pode fazer a configuração para você:


    Setup Completo: 30 min com especialista

    Treinamento: 1 hora para sua equipe

    Migração: Trazemos seus dados antigos




    ⚠️ Importante: A configuração inicial é fundamental para o sucesso. Clientes bem configurados têm 47% mais conversões.






    """
    ),

    "nurturing_intro": EmailTemplate(
    name="nurturing_intro",
    subject="${lead_name}, conheça o Vexus - Automação Inteligente de Vendas",
    html_template="""









    🤖 Vexus Service

    Automação Inteligente que Transforma Vendas



    Olá, ${lead_name}!

    Você já imaginou ter um assistente de vendas 24/7 que nunca esquece um follow-up, personaliza cada comunicação e aumenta suas conversões automaticamente?


    O Vexus Service é a plataforma de automação de vendas mais inteligente do mercado, criada para equipes que querem escalar resultados sem aumentar o trabalho.


    ✨ O que o Vexus faz por você:



    🤖


    Automação Inteligente

    Sequências automáticas que se adaptam ao comportamento do lead




    🎯


    Segmentação Avançada

    Envie a mensagem certa para a pessoa certa na hora certo




    📊


    Analytics Preditivo

    Saiba quais leads vão converter antes mesmo deles saberem




    🔄


    Integração Total

    Conecte com CRM, email, WhatsApp, site e muito mais




    "Com o Vexus, nossa taxa de conversão aumentou 217% em 3 meses. A automação inteligente mudou completamente nosso funil de vendas."



    — Maria Silva, Diretora de Vendas na TechCompany



    🎬 Agendar Demonstração Gratuita


    📈 Resultados Comprovados:


    +300% em leads qualificados

    -65% no tempo de resposta

    +47% na taxa de conversão

    -80% no trabalho manual




    🎁 Oferta Especial: Os primeiros 100 inscritos deste mês ganham 30 dias grátis + configuração personalizada.





    """
    ),

    "nurturing_case_study": EmailTemplate(
    name="nurturing_case_study",
    subject="Case: Como ${company_name} aumentou vendas em 300% com Vexus",
    html_template="""









    📈 Estudo de Caso Real

    ${company_name} + Vexus = Crescimento Exponencial



    Como uma empresa de SaaS aumentou vendas em 300%


    Cliente: ${company_name} (empresa de software B2B)

    Desafio: Funil de vendas manual, follow-ups perdidos, baixa conversão

    Solução: Automação Inteligente Vexus

    Período: 6 meses




    300%

    Aumento em Vendas



    217%

    Mais Leads Qualificados



    65%

    Menos Trabalho Manual




    🎯 O Desafio:

    A ${company_name} tinha um processo de vendas totalmente manual:


    Leads perdidos no email

    Follow-ups esquecidos

    Comunicação genérica

    Dificuldade em escalar

    Conversão abaixo do esperado



    🚀 A Solução Vexus:


    1. Sequência de Onboarding Inteligente

    Criamos uma sequência de 7 emails automáticos que:


    Segmenta leads por comportamento

    Personaliza conteúdo por indústria

    Envia no momento ideal

    Ajusta frequência automaticamente



    2. Lead Scoring Automático

    Sistema que pontua leads em tempo real:


    Engajamento com emails

    Visitas ao site

    Download de materiais

    Interação com conteúdo



    3. Integração Completa

    Tudo conectado em um só lugar:


    CRM Pipedrive

    Email Marketing

    WhatsApp Business

    Google Analytics




    "O Vexus transformou completamente nosso processo de vendas. Em 3 meses já vimos resultados impressionantes. A automação inteligente identifica oportunidades que antes perdíamos."



    — João Santos, CEO da ${company_name}


    📊 Resultados em Números:
































    Métrica 	Antes 	Depois 	Variação
    Taxa de Conversão 	2.3% 	7.4% 	+221%
    Leads/Mês 	120 	380 	+217%
    Vendas/Mês 	8 	32 	+300%
    Tempo de Resposta 	8.5 horas 	15 minutos 	-97%



    📖 Ler Estudo Completo
    🎬 Ver Demonstração


    🤔 Como isso se aplica ao seu negócio?

    Independente do seu tamanho ou indústria, o Vexus pode ajudar você a:


    Automatizar processos manuais

    Converter mais leads em clientes

    Reduzir custos operacionais

    Escalar sem aumentar a equipe




    💡 Próximo Passo: Agende uma demonstração personalizada para ver como o Vexus pode impactar seus resultados.






    """
    ),

    "reengagement_miss_you": EmailTemplate(
    name="reengagement_miss_you",
    subject="${lead_name}, sentimos sua falta no Vexus! 🥺",
    html_template="""









    🥺 Sentimos Sua Falta!

    Notamos que você não está usando o Vexus ultimamente



    Oi, ${lead_name}!

    Espero que esteja tudo bem! Notamos que você não tem usado o Vexus Service recentemente e queríamos checar se está tudo certo por aí.


    Sabemos que a rotina pode ser corrida, mas ficamos preocupados em não estarmos ajudando você da melhor forma possível.


    🤔 Alguma dessas situações aconteceu?


    Teve dificuldades na configuração?

    Não encontrou tempo para implementar?

    Precisa de ajuda com algo específico?

    Não viu os resultados esperados?



    Seja qual for o motivo, queremos ajudar você a ter sucesso!



    🎁 Presente de Volta!

    Para te dar um empurrãozinho, preparamos uma oferta especial:

    30 Dias Grátis + Setup Personalizado

    Nosso time especialista vai configurar tudo para você e sua equipe!




    🚀 Quero Meu Presente de Volta!


    🆕 O que há de novo no Vexus?

    Enquanto você estava fora, lançamos várias novidades:


    Integração com WhatsApp Business - Agora você pode automatizar conversas

    Analytics Preditivo 2.0 - Previsões ainda mais precisas

    Novos templates profissionais - Templates prontos para cada situação

    Dashboard aprimorado - Mais intuitivo e poderoso



    📊 Veja o que nossos clientes estão alcançando:


    Média de 214% mais leads com automação inteligente

    Redução de 78% no trabalho manual

    Aumento de 47% nas conversões

    Economia média de 15h/semana por vendedor




    💬 Feedback Importante: Sua opinião é fundamental para nós. Se houver algo que podemos melhorar, por favor nos conte!




    Esperamos ver você de volta!

    A equipe Vexus





    """
    )
    }

class TemplateManager:
    """Gerenciador de templates de email."""

def __init__(self):
    self.templates = TEMPLATES

def get_template(self, name: str) -> EmailTemplate:
    """Obtém template pelo nome."""
    template = self.templates.get(name)
    if not template:
    raise ValueError(f"Template '{name}' não encontrado")
    return template

def add_template(self, template: EmailTemplate) -> None:
    """Adiciona novo template."""
    self.templates[template.name] = template

def list_templates(self) -> Dict[str, str]:
    """Lista todos os templates disponíveis."""
    return {name: template.subject for name, template in self.templates.items()}

def render_template(self, name: str, context: Dict[str, Any]) -> Dict[str, str]:
    """Renderiza template com contexto."""
    template = self.get_template(name)
    return template.render(context)

# Factory para templates dinâmicos
class TemplateFactory:
    """Factory para criar templates dinâmicos."""

@staticmethod
def create_custom_template(name: str, subject: str, content: str) -> EmailTemplate:
    """Cria template customizado."""
    html_template = f"""









    {subject}



    {content}

    Vexus Service - Transformando vendas com inteligência artificial

    Para ajustar preferências, clique aqui.






    """

    return EmailTemplate(
    name=name,
    subject=subject,
    html_template=html_template
    )

@staticmethod
def create_promotional_template(product: str, discount: str) -> EmailTemplate:
    """Cria template promocional."""
    return EmailTemplate(
    name=f"promo_{product.lower().replace(' ', '_')}",
    subject=f"🎁 Oferta Especial: {discount} OFF em {product}",
    html_template=f"""









    🚀 OFERTA POR TEMPO LIMITADO!

    {discount} de desconto em {product}



    Olá, ${{lead_name}}!

    Temos uma oferta especial preparada especialmente para você!


    {discount} OFF



    ⏰ OFERTA TERMINA EM: 48:00:00


    Esta é sua chance de obter {product} com um desconto exclusivo que não será repetido!


    ✨ O que você recebe:


    {product} com {discount} de desconto

    Configuração personalizada gratuita

    Treinamento para sua equipe

    Suporte prioritário por 30 dias

    Garantia de satisfação de 14 dias




    🎯 QUERO MEU DESCONTO!



    ⚠️ Atenção: Esta oferta é exclusiva para clientes selecionados e termina em 48 horas. Não será repetida!








    """
    )

    __all__ = [
    'EmailTemplate',
    'TemplateManager',
    'TemplateFactory',
    'TEMPLATES'
    ]