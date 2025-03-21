from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.api.endpoints.auth import get_current_user, get_current_admin_user
from app.services.user import (
    get_user_by_id,
    get_users,
    update_user,
    delete_user,
    change_password,
)
from app.schemas.user import User, UserUpdate


# Create router
router = APIRouter()


class PasswordChangeRequest(BaseModel):
    """Schema for password change request."""
    current_password: str
    new_password: str
    confirm_password: str


@router.get("/me", response_model=User)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current user information.
    """
    return current_user


@router.put("/me", response_model=User)
def update_current_user(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update current user information.
    """
    updated_user = update_user(db, current_user, user_in)
    return updated_user


@router.post("/me/change-password")
def update_current_user_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Change current user password.
    """
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )
    
    if password_data.new_password == password_data.current_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )
    
    success = change_password(
        db, 
        current_user.id, 
        password_data.current_password, 
        password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )
    
    return {"message": "Password updated successfully"}


# Admin routes

@router.get("/", response_model=List[User])
def list_users(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get list of users (admin only).
    """
    filter_params = {}
    if is_active is not None:
        filter_params["is_active"] = is_active
    if is_verified is not None:
        filter_params["is_verified"] = is_verified
    
    users = get_users(db, skip=skip, limit=limit, filter_params=filter_params)
    return users


@router.get("/{user_id}", response_model=User)
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get user by ID (admin only).
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.put("/{user_id}", response_model=User)
def update_user_by_admin(
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update user by ID (admin only).
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    updated_user = update_user(db, user, user_in)
    return updated_user


@router.delete("/{user_id}")
def delete_user_by_admin(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete user by ID (admin only).
    """
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own user account",
        )
    
    success = delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return {"message": "User deleted successfully"} 