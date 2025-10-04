from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# Create PostgreSQL engine
postgres_engine = create_engine(settings.database_url)

# Create session factory
PostgresSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=postgres_engine)

# Create declarative base
Base = declarative_base()


def get_postgres_db() -> Session:
    """Dependency function to get PostgreSQL database session"""
    db = PostgresSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_postgres_engine():
    """Get the PostgreSQL engine instance"""
    return postgres_engine


async def check_postgres_health() -> bool:
    """Check PostgreSQL database health"""
    try:
        with postgres_engine.connect() as connection:
            connection.info
            logger.info("PostgreSQL health check passed")
            return True
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        return False
