from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class PushSubscriptionBase(BaseModel):
    endpoint: str
    auth_token: str
    p256dh_key: str
    device_info: Optional[Dict[str, Any]] = None

class PushSubscriptionCreate(PushSubscriptionBase):
    pass

class PushSubscriptionUpdate(PushSubscriptionBase):
    pass

class PushSubscriptionInDB(PushSubscriptionBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 