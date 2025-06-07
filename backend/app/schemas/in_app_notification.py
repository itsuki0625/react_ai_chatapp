from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from app.models.enums import NotificationType
import uuid

class InAppNotificationBase(BaseModel):
    title: str
    message: str
    link: str | None = None # 通知に関連するリンク（オプショナル）
    notification_type: str | None = None # 通知の種類（例: 'system', 'chat', 'document'）

class InAppNotificationCreate(InAppNotificationBase):
    user_id: uuid.UUID

class InAppNotificationResponse(InAppNotificationBase):
    id: uuid.UUID
    user_id: uuid.UUID # 念のため含めるか、用途によって除外も検討
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # Pydantic V2 では orm_mode の代わりに from_attributes を使用

class InAppNotificationUpdate(BaseModel):
    read: bool | None = None

class InAppNotificationInDB(InAppNotificationBase):
    id: str
    user_id: str
    is_read: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 