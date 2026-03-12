"""
Exemplos de uso do Vexus CRM Agêntico
"""

import asyncio
from vexus_crm.agents import AgentOrchestrator, LeadScoringAgent, ConversationAnalyzerAgent, AgentConfig, AgentType
from vexus_crm.automation import FlowBuilder
from vexus_crm.pipelines import VisualPipeline
from vexus_crm.omnichannel import OmnichannelManager, ChannelType


async def example_agent_scoring():
    """Exemplo 1: Score automático de lead com agentes"""
    
    print("\n=== EXEMPLO 1: Agent Scoring ===\n")
    
    orchestrator = AgentOrchestrator()
    
    lead_data = {
        "lead": {
            "id": "LEAD_001",
            "name": "Carlos Mendes",
            "email": "carlos@techcompany.com.br",
            "company": "Tech Solutions Brasil",
            "company_size": "enterprise",
            "budget": 150000,
            "budget_confirmed": True,
            "decision_maker": True,
            "urgency": "high"
        },
        "conversation_context": "Interessado em implementar CRM urgente. Já tem orçamento aprovado."
    }
    
    # Orquestrar agentes
    result = await orchestrator.orchestrate(lead_data)
    
    print(f"Lead: {lead_data['lead']['name']}")
    print(f"Score: {result['final_decision']['overall_score']}")
    print(f"Fase Recomendada: {result['final_decision']['recommended_phase']}")
    print(f"Próxima Ação: {result['final_decision']['next_action']}")
    print(f"Confidência: {result['final_decision']['confidence']}")


async def example_conversation_analysis():
    """Exemplo 2: Análise de conversa com IA"""
    
    print("\n=== EXEMPLO 2: Conversation Analysis ===\n")
    
    analyzer_config = AgentConfig(AgentType.CONVERSATION_ANALYZER)
    analyzer = ConversationAnalyzerAgent(analyzer_config)
    
    conversation = """
    Cliente: Olá! Gostaria de agendar uma consulta.
    Atendente: Claro! Qual dia você prefere?
    Cliente: Amanhã de manhã seria perfeito, tenho urgência.
    Atendente: Temos slots disponíveis às 10h e 11h.
    """
    
    data = {"conversation": conversation}
    result = await analyzer.process(data)
    
    print(f"Intenções: {result['intentions']}")
    print(f"Sentimento: {result['sentiment']}")
    print(f"Entidades: {result['entities']}")
    print(f"Urgência: {result['urgency_level']}")


def example_flow_builder():
    """Exemplo 3: Criar fluxo de automação"""
    
    print("\n=== EXEMPLO 3: Flow Builder ===\n")
    
    builder = FlowBuilder()
    
    # Criar fluxo WhatsApp
    flow_dict = builder.create_whatsapp_flow("Welcome Flow - WhatsApp")
    
    print(f"Flow ID: {flow_dict['id']}")
    print(f"Nome: {flow_dict['name']}")
    print(f"Blocos: {flow_dict['metadata']['block_count']}")
    print(f"Tem IA: {flow_dict['metadata']['has_ai']}")
    
    # Executar fluxo para um contato
    contact = {
        "id": "CONTACT_001",
        "name": "João Silva",
        "phone": "+5511999999999"
    }
    
    execution = builder.execute(contact)
    
    print(f"\nExecução:")
    print(f"ID: {execution['execution_id']}")
    print(f"Score Final: {execution['final_score']}")
    print(f"Passos: {len(execution['execution_path'])}")


def example_pipeline_visual():
    """Exemplo 4: Pipeline visual com cards"""
    
    print("\n=== EXEMPLO 4: Visual Pipeline ===\n")
    
    # Criar pipeline
    pipeline = VisualPipeline("Pipeline Vendas 2025")
    
    # Adicionar alguns cards
    card1 = pipeline.add_card(
        title="Acme Corp - Projeto de Integração",
        phase_name="📥 Leads",
        tags=["enterprise", "ai"],
        fields={
            "email": "contact@acme.com",
            "phone": "+5511988888888",
            "company": "Acme Corp"
        }
    )
    
    card1.ai_insights = {
        "score": 85,
        "confidence": 0.92,
        "recommendations": ["Enviar proposta", "Agendar demo"]
    }
    
    card2 = pipeline.add_card(
        title="Startup XYZ - Avaliação",
        phase_name="📞 Qualificação",
        tags=["startup"],
        fields={
            "email": "sales@xyz.com",
            "phone": "+5511977777777",
            "company": "Startup XYZ"
        }
    )
    
    card2.ai_insights = {
        "score": 65,
        "confidence": 0.88,
        "recommendations": ["Enviar mais informações", "Follow-up em 3 dias"]
    }
    
    # Obter dashboard
    dashboard = pipeline.get_dashboard_data()
    
    print(f"Pipeline: {dashboard['pipeline_name']}")
    print(f"Total de Cards: {dashboard['total_cards']}")
    print(f"Taxa de Conversão: {dashboard['conversion_rate']}%")
    print(f"Score Médio: {dashboard['average_lead_score']:.1f}")
    
    print("\nCards por Fase:")
    for phase_name, phase_data in dashboard['cards_by_phase'].items():
        print(f"  {phase_name}: {phase_data['count']} cards")


async def example_omnichannel():
    """Exemplo 5: Envio de mensagens omnichannel"""
    
    print("\n=== EXEMPLO 5: Omnichannel Messages ===\n")
    
    manager = OmnichannelManager()
    
    # Enviar via WhatsApp
    whatsapp_result = await manager.send_message(
        channel=ChannelType.WHATSAPP,
        content="Olá! 👋 Temos uma oferta especial para você hoje!",
        recipient="+5511999999999",
        metadata={"campaign": "special_offer"}
    )
    
    print(f"WhatsApp: {whatsapp_result['success']}")
    print(f"ID: {whatsapp_result['message_id']}")
    
    # Enviar via Email
    email_result = await manager.send_message(
        channel=ChannelType.EMAIL,
        content="Confira nossa nova solução de CRM inteligente!",
        recipient="contato@empresa.com.br",
        metadata={"subject": "Nova solução Vexus CRM"}
    )
    
    print(f"Email: {email_result['success']}")
    print(f"ID: {email_result['message_id']}")
    
    # Simular mensagem recebida
    incoming = {
        "message": "Ótimo! Gostaria de saber mais",
        "from": "+5511999999999",
        "to": "+5511988888888"
    }
    
    processed = await manager.process_incoming_message(ChannelType.WHATSAPP, incoming)
    
    print(f"Mensagem Processada: {processed['processed']}")


async def example_complete_flow():
    """Exemplo 6: Fluxo completo de um novo lead"""
    
    print("\n=== EXEMPLO 6: Complete Lead Flow ===\n")
    
    # 1. Novo lead chega pelo formulário
    new_lead = {
        "name": "Marina Costa",
        "email": "marina@hospital.com.br",
        "phone": "+5521987654321",
        "company": "Hospital São João",
        "interest": "Implementar CRM para agendamentos",
        "budget": 80000
    }
    
    print(f"1. Novo lead recebido: {new_lead['name']}")
    
    # 2. Score automático
    orchestrator = AgentOrchestrator()
    lead_data = {
        "lead": new_lead,
        "conversation_context": new_lead['interest']
    }
    
    score_result = await orchestrator.orchestrate(lead_data)
    lead_score = score_result['final_decision']['overall_score']
    
    print(f"2. Score calculado: {lead_score}/100")
    
    # 3. Criar no pipeline
    pipeline = VisualPipeline("Pipeline Hospitais")
    card = pipeline.add_card(
        title=new_lead['name'],
        phase_name="📥 Leads",
        fields={
            "email": new_lead['email'],
            "phone": new_lead['phone'],
            "company": new_lead['company']
        }
    )
    
    card.ai_insights = {
        "score": lead_score,
        "confidence": 0.9,
        "recommendations": ["Enviar welcome", "Agendar demo"]
    }
    
    print(f"3. Card criado no pipeline: {card.id}")
    
    # 4. Enviar mensagem de boas-vindas
    manager = OmnichannelManager()
    msg_result = await manager.send_message(
        channel=ChannelType.WHATSAPP,
        content=f"Olá {new_lead['name']}! 👋 Bem-vindo à Vexus CRM!",
        recipient=new_lead['phone']
    )
    
    print(f"4. Mensagem WhatsApp enviada: {msg_result['success']}")
    
    # 5. Obter status
    dashboard = pipeline.get_dashboard_data()
    
    print(f"5. Status do pipeline:")
    print(f"   - Total de leads: {dashboard['total_cards']}")
    print(f"   - Score médio: {dashboard['average_lead_score']:.1f}")


async def main():
    """Executar todos os exemplos"""
    
    print("🚀 Vexus CRM Agêntico - Exemplos de Uso")
    print("=" * 50)
    
    # Exemplos síncronos
    example_flow_builder()
    example_pipeline_visual()
    
    # Exemplos assíncronos
    await example_agent_scoring()
    await example_conversation_analysis()
    await example_omnichannel()
    await example_complete_flow()
    
    print("\n" + "=" * 50)
    print("✅ Todos os exemplos executados com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())
