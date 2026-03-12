"""
Modelos de dados para Vexus CRM Agêntico
Estrutura de banco de dados com SQLAlchemy 2.0
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


# ==================== AGENTES ====================


# ==================== KNOWLEDGE BASE ====================

class KnowledgeDocument(Base):
    """Documento armazenado para consulta RAG"""
    __tablename__ = "knowledge_documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, index=True)
    document_name = Column(String)
    file_path = Column(String)
    doc_type = Column(String)  # product_manual, faq, etc
    created_at = Column(DateTime, default=datetime.now)

    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete")


class KnowledgeChunk(Base):
    """Trecho de documento com embedding"""
    __tablename__ = "knowledge_chunks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("knowledge_documents.id"))
    chunk_text = Column(String)
    embedding = Column(JSON)  # storing vector as JSON list for now

    document = relationship("KnowledgeDocument", back_populates="chunks")



class AgentDecision(Base):
    """Registra decisões tomadas por agentes"""
    __tablename__ = "agent_decisions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_type = Column(String)  # lead_scoring, pipeline_manager, etc
    lead_id = Column(String, ForeignKey("leads.id"))
    decision_data = Column(JSON)  # Resultado da decisão
    confidence = Column(Float)
    model_used = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relacionamentos
    lead = relationship("Lead", back_populates="agent_decisions")


# ==================== LEADS & CONTACTS ====================

class Lead(Base):
    """Representa um lead no pipeline"""
    __tablename__ = "leads"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    email = Column(String, unique=True)
    phone = Column(String)
    company = Column(String)
    interest = Column(String)
    budget = Column(Float)
    source = Column(String)  # website, email, whatsapp, etc
    
    # Scoring & Status
    lead_score = Column(Integer, default=50)
    phase = Column(String, default="leads")  # leads, qualified, proposal, negotiation, closed
    status = Column(String, default="new")  # new, contacted, qualified, proposal_sent, closed_won, closed_lost
    
    # arbitrary metadata (not using SQLAlchemy's own metadata)
    meta = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    pipeline_cards = relationship("PipelineCard", back_populates="lead")
    messages = relationship("Message", back_populates="lead")
    agent_decisions = relationship("AgentDecision", back_populates="lead")


class Contact(Base):
    """Contato associado a um lead"""
    __tablename__ = "contacts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String, ForeignKey("leads.id"))
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    role = Column(String)  # decision_maker, influencer, user
    contact_type = Column(String)  # primary, secondary
    created_at = Column(DateTime, default=datetime.now)


# ==================== PIPELINE ====================

class Pipeline(Base):
    """Pipeline visual de vendas"""
    __tablename__ = "pipelines"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    description = Column(String)
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relacionamentos
    phases = relationship("PipelinePhase", back_populates="pipeline")
    cards = relationship("PipelineCard", back_populates="pipeline")


class PipelinePhase(Base):
    """Fase do pipeline (ex: Leads, Qualificação, Proposta)"""
    __tablename__ = "pipeline_phases"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    pipeline_id = Column(String, ForeignKey("pipelines.id"))
    name = Column(String)
    description = Column(String)
    position = Column(Integer)
    color = Column(String)  # Cor para UI
    
    # Relacionamentos
    pipeline = relationship("Pipeline", back_populates="phases")
    cards = relationship("PipelineCard", back_populates="phase")


class PipelineCard(Base):
    """Card no pipeline (representa um lead/deal)"""
    __tablename__ = "pipeline_cards"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    pipeline_id = Column(String, ForeignKey("pipelines.id"))
    phase_id = Column(String, ForeignKey("pipeline_phases.id"))
    lead_id = Column(String, ForeignKey("leads.id"))
    
    # Dados do card
    title = Column(String)
    description = Column(String)
    tags = Column(JSON)
    assigned_to = Column(JSON)  # Lista de user_ids
    
    # IA Insights
    ai_insights = Column(JSON)  # {score, confidence, recommendations}
    ai_last_update = Column(DateTime)
    
    # Status
    status = Column(String, default="in_progress")  # in_progress, review, done, blocked
    due_date = Column(DateTime)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    pipeline = relationship("Pipeline", back_populates="cards")
    phase = relationship("PipelinePhase", back_populates="cards")
    lead = relationship("Lead", back_populates="pipeline_cards")


# ==================== FLUXOS ====================

class FlowDefinition(Base):
    """Definição de um fluxo de automação"""
    __tablename__ = "flow_definitions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    channel = Column(String)  # whatsapp, email, instagram, etc
    description = Column(String)
    created_by = Column(String)
    
    # Estrutura do fluxo
    blocks_json = Column(JSON)  # Blocos do fluxo
    connections_json = Column(JSON)  # Conexões entre blocos
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    executions = relationship("FlowExecution", back_populates="flow")


class FlowExecution(Base):
    """Registro de execução de um fluxo"""
    __tablename__ = "flow_executions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    flow_id = Column(String, ForeignKey("flow_definitions.id"))
    lead_id = Column(String, ForeignKey("leads.id"))
    contact_id = Column(String)
    
    # Execução
    execution_data = Column(JSON)  # Resultado da execução
    collected_data = Column(JSON)  # Dados coletados durante execução
    final_score = Column(Integer)
    
    # Status
    status = Column(String)  # completed, in_progress, error
    error_message = Column(String)
    
    # Tracking
    started_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime)
    
    # Relacionamentos
    flow = relationship("FlowDefinition", back_populates="executions")


# ==================== OMNICHANNEL ====================

class Channel(Base):
    """Configuração de canal de comunicação"""
    __tablename__ = "channels"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)  # whatsapp, email, instagram, etc
    channel_type = Column(String)
    is_enabled = Column(Boolean, default=True)
    credentials = Column(JSON)  # Credenciais do canal (encrypted em produção)
    config = Column(JSON)  # Configurações adicionais
    created_at = Column(DateTime, default=datetime.now)


class Message(Base):
    """Mensagem enviada ou recebida"""
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String, ForeignKey("leads.id"))
    channel = Column(String)  # whatsapp, email, instagram, etc
    
    # Conteúdo
    content = Column(String)
    attachments = Column(JSON)
    
    # Comunicação
    sender = Column(String)
    recipient = Column(String)
    direction = Column(String)  # inbound, outbound
    
    # Processamento de IA
    ai_processed = Column(Boolean, default=False)
    ai_intent = Column(String)  # schedule, pricing, question, info
    ai_sentiment = Column(String)  # positive, negative, neutral
    ai_entities = Column(JSON)  # Entidades extraídas
    
    # Status
    status = Column(String)  # sent, delivered, read, failed
    error_message = Column(String)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    lead = relationship("Lead", back_populates="messages")


class ConversationThread(Base):
    """Agrupa mensagens em conversas por contato"""
    __tablename__ = "conversation_threads"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String, ForeignKey("leads.id"))
    channel = Column(String)
    contact_id = Column(String)
    
    # Metadata
    message_count = Column(Integer, default=0)
    last_message_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Análise
    conversation_summary = Column(String)
    key_topics = Column(JSON)
    overall_sentiment = Column(String)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

# ==================== CAMPANHAS ====================

class Campaign(Base):
    """Campanhas de marketing/vendas"""
    __tablename__ = "campaigns"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    description = Column(String)
    status = Column(String, default="draft")  # draft, active, paused, completed
    launch_date = Column(DateTime)
    end_date = Column(DateTime)
    budget = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

# ==================== ANALYTICS ====================

class LeadEvent(Base):
    """Registra eventos de um lead (mudança de fase, contato, etc)"""
    __tablename__ = "lead_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String, ForeignKey("leads.id"))
    
    # Evento
    event_type = Column(String)  # created, scored, contacted, phase_changed, closed
    event_data = Column(JSON)
    
    # Rastreamento
    created_at = Column(DateTime, default=datetime.now)


class Report(Base):
    """Relatórios gerados"""
    __tablename__ = "reports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    report_type = Column(String)  # pipeline, sales, conversion, ai_insights
    
    # Dados
    filters = Column(JSON)  # Filtros aplicados
    data = Column(JSON)  # Dados do relatório
    
    # Geração
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    period_start = Column(DateTime)
    period_end = Column(DateTime)


# ==================== CONFIGURAÇÃO ====================

class Config(Base):
    """Configurações globais do CRM"""
    __tablename__ = "configs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String, unique=True)
    value = Column(JSON)
    description = Column(String)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class User(Base):
    """Usuários do CRM"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    email = Column(String, unique=True)
    password_hash = Column(String)  # Deve ser hasheado com bcrypt
    role = Column(String)  # admin, manager, user
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)


# ==================== ÍNDICES & CONSTRAINTS ====================

# Índices para performance
# CREATE INDEX idx_leads_score ON leads(lead_score DESC);
# CREATE INDEX idx_cards_phase ON pipeline_cards(phase_id);
# CREATE INDEX idx_messages_lead ON messages(lead_id);
# CREATE INDEX idx_conversations_lead ON conversation_threads(lead_id);

# Foreign keys com constraints
# ALTER TABLE lead_events ADD FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE;
# ALTER TABLE agent_decisions ADD FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE;

# Exemplo de migração Alembic:
# alembic revision --autogenerate -m "Create initial schema"
# alembic upgrade head
