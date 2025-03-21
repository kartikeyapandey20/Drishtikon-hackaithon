from sqlalchemy import Column, String, Integer, ForeignKey, Text, Float, Enum, JSON, Boolean
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class ImageType(enum.Enum):
    """Enum for types of images."""
    SCENE = "scene"
    DOCUMENT = "document"
    PRODUCT = "product"
    CHART = "chart"
    TEXT = "text"
    OTHER = "other"


class ProcessingStatus(enum.Enum):
    """Enum for processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingMode(enum.Enum):
    """Enum for processing modes."""
    # Standard modes
    DESCRIPTION = "description"  # General description
    OCR = "ocr"  # Optical character recognition
    SCENE_ANALYSIS = "scene_analysis"  # Detailed scene breakdown
    DOCUMENT_READING = "document_reading"  # Read document content
    ACCESSIBILITY = "accessibility"  # Accessible description
    CUSTOM = "custom"  # Custom prompt
    
    # Specialized modes for visually impaired users
    CURRENCY_RECOGNITION = "currency_recognition"  # Identify and describe currency
    COLOR_ANALYSIS = "color_analysis"  # Analyze and describe colors
    OBJECT_RECOGNITION = "object_recognition"  # Spatial relationships for navigation
    FACE_RECOGNITION = "face_recognition"  # Recognize faces and expressions
    PRODUCT_IDENTIFICATION = "product_identification"  # Identify products and packaging
    HAZARD_DETECTION = "hazard_detection"  # Detect potential hazards
    TRANSPORT_INFORMATION = "transport_information"  # Extract public transport info
    MEDICINE_IDENTIFICATION = "medicine_identification"  # Identify medications
    EMOTIONAL_ANALYSIS = "emotional_analysis"  # Analyze emotions of people
    IMAGE_COMPARISON = "image_comparison"  # Compare two images
    DOCUMENT_SUMMARIZATION = "document_summarization"  # Summarize document content
    AUDIO_DESCRIPTION = "audio_description"  # Format for audio description


class Image(BaseModel):
    """
    Model to store uploaded images and their processing information.
    
    Attributes:
        filename: Original filename
        file_path: Storage path
        file_size: Size in bytes
        mime_type: MIME type of the image
        width: Image width in pixels
        height: Image height in pixels
        user_id: Foreign key to the user who uploaded the image
        image_type: Type of the image (scene, document, etc.)
        description: Optional user-provided description
        tags: Optional user-provided tags as JSON array
        location: Optional location data as JSON
        metadata: Additional metadata as JSON
    """
    
    __tablename__ = "images"
    
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    width = Column(Integer)
    height = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))
    image_type = Column(Enum(ImageType), default=ImageType.OTHER)
    description = Column(Text)
    tags = Column(JSON)
    location = Column(JSON)
    metadata = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="images")
    processing_results = relationship("ProcessingResult", back_populates="image", cascade="all, delete-orphan")


class ProcessingResult(BaseModel):
    """
    Model to store results of image processing by VLM and LLM.
    
    Attributes:
        image_id: Foreign key to the processed image
        status: Processing status
        mode: Processing mode (description, OCR, etc.)
        vlm_provider: Provider of VLM (OpenAI, Google, etc.)
        vlm_model: Name of the VLM model used
        vlm_response: Raw response from the VLM
        vlm_processing_time: Time taken by VLM in seconds
        llm_provider: Provider of LLM (OpenAI, Google, etc.)
        llm_model: Name of the LLM model used
        llm_response: Raw response from the LLM
        llm_processing_time: Time taken by LLM in seconds
        final_output: Final processed output for the user
        prompt_template: Template used for the VLM/LLM
        custom_prompt: Custom prompt if provided
        confidence_score: Confidence score of the result (0-1)
        error_message: Error message if failed
    """
    
    __tablename__ = "processing_results"
    
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False)
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING, nullable=False)
    mode = Column(Enum(ProcessingMode), default=ProcessingMode.DESCRIPTION, nullable=False)
    
    # VLM details
    vlm_provider = Column(String)
    vlm_model = Column(String)
    vlm_response = Column(Text)
    vlm_processing_time = Column(Float)
    
    # LLM details
    llm_provider = Column(String)
    llm_model = Column(String)
    llm_response = Column(Text)
    llm_processing_time = Column(Float)
    
    # Output and processing details
    final_output = Column(Text)
    prompt_template = Column(String)
    custom_prompt = Column(Text)
    confidence_score = Column(Float)
    error_message = Column(Text)
    
    # Relationships
    image = relationship("Image", back_populates="processing_results")
    feedback = relationship("Feedback", back_populates="processing_result", uselist=False, cascade="all, delete-orphan")


class Feedback(BaseModel):
    """
    Model to store user feedback on processing results.
    
    Attributes:
        processing_result_id: Foreign key to the processing result
        user_id: Foreign key to the user who provided feedback
        rating: User rating (1-5)
        feedback_text: Detailed feedback
        is_helpful: Whether the result was helpful
        suggested_improvements: Suggested improvements
    """
    
    __tablename__ = "feedback"
    
    processing_result_id = Column(Integer, ForeignKey("processing_results.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer)  # 1-5 rating
    feedback_text = Column(Text)
    is_helpful = Column(Boolean)
    suggested_improvements = Column(Text)
    
    # Relationships
    processing_result = relationship("ProcessingResult", back_populates="feedback")
    user = relationship("User") 