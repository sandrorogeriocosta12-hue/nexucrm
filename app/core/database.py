    """
    Configuração básica de banco de dados.
    """

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, Session
    from sqlalchemy.ext.declarative import declarative_base

# Configuração básica para testes
    DATABASE_URL = "sqlite:///./test.db"

    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base = declarative_base()

def get_db() -> Session:
    """Retorna sessão de banco de dados."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()