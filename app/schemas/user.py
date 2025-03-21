from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any, List
import json
from datetime import datetime
from app.models.user import UserRole


class UserBase(BaseModel):
    """Base schema for user data."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    full_name: Optional[str] = None
    preferred_language: Optional[str] = "en"
    
    class Config:
        from_attributes = True


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8)
    password_confirm: str
    
    @validator("password_confirm")
    def passwords_match(cls, v, values):
        """Validate that the passwords match."""
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v


class UserUpdate(BaseModel):
    """Schema for updating user data."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    full_name: Optional[str] = None
    preferred_language: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class UserInDBBase(UserBase):
    """Base schema for user data from database."""
    id: int
    is_active: bool
    is_verified: bool
    role: UserRole
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class User(UserInDBBase):
    """Schema for returning user data."""
    settings: Dict[str, Any] = Field(default_factory=dict)
    
    @validator("settings", pre=True)
    def parse_settings(cls, v):
        """Parse settings from JSON string to dict."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v


class UserWithToken(User):
    """Schema for returning user data with access token."""
    access_token: str
    token_type: str = "bearer"


class Token(BaseModel):
    """Schema for authentication token."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for data stored in JWT token."""
    username: str
    role: UserRole 