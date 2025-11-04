"""
Database connection and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from core.config import get_settings

settings = get_settings()

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=settings.environment == "development"
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


async def init_db():
    """Initialize database tables"""
    from models.database import APIKey, Deployment, DeploymentHistory
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Get database session - used as FastAPI dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
