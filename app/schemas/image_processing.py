from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import json
from app.models.image_processing import ImageType, ProcessingStatus, ProcessingMode


class ImageBase(BaseModel):
    """Base schema for image data."""
    description: Optional[str] = None
    image_type: Optional[ImageType] = ImageType.OTHER
    tags: Optional[List[str]] = None
    location: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class ImageCreate(ImageBase):
    """Schema for creating a new image."""
    pass


class ImageUpdate(ImageBase):
    """Schema for updating image data."""
    description: Optional[str] = None
    image_type: Optional[ImageType] = None
    tags: Optional[List[str]] = None
    location: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class Image(ImageBase):
    """Schema for returning image data."""
    id: int
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    @validator("tags", "location", "metadata", pre=True)
    def parse_json(cls, v):
        """Parse JSON strings to Python objects."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v
    
    class Config:
        from_attributes = True


class ProcessingBase(BaseModel):
    """Base schema for processing data."""
    mode: ProcessingMode = ProcessingMode.DESCRIPTION
    custom_prompt: Optional[str] = None
    
    class Config:
        from_attributes = True


class ProcessingCreate(ProcessingBase):
    """Schema for creating a new processing request."""
    pass


class ProcessingResultBase(ProcessingBase):
    """Base schema for processing result data."""
    id: int
    image_id: int
    status: ProcessingStatus
    vlm_provider: Optional[str] = None
    vlm_model: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    final_output: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProcessingResult(ProcessingResultBase):
    """Schema for returning processing result data."""
    vlm_response: Optional[str] = None
    vlm_processing_time: Optional[float] = None
    llm_response: Optional[str] = None
    llm_processing_time: Optional[float] = None
    prompt_template: Optional[str] = None
    error_message: Optional[str] = None


class ProcessingResultDetailed(ProcessingResult):
    """Schema for returning detailed processing result data."""
    image: Image


class FeedbackBase(BaseModel):
    """Base schema for feedback data."""
    rating: Optional[int] = Field(None, ge=1, le=5)
    feedback_text: Optional[str] = None
    is_helpful: Optional[bool] = None
    suggested_improvements: Optional[str] = None
    
    class Config:
        from_attributes = True


class FeedbackCreate(FeedbackBase):
    """Schema for creating feedback."""
    processing_result_id: int


class FeedbackUpdate(FeedbackBase):
    """Schema for updating feedback."""
    pass


class Feedback(FeedbackBase):
    """Schema for returning feedback data."""
    id: int
    processing_result_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class ImageUploadResponse(BaseModel):
    """Schema for response after image upload."""
    image: Image
    message: str = "Image uploaded successfully"
    processing_id: Optional[int] = None 