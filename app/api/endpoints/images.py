from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.api.endpoints.auth import get_current_user, get_current_admin_user
from app.services.storage import storage_service
from app.models.image_processing import Image, ImageType
from app.schemas.image_processing import ImageCreate, ImageUpdate, Image as ImageSchema, ImageUploadResponse
from app.schemas.user import User


# Create router
router = APIRouter()


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    image_type: Optional[ImageType] = Form(ImageType.OTHER),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Upload an image file.
    
    This endpoint allows users to upload an image file with optional metadata.
    The image will be stored and basic information will be returned.
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )
    
    try:
        # Save file to storage
        filename, file_path, file_size = await storage_service.save_file(file)
        
        # Create image record
        image = Image(
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.content_type,
            user_id=current_user.id,
            image_type=image_type,
            description=description,
        )
        
        db.add(image)
        db.commit()
        db.refresh(image)
        
        # Convert to Pydantic model
        image_schema = ImageSchema.model_validate(image)
        
        return ImageUploadResponse(
            image=image_schema,
            message="Image uploaded successfully",
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading image: {str(e)}",
        )


@router.get("/", response_model=List[ImageSchema])
def list_images(
    skip: int = 0,
    limit: int = 100,
    image_type: Optional[ImageType] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get list of images for the current user.
    """
    query = db.query(Image).filter(Image.user_id == current_user.id)
    
    if image_type:
        query = query.filter(Image.image_type == image_type)
    
    images = query.order_by(Image.created_at.desc()).offset(skip).limit(limit).all()
    return images


@router.get("/all", response_model=List[ImageSchema])
def list_all_images(
    skip: int = 0,
    limit: int = 100,
    image_type: Optional[ImageType] = None,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get list of all images (admin only).
    """
    query = db.query(Image)
    
    if image_type:
        query = query.filter(Image.image_type == image_type)
    
    if user_id:
        query = query.filter(Image.user_id == user_id)
    
    images = query.order_by(Image.created_at.desc()).offset(skip).limit(limit).all()
    return images


@router.get("/{image_id}", response_model=ImageSchema)
def get_image(
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get image by ID.
    """
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
    
    return image


@router.put("/{image_id}", response_model=ImageSchema)
def update_image(
    image_id: int,
    image_in: ImageUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update image metadata.
    """
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
    
    # Update image fields
    update_data = image_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(image, field, value)
    
    db.add(image)
    db.commit()
    db.refresh(image)
    
    return image


@router.delete("/{image_id}")
async def delete_image(
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete an image.
    """
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
    
    # Delete file from storage
    file_path = image.file_path
    await storage_service.delete_file(file_path)
    
    # Delete image record
    db.delete(image)
    db.commit()
    
    return {"message": "Image deleted successfully"} 