from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.sql import func
from datetime import datetime
from app.db.session import Base


class BaseModel(Base):
    """Base model class with common fields for all models."""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    ) 