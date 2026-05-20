"""Database abstraction for API v1 pipeline workflows.

This file adds a minimal SQLAlchemy schema to support multiple sales funnels,
stages, and deals for the Vexus CRM pipeline interface.
"""

import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nexus_pipeline.db")
CONNECT_ARGS = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=CONNECT_ARGS, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()

DEFAULT_PIPELINE_ID = "pipeline_default"
DEFAULT_PIPELINE_NAME = "Funil Principal"
DEFAULT_PIPELINE_DESCRIPTION = "Pipeline padrão do Nexus CRM para leads e negociações."


class Pipeline(Base):
    __tablename__ = "pipelines"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    stages = relationship("PipelineStage", back_populates="pipeline", cascade="all, delete-orphan")
    deals = relationship("Deal", back_populates="pipeline", cascade="all, delete-orphan")


class PipelineStage(Base):
    __tablename__ = "pipeline_stages"

    id = Column(String, primary_key=True)
    pipeline_id = Column(String, ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    order = Column(Integer, nullable=False, default=0)
    color = Column(String, nullable=False, default="#64748B")
    created_at = Column(DateTime, default=datetime.utcnow)

    pipeline = relationship("Pipeline", back_populates="stages")
    deals = relationship("Deal", back_populates="stage")


class Deal(Base):
    __tablename__ = "deals"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    value = Column(Float, nullable=False, default=0.0)
    pipeline_id = Column(String, ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False)
    stage_id = Column(String, ForeignKey("pipeline_stages.id"), nullable=False)
    contact_id = Column(String, nullable=True)
    probability = Column(Float, nullable=False, default=0.0)

    # Ordenação (Trello/Trello-like)
    position = Column(Integer, nullable=False, default=0)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    stage = relationship("PipelineStage", back_populates="deals")
    pipeline = relationship("Pipeline", back_populates="deals")



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(engine)
    seed_default_pipeline()


def seed_default_pipeline():
    from sqlalchemy import select

    with SessionLocal() as db:
        pipeline = db.get(Pipeline, DEFAULT_PIPELINE_ID)
        if pipeline:
            return

        pipeline = Pipeline(
            id=DEFAULT_PIPELINE_ID,
            name=DEFAULT_PIPELINE_NAME,
            description=DEFAULT_PIPELINE_DESCRIPTION,
        )
        db.add(pipeline)
        db.flush()

        stage_data = [
            ("stage_1", "Novo", 1, "#3B82F6"),
            ("stage_2", "Contato", 2, "#8B5CF6"),
            ("stage_3", "Proposta", 3, "#EC4899"),
            ("stage_4", "Ganhou", 4, "#10B981"),
        ]

        for stage_id, name, order, color in stage_data:
            db.add(PipelineStage(
                id=stage_id,
                pipeline_id=pipeline.id,
                name=name,
                order=order,
                color=color,
            ))

        sample_deals = [
            {
                "id": "deal_001",
                "title": "Empresa XYZ - Pacote Premium",
                "value": 15000.0,
                "stage_id": "stage_2",
                "contact_id": "contact_1",
                "probability": 0.65,
                "position": 0,
                "notes": "Cliente potencial em reunião",
            },
            {
                "id": "deal_002",
                "title": "Startup ABC - Consultoria",
                "value": 5000.0,
                "stage_id": "stage_1",
                "contact_id": "contact_2",
                "probability": 0.30,
                "position": 0,
                "notes": "Primeiro contato realizado",
            },
        ]


        for deal_data in sample_deals:
            db.add(Deal(
                id=deal_data["id"],
                title=deal_data["title"],
                value=deal_data["value"],
                pipeline_id=pipeline.id,
                stage_id=deal_data["stage_id"],
                contact_id=deal_data["contact_id"],
                probability=deal_data["probability"],
                position=deal_data.get("position", 0),
                notes=deal_data["notes"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ))


        db.commit()


# Backwards compatibility aliases used by api_v1_routes.
PipelineStageModel = PipelineStage
DealModel = Deal
