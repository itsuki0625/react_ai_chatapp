from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from app.models.enums import NotificationType

class InAppNotificationBase(BaseModel):
    notification_type: NotificationType
    title: str
    message: str
    metadata: Optional[Dict[str, Any]] = None

class InAppNotificationCreate(InAppNotificationBase):
    pass

class InAppNotificationUpdate(BaseModel):
    is_read: bool

class InAppNotificationInDB(InAppNotificationBase):
    id: str
    user_id: str
    is_read: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 