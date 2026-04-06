#!/usr/bin/env python3
"""Test PostgreSQL connection"""
import os
from sqlalchemy import create_engine, text

# Set PostgreSQL URL
DATABASE_URL = "postgresql://vexus:password@localhost/vexus_crm"

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print("✅ PostgreSQL connection successful!")
        print(f"Version: {version[:60]}...")
except Exception as e:
    print(f"❌ PostgreSQL connection failed: {e}")