from pydantic import BaseModel
from typing import Optional


class RecognitionCreate(BaseModel):
    """Schema for creating a new recognition entry."""
    input_text: str  # Text received from frontend


class RecognitionResponse(BaseModel):
    """Schema for returning a recognition entry after AI processing."""
    id: int
    input_text: str
    image_url: Optional[str]  # URL of the stored image in S3
    result_text: Optional[str]  # AI processed text result

    class Config:
        from_attributes = True

