from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime
from .base import TimestampMixin

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    grade: Optional[int] = None
    class_number: Optional[str] = None
    student_number: Optional[str] = None
    profile_image_url: Optional[str] = None

class UserCreate(UserBase):
    password: str
    role_id: UUID
    school_id: Optional[UUID] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    grade: Optional[int] = None
    class_number: Optional[str] = None
    student_number: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase, TimestampMixin):
    id: UUID
    role_id: UUID
    school_id: Optional[UUID]
    is_active: bool
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[UUID] = None 