import logging
from pydantic import BaseModel, EmailStr, validator, Field, computed_field
from typing import Optional, List, Dict, Any, Set
from uuid import UUID
from datetime import datetime
from enum import Enum
from .base import TimestampMixin
from app.models.user import User as UserModel, UserRole as UserRoleModel, Role, Permission
from .subscription import SubscriptionResponse # SubscriptionResponse をインポート

# Logger をモジュールレベルで定義
logger = logging.getLogger(__name__)

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    UNPAID = "unpaid"

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    # name: str # computed_field で生成するのでコメントアウトまたは削除
    # grade, class_number, student_number はOptionalのまま残すか、必要なら削除
    # grade: Optional[int] = None # ★ 下の UserUpdate で定義するので削除
    class_number: Optional[str] = None
    student_number: Optional[str] = None
    profile_image_url: Optional[str] = None
    # role: UserRole = UserRole.STUDENT # computed_field で生成するのでコメントアウトまたは削除

class UserCreate(UserBase):
    # UserCreate では full_name を受け取るように変更
    full_name: str # Userモデルに合わせて full_name を追加
    password: str
    status: UserStatus = UserStatus.PENDING # 作成時のデフォルトステータス
    # role: UserRole = UserRole.STUDENT # 作成時にロールを指定できるようにする (デフォルトはSTUDENT)
    role: str = "フリー" # 型を str に変更し、デフォルト値を文字列で設定 (生徒からフリーへ変更)
    # ★ UserCreate 時にも grade, prefecture を受け付ける場合はここに追加
    # grade: Optional[str] = None
    # prefecture: Optional[str] = None

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('パスワードは8文字以上である必要があります')
        if not any(c.islower() for c in v):
            raise ValueError('パスワードには小文字を含める必要があります')
        if not any(c.isupper() for c in v):
            raise ValueError('パスワードには大文字を含める必要があります')
        if not any(c.isdigit() for c in v):
            raise ValueError('パスワードには数字を含める必要があります')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    # name ではなく full_name を更新対象に
    full_name: Optional[str] = None # full_name を追加
    password: Optional[str] = None # パスワード変更用
    grade: Optional[str] = None # Integer から String に変更
    prefecture: Optional[str] = None # prefecture を追加
    class_number: Optional[str] = None
    student_number: Optional[str] = None
    profile_image_url: Optional[str] = None
    role: Optional[str] = None # 文字列として受け入れるように変更
    status: Optional[UserStatus] = None # ステータス変更用

# Revert inheritance order for UserInDBBase and ensure fields match model
class UserInDBBase(UserBase, TimestampMixin): # Inherit from UserBase and TimestampMixin again
    id: UUID
    hashed_password: str
    full_name: str # From User model
    is_verified: bool # From User model (was is_email_verified in schema)
    status: UserStatus # From User model
    is_2fa_enabled: bool = False # From User model
    school_id: Optional[UUID] = None # From User model
    # last_login_at is tricky, it comes from UserLoginInfo relation
    last_login_at: Optional[datetime] = None

# DBから読み込む際のスキーマ (UserInDBBase を継承)
class UserInDB(UserInDBBase):
    user_roles: List[Any] = [] # Include user_roles for relationship loading

    class Config:
        from_attributes = True # DBモデルからの読み込み設定

# APIレスポンス用のスキーマ (パスワード非表示)
class UserResponse(TimestampMixin):
    id: UUID
    email: EmailStr

    # --- Include source fields needed for computed fields (no exclude=True) ---
    full_name: str
    is_verified: bool
    user_roles: List[Any] = []
    status: UserStatus # status を直接含める
    login_info: Optional[Any] = None # 型は UserLoginInfo だが、循環参照を避けるため Any も可
    grade: Optional[str] = None # grade を追加 (モデルに合わせて Optional[str])
    prefecture: Optional[str] = None # prefecture を追加 (モデルに合わせて Optional[str])
    profile_image_url: Optional[str] = None # 追加
    # --- End source fields ---

    # --- computed fields (these will be in the final JSON) ---
    @computed_field
    @property
    def name(self) -> str:
        logger.info(f"SCHEMA: Computing field 'name'. Accessing self.full_name: '{getattr(self, 'full_name', 'N/A')}'")
        return getattr(self, 'full_name', '')

    @computed_field
    @property
    def role(self) -> str: # 戻り値の型を str に変更
        user_roles_rel = getattr(self, 'user_roles', [])
        logger.info(f"SCHEMA: Computing field 'role'. Accessing self.user_roles: {user_roles_rel}")
        if user_roles_rel and isinstance(user_roles_rel, list):
            # is_primary=True のロールを探す
            primary_user_role_obj = next((ur for ur in user_roles_rel if getattr(ur, 'is_primary', False)), None)
            
            # プライマリが見つからない場合は最初のロールを試す (フォールバック)
            if not primary_user_role_obj and len(user_roles_rel) > 0:
                 primary_user_role_obj = user_roles_rel[0]
                 logger.warning(f"SCHEMA: Primary role not found for user. Falling back to first role: {primary_user_role_obj}")
            
            if primary_user_role_obj:
                if hasattr(primary_user_role_obj, 'role') and hasattr(primary_user_role_obj.role, 'name'):
                    role_name = getattr(primary_user_role_obj.role, 'name', '不明')
                    logger.info(f"SCHEMA: Computed role name: '{role_name}'")
                    return role_name
                else:
                    logger.warning(f"SCHEMA: UserRole object lacks expected 'role' attribute or role.name: {primary_user_role_obj}")
            else:
                 logger.warning(f"SCHEMA: user_roles list is empty or contains no valid role objects.")
        else:
             logger.warning(f"SCHEMA: user_roles attribute is missing or not a list: {user_roles_rel}")
        return '不明' # デフォルト値 / エラー時の値

    @computed_field
    @property
    def is_email_verified(self) -> bool:
         logger.info(f"SCHEMA: Computing field 'is_email_verified'. Accessing self.is_verified: {getattr(self, 'is_verified', 'N/A')}")
         return getattr(self, 'is_verified', False)

    @computed_field
    @property
    def last_login_at(self) -> Optional[datetime]:
        login_info_obj = getattr(self, 'login_info', None)
        if login_info_obj and hasattr(login_info_obj, 'last_login_at'):
            last_login = getattr(login_info_obj, 'last_login_at', None)
            logger.info(f"SCHEMA: Computing field 'last_login_at'. Found login_info, last_login: {last_login}")
            return last_login
        logger.info("SCHEMA: Computing field 'last_login_at'. login_info not found or None.")
        return None

    @computed_field
    @property
    def permissions(self) -> Set[str]:
        """ユーザーが持つロールに紐づく全ての権限名のセットを返す"""
        user_perms: Set[str] = set()
        user_roles_rel = getattr(self, 'user_roles', [])
        logger.debug(f"SCHEMA: Computing permissions for user. Roles: {user_roles_rel}")
        if user_roles_rel and isinstance(user_roles_rel, list):
            for user_role_assoc in user_roles_rel:
                # UserRoleModel の role 属性にアクセス
                if hasattr(user_role_assoc, 'role') and isinstance(user_role_assoc.role, Role):
                    role_obj: Role = user_role_assoc.role
                    # Role の permissions 属性 (Association Proxy) にアクセス
                    if hasattr(role_obj, 'permissions') and isinstance(role_obj.permissions, list):
                        for perm in role_obj.permissions:
                             # Permission オブジェクトの name 属性を確認
                            if isinstance(perm, Permission) and hasattr(perm, 'name'):
                                user_perms.add(perm.name)
                            else:
                                logger.warning(f"SCHEMA: Unexpected permission object type or missing name: {perm} in role {role_obj.name}")
                    else:
                        logger.warning(f"SCHEMA: Role object {role_obj.name} lacks 'permissions' list or is not a list.")
                else:
                     logger.warning(f"SCHEMA: UserRole association lacks 'role' object or it's not a Role instance: {user_role_assoc}")
        logger.info(f"SCHEMA: Computed permissions: {user_perms}")
        return user_perms

    # --- End computed fields ---

    model_config = {
        "from_attributes": True,
    }

# ユーザー一覧取得レスポンス
class UserListResponse(BaseModel):
    total: int
    users: List[UserResponse]
    page: int
    size: int

# --- Role & Permission Schemas (既存のものを維持 or 必要なら調整) ---
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    permissions: List[str] # 権限コードのリスト

class RoleUpdate(RoleBase):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None

class RoleResponse(RoleBase, TimestampMixin):
    id: UUID
    permissions: List[Dict] # 権限情報のリスト

    class Config:
        from_attributes = True

class PermissionBase(BaseModel):
    code: str
    description: str

class PermissionResponse(PermissionBase):
    id: UUID

    class Config:
        from_attributes = True

# --- User Settings & Role Assignment (既存のものを維持) ---
class UserSettings(BaseModel):
    notification_preferences: Dict
    ui_preferences: Dict
    last_updated: datetime

    class Config:
        from_attributes = True

class UserRoleAssignment(BaseModel):
    user_id: UUID
    role_id: UUID

# --- User Settings Schema ---
class UserSettingsResponse(BaseModel):
    email: EmailStr
    full_name: str
    profile_image_url: Optional[str] = None
    # ★ 必要であればここにも grade, prefecture を追加する
    # grade: Optional[str] = None
    # prefecture: Optional[str] = None
    email_notifications: bool = True
    browser_notifications: bool = False
    theme: str = "light"
    subscription: Optional[SubscriptionResponse] = None # ★ サブスクリプション情報を追加

    model_config = {
        "from_attributes": True,
    } 