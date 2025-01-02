from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional
from uuid import UUID
from enum import Enum

class ContentType(str, Enum):
    VIDEO = "VIDEO"
    SLIDE = "SLIDE"
    PDF = "PDF"

class ContentBase(BaseModel):
    title: str
    description: Optional[str] = None
    url: str
    content_type: ContentType
    thumbnail_url: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None

class ContentCreate(ContentBase):
    pass

class ContentUpdate(ContentBase):
    title: Optional[str] = None
    url: Optional[str] = None
    content_type: Optional[ContentType] = None

class ContentResponse(ContentBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 