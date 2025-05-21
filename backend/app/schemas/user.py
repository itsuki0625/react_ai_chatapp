import logging
from pydantic import BaseModel, EmailStr, validator, Field, computed_field, ConfigDict
from typing import Optional, List, Dict, Any, Set
from uuid import UUID
from datetime import datetime
from enum import Enum
from .base import TimestampMixin
from app.models.user import User as UserModel, UserRole as UserRoleModel, Role, Permission, UserLoginInfo
from .subscription import SubscriptionResponse # SubscriptionResponse をインポート
from app.core.config import settings

# Logger をモジュールレベルで定義
logger = logging.getLogger(__name__)

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    UNPAID = "unpaid"

# --- Role & Permission Schemas (先に定義) ---
class PermissionBase(BaseModel):
    # モデルに合わせて name に変更 (code ではなく)
    name: str
    description: Optional[str] = None

class PermissionResponse(PermissionBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    permissions: List[str] # 権限名のリストで受け取る

class RoleUpdate(RoleBase):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None

class RoleResponse(RoleBase, TimestampMixin):
    id: UUID
    # ★ 修正: permissions の型を List[PermissionResponse] に変更し、ネストされた権限情報を返す
    # permissions: List[Dict] # 変更前
    permissions: List[PermissionResponse] = [] # 権限オブジェクトのリスト

    model_config = ConfigDict(from_attributes=True)

# ★ 新規追加: UserRole モデルに対応する Pydantic スキーマ
class UserRoleResponse(TimestampMixin): # 必要に応じて TimestampMixin を継承
    role: RoleResponse # ネストされた RoleResponse を使用
    is_primary: bool

    model_config = ConfigDict(from_attributes=True)

# ★ 新規追加: UserLoginInfo モデルに対応する Pydantic スキーマ
class UserLoginInfoResponse(BaseModel):
    id: UUID
    last_login_at: Optional[datetime] = None
    failed_login_attempts: int
    last_failed_login_at: Optional[datetime] = None
    locked_until: Optional[datetime] = None
    account_lock_reason: Optional[Any] = None # Enumの場合は適切なEnum型を指定

    model_config = ConfigDict(from_attributes=True)

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
    profile_image_url: Optional[str] = None # S3 キーを受け取る想定
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
    user_roles: List[UserRoleResponse] = []
    status: UserStatus # status を直接含める
    login_info: Optional[UserLoginInfoResponse] = None # Any から UserLoginInfoResponse に変更
    grade: Optional[str] = None # grade を追加 (モデルに合わせて Optional[str])
    prefecture: Optional[str] = None # prefecture を追加 (モデルに合わせて Optional[str])
    # ★ profile_image_url を computed_field で上書きするため、元のフィールドは別名にする
    profile_image_url_key: Optional[str] = Field(alias='profile_image_url', default=None)
    # --- End source fields ---

    # --- computed fields (these will be in the final JSON) ---
    @computed_field
    @property
    def name(self) -> str:
        logger.info(f"SCHEMA: Computing field 'name'. Accessing self.full_name: '{getattr(self, 'full_name', 'N/A')}'")
        return getattr(self, 'full_name', '')

    @computed_field
    @property
    def role(self) -> str:
        """プライマリロール名を返す"""
        logger.info(f"SCHEMA: Computing field 'role'. Accessing self.user_roles: {self.user_roles}")
        primary_role_resp = next((ur_resp for ur_resp in self.user_roles if ur_resp.is_primary), None)

        if primary_role_resp and primary_role_resp.role:
            return primary_role_resp.role.name
        elif self.user_roles: # プライマリがない場合、最初のロールを返す (フォールバック)
            first_role_resp = self.user_roles[0]
            if first_role_resp.role:
                 logger.warning(f"SCHEMA: Primary role not found for user. Falling back to first role: {first_role_resp.role.name}")
                 return first_role_resp.role.name

        logger.warning(f"SCHEMA: Could not determine primary role name for user {self.id}")
        return '不明'

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
        logger.debug(f"SCHEMA: Computing permissions for user {self.id}. Roles: {self.user_roles}")
        for user_role_resp in self.user_roles:
            if user_role_resp.role and user_role_resp.role.permissions:
                for perm_resp in user_role_resp.role.permissions:
                    user_perms.add(perm_resp.name)
            else:
                 logger.warning(f"SCHEMA: UserRoleResponse lacks 'role' or role lacks 'permissions': {user_role_resp}")
        logger.info(f"SCHEMA: Computed permissions for user {self.id}: {user_perms}")
        return user_perms

    # ★ profile_image_url を計算する computed_field を追加
    @computed_field(return_type=Optional[str])
    @property
    def profile_image_url(self) -> Optional[str]:
        """S3キーから完全なURLを生成して返す"""
        key = getattr(self, 'profile_image_url_key', None)
        if key:
            # config からバケット名とリージョンを取得
            bucket_name = settings.AWS_S3_ICON_BUCKET_NAME
            region = settings.AWS_REGION
            if bucket_name and region:
                # Virtual Hosted Style URL を生成
                # 必要に応じて Path Style に変更 (https://s3.{region}.amazonaws.com/{bucket_name}/{key})
                return f"https://{bucket_name}.s3.{region}.amazonaws.com/{key}"
            else:
                logger.error("S3 bucket name or region is not configured for generating profile image URL.")
        return None

    # --- End computed fields ---

    model_config = ConfigDict(
        from_attributes=True,
        # ★ computed_field が元のフィールドを上書きできるように設定
        populate_by_name=True, 
    )

# ユーザー一覧取得レスポンス
class UserListResponse(BaseModel):
    total: int
    users: List[UserResponse]
    page: int
    size: int

# --- User Settings & Role Assignment (既存のものを維持) ---
class UserSettings(BaseModel):
    notification_preferences: Dict
    ui_preferences: Dict
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)

class UserRoleAssignment(BaseModel):
    user_id: UUID
    role_id: UUID

# --- User Settings Schema ---
class UserSettingsResponse(BaseModel):
    email: EmailStr
    full_name: str
    profile_image_url: Optional[str] = None
    email_notifications: bool = True
    browser_notifications: bool = False
    system_notifications: bool = True
    chat_notifications: bool = True
    document_notifications: bool = True
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    theme: str = "light"
    subscription: Optional[SubscriptionResponse] = None

    model_config = ConfigDict(from_attributes=True) 