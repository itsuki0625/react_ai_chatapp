from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from uuid import UUID
from .base import TimestampMixin

class Message(BaseModel):
    sender: str
    text: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Message]] = []

class ChatResponse(BaseModel):
    reply: str
    timestamp: str
    session_id: str

class ChatSessionCreate(BaseModel):
    user_id: UUID
    title: str
    session_type: str
    metadata: Optional[Dict] = None

class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict] = None

class ChatSessionResponse(TimestampMixin):
    id: UUID
    user_id: UUID
    title: str
    session_type: str
    status: str
    metadata: Optional[Dict] = None
    last_message_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ChatMessageCreate(BaseModel):
    session_id: UUID
    sender_id: UUID
    sender_type: str
    content: str
    message_type: str
    metadata: Optional[Dict] = None

class ChatMessageResponse(TimestampMixin):
    id: UUID
    session_id: UUID
    sender_id: UUID
    sender_type: str
    content: str
    message_type: str
    metadata: Optional[Dict] = None
    is_read: bool

    class Config:
        from_attributes = True 