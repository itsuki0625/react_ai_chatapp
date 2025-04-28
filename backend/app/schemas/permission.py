import uuid
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class PermissionBase(BaseModel):
    name: str = Field(..., examples=["read_users"])
    description: Optional[str] = Field(None, examples=["Permission to read user data"])

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(PermissionBase):
    name: Optional[str] = None
    description: Optional[str] = None

class PermissionRead(PermissionBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True # SQLAlchemyモデルからPydanticモデルへの変換を有効化 (v1)
        # from_attributes = True # Pydantic v2 の場合 