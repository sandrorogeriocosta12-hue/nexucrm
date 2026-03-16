#!/usr/bin/env python3
"""
Migration script to move data from SQLite to PostgreSQL
"""
import os
import sqlite3
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import psycopg2
from psycopg2 import sql

# Database URLs
SQLITE_URL = "sqlite:///./vexus.db"
POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/vexus_db")

def get_sqlite_data():
    """Extract all data from SQLite database"""
    sqlite_engine = create_engine(SQLITE_URL)
    sqlite_conn = sqlite_engine.connect()

    # Get all table names
    result = sqlite_conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in result.fetchall() if not row[0].startswith('sqlite_')]

    data = {}
    for table in tables:
        result = sqlite_conn.execute(f"SELECT * FROM {table}")
        columns = result.keys()
        rows = result.fetchall()
        data[table] = {
            'columns': columns,
            'rows': rows
        }

    sqlite_conn.close()
    return data

def create_postgres_tables(postgres_engine, sqlite_data):
    """Create tables in PostgreSQL based on SQLite schema"""
    from vexus_crm.models import Base

    # Create all tables
    Base.metadata.create_all(bind=postgres_engine)
    print("✅ PostgreSQL tables created")

def migrate_data(postgres_engine, sqlite_data):
    """Migrate data from SQLite to PostgreSQL"""
    postgres_conn = postgres_engine.connect()

    for table_name, table_data in sqlite_data.items():
        if not table_data['rows']:
            print(f"⚠️  Skipping empty table: {table_name}")
            continue

        columns = table_data['columns']
        rows = table_data['rows']

        print(f"📊 Migrating {len(rows)} records from {table_name}")

        # Insert data
        for row in rows:
            # Create INSERT statement
            placeholders = ', '.join(['%s'] * len(columns))
            column_names = ', '.join(columns)

            insert_query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"

            try:
                postgres_conn.execute(insert_query, row)
            except Exception as e:
                print(f"❌ Error inserting into {table_name}: {e}")
                # Try to continue with other records

    postgres_conn.commit()
    postgres_conn.close()
    print("✅ Data migration completed")

def main():
    print("🚀 Starting SQLite to PostgreSQL migration...")

    # Extract data from SQLite
    print("📖 Extracting data from SQLite...")
    sqlite_data = get_sqlite_data()
    print(f"📋 Found {len(sqlite_data)} tables with data")

    # Create PostgreSQL engine
    print("🔌 Connecting to PostgreSQL...")
    postgres_engine = create_engine(POSTGRES_URL)

    try:
        # Test connection
        postgres_engine.connect()
        print("✅ PostgreSQL connection successful")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("💡 Make sure PostgreSQL is running and DATABASE_URL is correct")
        return

    # Create tables
    print("🏗️  Creating PostgreSQL tables...")
    create_postgres_tables(postgres_engine, sqlite_data)

    # Migrate data
    print("📤 Migrating data...")
    migrate_data(postgres_engine, sqlite_data)

    print("🎉 Migration completed successfully!")
    print("🔄 You can now update your DATABASE_URL to use PostgreSQL")

if __name__ == "__main__":
    main()