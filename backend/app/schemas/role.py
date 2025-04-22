from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class RoleBase(BaseModel):
    """ロールの基本情報"""
    name: str = Field(..., description="ロール名")
    description: Optional[str] = Field(None, description="ロールの説明")
    permissions: List[str] = Field([], description="付与される権限のリスト")

class RoleCreate(RoleBase):
    """ロール作成リクエスト"""
    pass

class RoleUpdate(BaseModel):
    """ロール更新リクエスト"""
    name: Optional[str] = Field(None, description="ロール名")
    description: Optional[str] = Field(None, description="ロールの説明")
    permissions: Optional[List[str]] = Field(None, description="付与される権限のリスト")

class RoleResponse(RoleBase):
    """ロールレスポンス"""
    id: UUID = Field(..., description="ロールID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: Optional[datetime] = Field(None, description="更新日時")

    class Config:
        orm_mode = True

class RoleAssign(BaseModel):
    """ロール割り当てリクエスト"""
    user_id: UUID = Field(..., description="ユーザーID")
    role_id: UUID = Field(..., description="割り当てるロールID")

# 権限スキーマ
class PermissionBase(BaseModel):
    """権限の基本情報"""
    name: str = Field(..., description="権限名")
    description: Optional[str] = Field(None, description="権限の説明")

class PermissionCreate(PermissionBase):
    """権限作成リクエスト"""
    pass

class PermissionResponse(PermissionBase):
    """権限レスポンス"""
    id: UUID = Field(..., description="権限ID")
    created_at: datetime = Field(..., description="作成日時")

    class Config:
        orm_mode = True

# ロール権限スキーマ
class RolePermissionBase(BaseModel):
    """ロールと権限の関連付け基本情報"""
    role_id: UUID = Field(..., description="ロールID")
    permission_id: UUID = Field(..., description="権限ID")
    is_granted: bool = Field(True, description="権限が付与されているか")

class RolePermissionCreate(RolePermissionBase):
    """ロール権限作成リクエスト"""
    pass

class RolePermissionResponse(RolePermissionBase):
    """ロール権限レスポンス"""
    id: UUID = Field(..., description="ロール権限ID")
    created_at: datetime = Field(..., description="作成日時")

    class Config:
        orm_mode = True 