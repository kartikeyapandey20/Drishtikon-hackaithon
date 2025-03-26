from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, func
from db.database import Base

class News(Base):
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(500), nullable=False, unique=True)
    source = Column(String(100), nullable=False)
    published_at = Column(TIMESTAMP(timezone=True), nullable=False)
    image_url = Column(String(500), nullable=True)
    author = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())