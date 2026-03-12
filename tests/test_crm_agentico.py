"""
Testes para o CRM Agêntico Vexus
"""

import pytest

pytest.skip("legacy crm agentico tests disabled", allow_module_level=True)
import asyncio
from vexus_crm.agents import AgentOrchestrator, LeadScoringAgent, AgentConfig, AgentType
from vexus_crm.automation import FlowBuilder, BlockType
from vexus_crm.pipelines import VisualPipeline, CardStatus
from vexus_crm.omnichannel import OmnichannelManager, ChannelType


class TestAgents:
    """Testes dos agentes de IA"""

    @pytest.mark.asyncio
    async def test_lead_scoring_agent(self):
        """Testa agent de scoring de leads"""
        config = AgentConfig(AgentType.LEAD_SCORING)
        agent = LeadScoringAgent(config)

        data = {
            "lead": {
                "company_size": "enterprise",
                "budget_confirmed": True,
                "decision_maker": True,
                "urgency": "high",
            }
        }

        result = await agent.process(data)

        assert "score" in result
        assert result["score"] > 0
        assert result["confidence"] > 0
        assert "breakdown" in result

    @pytest.mark.asyncio
    async def test_agent_orchestrator(self):
        """Testa orquestrador de agentes"""
        orchestrator = AgentOrchestrator()

        lead_data = {
            "lead": {
                "id": "TEST_001",
                "name": "Test Lead",
                "company": "Test Corp",
                "budget": 50000,
                "budget_confirmed": True,
                "decision_maker": True,
                "urgency": "high",
            },
            "conversation_context": "Interessado em CRM",
        }

        result = await orchestrator.orchestrate(lead_data)

        assert "agent_decisions" in result
        assert "final_decision" in result
        assert result["final_decision"]["overall_score"] > 0


class TestFlowBuilder:
    """Testes do construtor de fluxos"""

    def test_create_block(self):
        """Testa criação de blocos"""
        builder = FlowBuilder()

        block = builder.create_block(BlockType.MESSAGE, config={"message": "Olá!"})

        assert block.type == BlockType.MESSAGE
        assert block.config["message"] == "Olá!"

    def test_connect_blocks(self):
        """Testa conexão entre blocos"""
        builder = FlowBuilder()

        block1 = builder.create_block(BlockType.START)
        block2 = builder.create_block(BlockType.MESSAGE)

        builder.connect(block1, block2)

        assert block2.id in block1.next_blocks

    def test_create_whatsapp_flow(self):
        """Testa criação de fluxo WhatsApp"""
        builder = FlowBuilder()

        flow = builder.create_whatsapp_flow("Test Flow")

        assert flow["name"] == "Test Flow" or "WhatsApp" in flow["name"]
        assert len(flow["blocks"]) > 0
        assert flow["metadata"]["has_ai"] == True

    def test_execute_flow(self):
        """Testa execução de fluxo"""
        builder = FlowBuilder()
        builder.create_whatsapp_flow("Test")

        contact = {"id": "CONTACT_001", "name": "Test"}
        execution = builder.execute(contact)

        assert execution["execution_id"]
        assert execution["contact_id"] == "CONTACT_001"
        assert len(execution["execution_path"]) > 0


class TestPipeline:
    """Testes do pipeline visual"""

    def test_create_pipeline(self):
        """Testa criação de pipeline"""
        pipeline = VisualPipeline("Test Pipeline")

        assert pipeline.name == "Test Pipeline"
        assert len(pipeline.phases) > 0
        assert len(pipeline.cards) == 0

    def test_add_card(self):
        """Testa adição de card"""
        pipeline = VisualPipeline("Test")

        card = pipeline.add_card(title="Test Lead", phase_name="📥 Leads", tags=["test"])

        assert card.title == "Test Lead"
        assert card.id in pipeline.cards
        assert "test" in card.tags

    def test_move_card(self):
        """Testa movimento de card"""
        pipeline = VisualPipeline("Test")

        card = pipeline.add_card("Test", "📥 Leads")

        success = pipeline.move_card(card.id, "📞 Qualificação")

        assert success == True
        assert pipeline.cards[card.id].phase_id != ""

    def test_dashboard_data(self):
        """Testa geração de dashboard"""
        pipeline = VisualPipeline("Test")

        for i in range(3):
            card = pipeline.add_card(f"Lead {i}", "📥 Leads")
            card.ai_insights = {"score": 50 + i * 10}

        dashboard = pipeline.get_dashboard_data()

        assert dashboard["total_cards"] == 3
        assert dashboard["average_lead_score"] > 0
        assert "📥 Leads" in dashboard["cards_by_phase"]


class TestOmnichannel:
    """Testes do gerenciador omnichannel"""

    @pytest.mark.asyncio
    async def test_send_message_whatsapp(self):
        """Testa envio via WhatsApp"""
        manager = OmnichannelManager()

        result = await manager.send_message(
            channel=ChannelType.WHATSAPP,
            content="Test message",
            recipient="+5511999999999",
        )

        assert result["success"] == True
        assert "message_id" in result

    @pytest.mark.asyncio
    async def test_send_message_email(self):
        """Testa envio via Email"""
        manager = OmnichannelManager()

        result = await manager.send_message(
            channel=ChannelType.EMAIL,
            content="Test email",
            recipient="test@example.com",
        )

        assert result["success"] == True

    @pytest.mark.asyncio
    async def test_disabled_channel(self):
        """Testa canal desabilitado"""
        manager = OmnichannelManager()

        # Instagram disabled by default
        result = await manager.send_message(
            channel=ChannelType.INSTAGRAM, content="Test", recipient="@user"
        )

        assert result["success"] == False

    @pytest.mark.asyncio
    async def test_process_incoming_message(self):
        """Testa processamento de mensagem recebida"""
        manager = OmnichannelManager()

        data = {
            "message": "Olá, gostaria de agendar",
            "from": "+5511999999999",
            "to": "+5511988888888",
        }

        result = await manager.process_incoming_message(ChannelType.WHATSAPP, data)

        assert result["processed"] == True

    @pytest.mark.asyncio
    async def test_conversation_history(self):
        """Testa histórico de conversa"""
        manager = OmnichannelManager()

        # Adicionar algumas mensagens
        await manager.send_message(
            channel=ChannelType.WHATSAPP, content="Message 1", recipient="contact_001"
        )

        await manager.send_message(
            channel=ChannelType.WHATSAPP, content="Message 2", recipient="contact_001"
        )

        history = manager.get_conversation_history("contact_001")

        assert len(history) == 2


class TestIntegration:
    """Testes de integração entre módulos"""

    @pytest.mark.asyncio
    async def test_complete_lead_flow(self):
        """Testa fluxo completo de um novo lead"""

        # 1. Score o lead
        orchestrator = AgentOrchestrator()
        lead_data = {
            "lead": {
                "id": "INT_001",
                "name": "Integration Test Lead",
                "company": "Test Corp",
                "budget": 100000,
                "budget_confirmed": True,
                "decision_maker": True,
                "urgency": "high",
            },
            "conversation_context": "Quer implementar CRM",
        }

        score_result = await orchestrator.orchestrate(lead_data)
        lead_score = score_result["final_decision"]["overall_score"]

        # 2. Adicione ao pipeline
        pipeline = VisualPipeline("Integration Test")
        card = pipeline.add_card(title=lead_data["lead"]["name"], phase_name="📥 Leads")

        card.ai_insights = {"score": lead_score, "confidence": 0.9}

        # 3. Envie mensagem
        manager = OmnichannelManager()
        msg_result = await manager.send_message(
            channel=ChannelType.WHATSAPP,
            content=f"Olá {lead_data['lead']['name']}!",
            recipient="+5511999999999",
        )

        # Validações finais
        assert lead_score > 50
        assert card.id in pipeline.cards
        assert msg_result["success"] == True


# Executar testes
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
