from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import json

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Get a user by ID.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get a user by email.
    
    Args:
        db: Database session
        email: User email
        
    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Get a user by username.
    
    Args:
        db: Database session
        username: Username
        
    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.username == username).first()


def get_users(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    filter_params: Optional[Dict[str, Any]] = None
) -> List[User]:
    """
    Get a list of users.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        filter_params: Optional filter parameters
        
    Returns:
        List of User objects
    """
    query = db.query(User)
    
    if filter_params:
        if filter_params.get("is_active") is not None:
            query = query.filter(User.is_active == filter_params["is_active"])
        if filter_params.get("is_verified") is not None:
            query = query.filter(User.is_verified == filter_params["is_verified"])
        if filter_params.get("role") is not None:
            query = query.filter(User.role == filter_params["role"])
    
    return query.offset(skip).limit(limit).all()


def create_user(db: Session, user_in: UserCreate) -> User:
    """
    Create a new user.
    
    Args:
        db: Database session
        user_in: User data
        
    Returns:
        Created User object
        
    Raises:
        HTTPException: If user with the same email or username already exists
    """
    # Check if user with the same email already exists
    db_user = get_user_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    
    # Check if user with the same username already exists
    db_user = get_user_by_username(db, username=user_in.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username already exists",
        )
    
    # Create new user
    db_user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        preferred_language=user_in.preferred_language,
        settings="{}",
        is_active=True,
        is_verified=False,
        role=UserRole.USER,
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


def update_user(
    db: Session, 
    db_user: User, 
    user_in: UserUpdate
) -> User:
    """
    Update a user.
    
    Args:
        db: Database session
        db_user: User object to update
        user_in: User data to update
        
    Returns:
        Updated User object
    """
    update_data = user_in.model_dump(exclude_unset=True)
    
    # Handle settings separately as it needs to be stored as a JSON string
    if "settings" in update_data:
        settings = update_data.pop("settings")
        if settings is not None:
            db_user.settings = json.dumps(settings)
    
    # Update other fields
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    """
    Delete a user.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        True if user was deleted, False otherwise
    """
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    
    db.delete(user)
    db.commit()
    
    return True


def authenticate_user(
    db: Session, 
    username: str, 
    password: str
) -> Optional[User]:
    """
    Authenticate a user.
    
    Args:
        db: Database session
        username: Username
        password: Password
        
    Returns:
        User object if authentication is successful, None otherwise
    """
    user = get_user_by_username(db, username)
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


def change_password(
    db: Session, 
    user_id: int, 
    current_password: str, 
    new_password: str
) -> bool:
    """
    Change a user's password.
    
    Args:
        db: Database session
        user_id: User ID
        current_password: Current password
        new_password: New password
        
    Returns:
        True if password was changed, False otherwise
    """
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    
    if not verify_password(current_password, user.hashed_password):
        return False
    
    user.hashed_password = get_password_hash(new_password)
    db.add(user)
    db.commit()
    
    return True 