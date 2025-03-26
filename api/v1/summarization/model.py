from sqlalchemy import Column, Integer, String
from db.database import Base

class TextData(Base):
    __tablename__ = "texts"

    id = Column(Integer, primary_key=True, index=True)
    input_text = Column(String, nullable=False)
    result_text = Column(String, nullable=True)  # AI result
