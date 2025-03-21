from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from app.core.config import settings
from loguru import logger

# Create SQLAlchemy engine
if settings.DATABASE_URL is None:
    raise ValueError("Database URL is not configured. Check your environment variables.")

engine = create_engine(
    str(settings.DATABASE_URL),
    pool_pre_ping=True,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,  # Recycle connections after 30 minutes
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for models
Base = declarative_base()

def get_db():
    """
    Dependency function to get a database session.
    
    Yields:
        SQLAlchemy session that will be automatically closed after use.
    """
    db = SessionLocal()
    try:
        logger.debug("Database session created")
        yield db
    finally:
        db.close()
        logger.debug("Database session closed") 