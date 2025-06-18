from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models.enums import NotificationType
import uuid

class InAppNotificationBase(BaseModel):
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None # JSON型のデータ（モデルと一致させる）
    notification_type: Optional[str] = None # 通知の種類（例: 'system', 'chat', 'document'）

class InAppNotificationCreate(InAppNotificationBase):
    user_id: uuid.UUID

class InAppNotificationResponse(InAppNotificationBase):
    id: uuid.UUID
    user_id: uuid.UUID # 念のため含めるか、用途によって除外も検討
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class InAppNotificationUpdate(BaseModel):
    read: Optional[bool] = None

class InAppNotificationInDB(InAppNotificationBase):
    id: str
    user_id: str
    is_read: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 