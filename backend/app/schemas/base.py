from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BaseResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    
    class Config:
        from_attributes = True 