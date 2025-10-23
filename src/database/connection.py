from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from src.config import settings

# Register pgvector with asyncpg
try:
    import pgvector.asyncpg
except ImportError:
    # Handle import error gracefully for testing
    import warnings
    warnings.warn("pgvector.asyncpg not available, some features may not work")
    pgvector = None

# Enhanced database connection with proper pooling and timeout settings
engine = create_engine(
    settings.database_url, 
    echo=False,
    # Connection pooling settings
    pool_size=10,  # Number of connections to maintain in the pool
    max_overflow=20,  # Additional connections that can be created on demand
    pool_timeout=30,  # Seconds to wait for a connection from the pool
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Verify connections before use
    # Connection timeout settings
    connect_args={
        "connect_timeout": 10,  # Connection timeout in seconds
        "application_name": "survey_engine"
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_independent_db_session() -> Session:
    """
    Get an independent database session for operations that should not be 
    affected by parent transaction rollbacks (e.g., audit logging).
    
    The caller is responsible for closing this session.
    """
    return SessionLocal()