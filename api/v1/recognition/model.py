from sqlalchemy import Column, Integer, String
from db.database import Base

class RecognitionData(Base):
    """
    Database model for storing text and image data for AI recognition processing.
    """
    __tablename__ = "recognition"

    id = Column(Integer, primary_key=True, index=True)
    input_text = Column(String, nullable=False)  # Text received from frontend
    image_url = Column(String, nullable=False)  # S3 bucket URL of uploaded image
    result_text = Column(String, nullable=True)  # AI-processed text result
