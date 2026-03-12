import pytest
import os
import sys
from typing import Generator
from unittest.mock import patch

# Adicionar o diretório raiz ao path para importar os módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Configurar variáveis de ambiente para testes
os.environ["FLASK_ENV"] = "testing"
os.environ["TESTING"] = "True"
os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"


@pytest.fixture
def mock_redis():
    """Mock para Redis"""
    with patch("redis.Redis") as mock:
        mock.get = mock.return_value = None
        mock.set = mock.return_value = True
        mock.delete = mock.return_value = True
        mock.exists = mock.return_value = False
        yield mock


@pytest.fixture
def mock_send_email():
    """Mock para envio de emails"""
    with patch("smtplib.SMTP") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def sample_user_data():
    """Dados de exemplo para usuário"""
    return {
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User",
        "company": "Test Company",
        "phone": "+5511999999999",
    }


@pytest.fixture
def sample_lead_data():
    """Dados de exemplo para lead"""
    return {
        "email": "lead@example.com",
        "full_name": "Lead Test",
        "company": "Lead Company",
        "phone": "+5511888888888",
        "source": "website",
        "status": "new",
    }


# ==================== DATABASE SETUP ====================
from httpx import AsyncClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Import all models FIRST to register them
from vexus_crm.models import (
    User,
    Lead,
    Contact,
    Pipeline,
    PipelinePhase,
    PipelineCard,
    FlowDefinition,
    FlowExecution,
    Message,
    ConversationThread,
    KnowledgeDocument,
    KnowledgeChunk,
    AgentDecision,
    LeadEvent,
    Campaign,
    Base,
)

# Create in-memory SQLite engine
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"
engine_test = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)


# Enable foreign keys
@event.listens_for(engine_test, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Create all tables in test database
Base.metadata.create_all(bind=engine_test)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def get_db_test():
    """Test database session generator"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# Import app_server AFTER setting up the test database
from app_server import app
from vexus_crm.database import get_db

# Override dependency injection for app
app.dependency_overrides[get_db] = get_db_test


@pytest.fixture(scope="function", autouse=True)
def reset_db():
    """Reset database before each test"""
    # Clear all data
    Session = TestingSessionLocal()
    for table in reversed(Base.metadata.sorted_tables):
        Session.execute(table.delete())
    Session.commit()
    Session.close()
    yield
    # Cleanup after test
    Session = TestingSessionLocal()
    for table in reversed(Base.metadata.sorted_tables):
        Session.execute(table.delete())
    Session.commit()
    Session.close()


@pytest.fixture
def client():
    """Test HTTP client"""
    return AsyncClient(app=app, base_url="http://test")


@pytest.fixture
def db_session():
    """Database session for tests"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
async def client():
    """FastAPI test client - uses cleanup_db fixture for setup"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
