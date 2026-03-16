"""Database setup using SQLAlchemy with PostgreSQL primary, SQLite fallback."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Try PostgreSQL first, fallback to SQLite
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Use a relative SQLite file to avoid permission issues in container environments
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
    # Ensure the directory exists for SQLite file paths
    if DATABASE_URL.startswith("sqlite://"):
        # Strip sqlite:// prefix to extract file path
        sqlite_path = DATABASE_URL[len("sqlite://"):]
        # Normalize leading slashes (sqlite:////path should map to /path)
        if sqlite_path.startswith("//"):
            sqlite_path = sqlite_path[1:]
        sqlite_path = os.path.normpath(sqlite_path)
        sqlite_dir = os.path.dirname(sqlite_path)
        if sqlite_dir:
            try:
                os.makedirs(sqlite_dir, exist_ok=True)
            except PermissionError:
                # In some environments (read-only root), cannot create directories.
                # We'll rely on the existing directory structure.
                pass

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
