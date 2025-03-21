from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.api.endpoints.auth import get_current_user, get_current_admin_user
from app.services.image_processing import image_processing_service
from app.models.image_processing import (
    ProcessingResult, 
    ProcessingStatus, 
    ProcessingMode, 
    Image,
    Feedback
)
from app.schemas.image_processing import (
    ProcessingCreate,
    ProcessingResult as ProcessingResultSchema,
    ProcessingResultDetailed,
    FeedbackCreate,
    Feedback as FeedbackSchema,
    ImageUploadResponse
)
from app.schemas.user import User


# Create router
router = APIRouter()


@router.post("/upload-and-process", response_model=ImageUploadResponse)
async def upload_and_process_image(
    file: UploadFile = File(...),
    mode: ProcessingMode = Form(ProcessingMode.DESCRIPTION),
    custom_prompt: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Upload and process an image in one step.
    
    This endpoint allows users to upload an image and immediately process it with
    the specified mode. The image will be analyzed by a Vision Language Model (VLM)
    and then the result will be processed by a Language Model (LLM) to provide
    a detailed, accessible description.
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )
    
    try:
        # Process image with VLM and LLM
        image, processing_result = await image_processing_service.process_image(
            db=db,
            file=file,
            user_id=current_user.id,
            processing_mode=mode,
            custom_prompt=custom_prompt,
        )
        
        # Convert to Pydantic model
        from app.schemas.image_processing import Image as ImageSchema
        image_schema = ImageSchema.model_validate(image)
        
        return ImageUploadResponse(
            image=image_schema,
            message="Image uploaded and processing started",
            processing_id=processing_result.id,
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}",
        )


@router.post("/process/{image_id}", response_model=ProcessingResultSchema)
async def process_existing_image(
    image_id: int,
    processing_in: ProcessingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Process an existing image.
    
    This endpoint allows users to process an image that has already been uploaded.
    The image will be analyzed by a Vision Language Model (VLM) and then the result
    will be processed by a Language Model (LLM) to provide a detailed, accessible
    description.
    """
    # Get image
    image = db.query(Image).filter(Image.id == image_id).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    
    # Check if user has access to this image
    if image.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    try:
        # Create processing result record
        processing_result = ProcessingResult(
            image_id=image.id,
            status=ProcessingStatus.PENDING,
            mode=processing_in.mode,
            custom_prompt=processing_in.custom_prompt,
        )
        
        db.add(processing_result)
        db.commit()
        db.refresh(processing_result)
        
        # Process the image (in a real system, this would be a background task)
        # For simplicity, we're doing it synchronously here
        await image_processing_service._process_with_models(
            db=db,
            image=image,
            processing_result=processing_result,
            custom_prompt=processing_in.custom_prompt,
        )
        
        # Refresh processing result
        db.refresh(processing_result)
        
        return processing_result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}",
        )


@router.get("/results", response_model=List[ProcessingResultSchema])
def list_processing_results(
    skip: int = 0,
    limit: int = 100,
    status: Optional[ProcessingStatus] = None,
    mode: Optional[ProcessingMode] = None,
    image_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get list of processing results for the current user.
    """
    query = db.query(ProcessingResult).join(Image).filter(Image.user_id == current_user.id)
    
    if status:
        query = query.filter(ProcessingResult.status == status)
    
    if mode:
        query = query.filter(ProcessingResult.mode == mode)
    
    if image_id:
        query = query.filter(ProcessingResult.image_id == image_id)
    
    results = query.order_by(ProcessingResult.created_at.desc()).offset(skip).limit(limit).all()
    return results


@router.get("/results/all", response_model=List[ProcessingResultSchema])
def list_all_processing_results(
    skip: int = 0,
    limit: int = 100,
    status: Optional[ProcessingStatus] = None,
    mode: Optional[ProcessingMode] = None,
    image_id: Optional[int] = None,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get list of all processing results (admin only).
    """
    query = db.query(ProcessingResult).join(Image)
    
    if status:
        query = query.filter(ProcessingResult.status == status)
    
    if mode:
        query = query.filter(ProcessingResult.mode == mode)
    
    if image_id:
        query = query.filter(ProcessingResult.image_id == image_id)
    
    if user_id:
        query = query.filter(Image.user_id == user_id)
    
    results = query.order_by(ProcessingResult.created_at.desc()).offset(skip).limit(limit).all()
    return results


@router.get("/results/{result_id}", response_model=ProcessingResultDetailed)
def get_processing_result(
    result_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get processing result by ID.
    """
    result = db.query(ProcessingResult).filter(ProcessingResult.id == result_id).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing result not found",
        )
    
    # Get image
    image = db.query(Image).filter(Image.id == result.image_id).first()
    
    # Check if user has access to this image
    if image.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return result


@router.post("/feedback", response_model=FeedbackSchema)
def create_feedback(
    feedback_in: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create feedback for a processing result.
    """
    # Get processing result
    result = db.query(ProcessingResult).filter(ProcessingResult.id == feedback_in.processing_result_id).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing result not found",
        )
    
    # Get image
    image = db.query(Image).filter(Image.id == result.image_id).first()
    
    # Check if user has access to this image
    if image.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Check if feedback already exists
    existing_feedback = db.query(Feedback).filter(
        Feedback.processing_result_id == feedback_in.processing_result_id,
        Feedback.user_id == current_user.id
    ).first()
    
    if existing_feedback:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback already exists for this processing result",
        )
    
    # Create feedback
    feedback = Feedback(
        processing_result_id=feedback_in.processing_result_id,
        user_id=current_user.id,
        rating=feedback_in.rating,
        feedback_text=feedback_in.feedback_text,
        is_helpful=feedback_in.is_helpful,
        suggested_improvements=feedback_in.suggested_improvements,
    )
    
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    return feedback


@router.get("/feedback", response_model=List[FeedbackSchema])
def list_feedback(
    skip: int = 0,
    limit: int = 100,
    processing_result_id: Optional[int] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get list of feedback (admin only).
    """
    query = db.query(Feedback)
    
    if processing_result_id:
        query = query.filter(Feedback.processing_result_id == processing_result_id)
    
    feedback_list = query.order_by(Feedback.created_at.desc()).offset(skip).limit(limit).all()
    return feedback_list 