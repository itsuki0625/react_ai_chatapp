from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import uuid

# 循環インポートを避けるため、PermissionRead のインポートを工夫するか、
# 完全なスキーマ定義をここに含めるか、型ヒントとして文字列を使う。
# ここでは PermissionRead をインポートする前提で進める。
from .permission import PermissionRead

class RoleBase(BaseModel):
    """ロールの基本情報"""
    name: str = Field(..., description="ロール名", examples=["admin", "premium_user"])
    description: Optional[str] = Field(None, description="ロールの説明", examples=["Administrator role with full access"])
    is_active: bool = True
    permissions: List[str] = Field([], description="付与される権限のリスト")

class RoleCreate(RoleBase):
    """ロール作成リクエスト"""
    pass

class RoleUpdate(BaseModel):
    """ロール更新リクエスト"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permissions: Optional[List[str]] = None

class RoleRead(RoleBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    permissions: List[PermissionRead] = []

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