from sqlalchemy import Boolean, Column, String, Enum
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class UserRole(enum.Enum):
    """Enum for user roles."""
    ADMIN = "admin"
    USER = "user"


class User(BaseModel):
    """
    User model for authentication and authorization.
    
    Attributes:
        email: Unique email address for the user
        username: Unique username for the user
        hashed_password: Hashed password for authentication
        full_name: User's full name
        is_active: Whether the user account is active
        is_verified: Whether the user's email has been verified
        role: User's role for authorization
        preferred_language: User's preferred language for descriptions
        settings: JSON field for user-specific settings
    """
    
    __tablename__ = "users"
    
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    preferred_language = Column(String, default="en")
    settings = Column(String, default="{}")  # Store JSON settings as string
    
    # Relationships
    images = relationship("Image", back_populates="user", cascade="all, delete-orphan") 