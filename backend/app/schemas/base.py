from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime

class BaseResponse(BaseModel):
    success: bool
    message: Optional[str] = None 