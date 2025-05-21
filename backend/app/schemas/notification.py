from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from app.models.enums import NotificationType

class NotificationBase(BaseModel):
    notification_type: NotificationType
    title: str
    message: str
    metadata: Optional[Dict[str, Any]] = None

class NotificationCreate(NotificationBase):
    user_id: str

class BulkNotificationCreate(NotificationBase):
    user_ids: List[str]

class NotificationResponse(BaseModel):
    success: bool
    message: str
    user_id: Optional[str] = None 