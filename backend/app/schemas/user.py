from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict
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
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('パスワードは8文字以上である必要があります')
        return v

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
    roles: List[str]  # ロール名のリスト（"admin", "teacher", "student"など）
    permissions: List[str]  # 権限コードのリスト
    school_id: Optional[UUID] = None
    is_active: bool
    last_login_at: Optional[datetime] = None
    is_email_verified: bool
    has_2fa_enabled: bool = False

    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    permissions: List[str]  # 権限コードのリスト

class RoleUpdate(RoleBase):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None

class RoleResponse(RoleBase, TimestampMixin):
    id: UUID
    permissions: List[Dict]  # 権限情報のリスト

    class Config:
        from_attributes = True

class PermissionBase(BaseModel):
    code: str
    description: str

class PermissionResponse(PermissionBase):
    id: UUID

    class Config:
        from_attributes = True

class UserSettings(BaseModel):
    notification_preferences: Dict
    ui_preferences: Dict
    last_updated: datetime

    class Config:
        from_attributes = True

class UserRoleAssignment(BaseModel):
    user_id: UUID
    role_id: UUID 