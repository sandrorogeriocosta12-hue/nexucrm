    """
    Engine básica de templates.
    """

    from typing import Dict, Any
    from string import Template

class TemplateEngine:
    """Engine básica para renderização de templates."""

async def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """Renderiza template com contexto."""
# Template básico para teste
        templates = {
            "onboarding_welcome": """
    <h1>Bem-vindo ao Vexus Service!</h1>
    <p>Olá, ${lead_name}!</p>
    <p>É um prazer ter você conosco.</p>
    """,
            "onboarding_setup": """
    <h1>Configuração Inicial</h1>
    <p>Olá, ${lead_name}!</p>
    <p>Vamos configurar seu Vexus.</p>
    """,
            "nurturing_intro": """
    <h1>Conheça o Vexus</h1>
    <p>Olá, ${lead_name}!</p>
    <p>Automação inteligente de vendas.</p>
    """,
            "nurturing_case_study": """
    <h1>Estudo de Caso</h1>
    <p>Como ${company_name} aumentou vendas em 300%.</p>
    """,
            "reengagement_miss_you": """
    <h1>Sentimos sua falta!</h1>
    <p>Olá, ${lead_name}!</p>
    <p>Notamos que você não está usando o Vexus.</p>
    """
        }

        template_content = templates.get(template_name, f"<h1>{template_name}</h1><p>Template não encontrado.</p>")

        return Template(template_content).safe_substitute(context)