from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from db.database import Base

class ProcessedData(Base):
    __tablename__ = "processed_data"
    
    id = Column(Integer, primary_key=True, index=True)
    input_text = Column(Text, nullable=False)
    image_url_1 = Column(String(500), nullable=False)
    image_url_2 = Column(String(500), nullable=False)
    processed_text = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    processed_at = Column(TIMESTAMP(timezone=True), nullable=True, onupdate=func.now())