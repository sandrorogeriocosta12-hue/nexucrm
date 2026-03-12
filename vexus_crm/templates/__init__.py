"""
Templates por setor e caso de uso
"""

WHATSAPP_TEMPLATES = {
    "greeting": """
    Olá {contact_name}! 👋
    
    Bem-vindo ao {company_name}!
    
    Como posso ajudá-lo hoje?
    """,
    
    "schedule_option": """
    Perfeito! Para agendar, qual serviço você gostaria?
    
    {services_list}
    """,
    
    "pricing_info": """
    Aqui estão nossas opções:
    
    {pricing_list}
    
    Gostaria de mais detalhes?
    """,
    
    "follow_up": """
    Oi {contact_name}! 👋
    
    Tudo bem? Gostaria de saber se você teve oportunidade de revisar nossa proposta.
    
    Estou à disposição para esclarecer dúvidas! 😊
    """,
    
    "closing": """
    {contact_name}, estamos prontos para começar! 🚀
    
    Apenas alguns dados para finalizarmos:
    - Data de início preferida
    - Contato para billing
    
    Vamos lá?
    """
}

EMAIL_TEMPLATES = {
    "welcome": """
    Subject: Bem-vindo a {company_name}!
    
    Olá {contact_name},
    
    Obrigado por entrar em contato conosco!
    
    Sua proposta personalizada está em anexo.
    
    Qualquer dúvida, é só responder este email.
    
    Atenciosamente,
    {company_name}
    """,
    
    "proposal": """
    Subject: Sua proposta customizada - {company_name}
    
    Olá {contact_name},
    
    Preparamos uma proposta especial para {company_name}.
    
    Highlights:
    - Plano customizado
    - Suporte dedicado
    - ROI garantido
    
    Vamos conversar?
    
    {company_name}
    """,
    
    "follow_up": """
    Subject: Seguindo sobre nossa proposta
    
    Olá {contact_name},
    
    Gostaria de saber se você teve oportunidade de revisar nossa proposta.
    
    Tenho algumas ideias que podem adicionar ainda mais valor.
    
    Podemos marcar uma breve conversa?
    
    {company_name}
    """
}

INSTAGRAM_TEMPLATES = {
    "story": """
    📊 Você sabia?
    
    Nossas soluções aumentam produtividade em 40% 🚀
    
    Saiba mais no link da bio!
    """,
    
    "post": """
    🎯 5 dicas para melhorar seu CRM
    
    1. Automação inteligente
    2. IA generativa
    3. Análise preditiva
    4. Multi-canal
    5. Integração completa
    
    Qual você já usa?
    
    #CRM #Automação #IA
    """
}

SMS_TEMPLATES = {
    "appointment_reminder": "Olá {name}, seu agendamento é amanhã às {time}. Confirmar?",
    
    "verification_code": "Seu código de verificação é: {code}",
    
    "promotion": "🎉 Promoção especial! Desconto de {discount}% em {service}. Código: {code}",
    
    "feedback": "Como foi sua experiência? Deixe uma avaliação: {link}"
}


def get_template(channel: str, template_type: str, **kwargs) -> str:
    """Retorna template personalizado"""
    
    templates_map = {
        'whatsapp': WHATSAPP_TEMPLATES,
        'email': EMAIL_TEMPLATES,
        'instagram': INSTAGRAM_TEMPLATES,
        'sms': SMS_TEMPLATES
    }
    
    channel_templates = templates_map.get(channel, {})
    template = channel_templates.get(template_type, "Mensagem padrão")
    
    # Substituir variáveis
    for key, value in kwargs.items():
        template = template.replace(f"{{{key}}}", str(value))
    
    return template


__all__ = [
    'WHATSAPP_TEMPLATES',
    'EMAIL_TEMPLATES',
    'INSTAGRAM_TEMPLATES',
    'SMS_TEMPLATES',
    'get_template'
]
