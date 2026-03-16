"""Database setup using SQLAlchemy with PostgreSQL primary, SQLite fallback."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Try PostgreSQL first, fallback to SQLite
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Use absolute path for Railway persistence
    if os.getenv("RAILWAY_ENVIRONMENT"):
        DATABASE_URL = "sqlite:////app/vexus.db"
    else:
        DATABASE_URL = "sqlite:///./vexus.db"
    print("⚠️  No DATABASE_URL found, using SQLite fallback")

# Configure engine based on database type
if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=300,    # Recycle connections every 5 minutes
    )
    print("🐘 Using PostgreSQL database")
else:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    print("📱 Using SQLite database")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
