"""
Modelos básicos para suportar automação de vendas.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Lead(Base):
    """Modelo básico de Lead."""

    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    company = Column(String(255))
    phone = Column(String(50))
    status = Column(String(50), default="new")
    last_contacted = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Task(Base):
    """Modelo básico de Task."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    assigned_to = Column(Integer)
    due_date = Column(DateTime)
    priority = Column(String(20), default="medium")
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Company(Base):
    """Modelo de Empresa (Tenant)."""

    __tablename__ = "companies"

    id = Column(String(36), primary_key=True, index=True)  # UUID
    name = Column(String(255), nullable=False, unique=True)
    owner_id = Column(Integer, nullable=False)  # FK para User.id
    stripe_customer_id = Column(String(255), nullable=True)
    subscription_id = Column(String(255), nullable=True)
    plan = Column(String(50), default="starter")  # starter, professional, business
    status = Column(String(50), default="active")  # active, trial, suspended, cancelled
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    """Modelo de Usuário com multi-tenant."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), default="member")  # admin, manager, member
    company_id = Column(String(36), nullable=True, index=True)  # FK para Company.id
    is_verified = Column(Boolean, default=False)  # Email verification status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
