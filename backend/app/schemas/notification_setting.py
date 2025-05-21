from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.models.enums import NotificationType # enums.py から NotificationType をインポート

# Userスキーマをインポート (存在すると仮定)
# from .user import User # 必要に応じて調整

# 開発を簡略化するため、一時的にUserスキーマを定義 (本来はuser.pyからインポート)
class UserBase(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str] = None

    class Config:
        orm_mode = True

class User(UserBase):
    pass


class NotificationSettingBase(BaseModel):
    notification_type: NotificationType
    email_enabled: bool = True
    push_enabled: bool = False
    in_app_enabled: bool = True
    quiet_hours_start: Optional[datetime] = None
    quiet_hours_end: Optional[datetime] = None

class NotificationSettingCreate(NotificationSettingBase):
    user_id: UUID

class NotificationSettingUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    quiet_hours_start: Optional[datetime] = None
    quiet_hours_end: Optional[datetime] = None

class NotificationSettingInDBBase(NotificationSettingBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# APIのレスポンスで使用
class NotificationSetting(NotificationSettingInDBBase):
    pass

# Admin画面でユーザー情報と共に通知設定を表示する場合のスキーマ
class NotificationSettingUser(NotificationSetting):
    user: Optional[User] = None # 関連するユーザー情報

# 複数の通知設定をリストで返すためのスキーマ (ページネーションなどで使用)
class NotificationSettingList(BaseModel):
    total: int
    items: List[NotificationSettingUser] 