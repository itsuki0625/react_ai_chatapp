from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Message(BaseModel):
    sender: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []
    session_id: Optional[str] = None
    session_type: Optional[str] = "CONSULTATION"

class ChatResponse(BaseModel):
    reply: str
    timestamp: str
    session_id: str

# チャットメッセージのレスポンス用スキーマ
class ChatMessageResponse(BaseModel):
    id: str
    content: str
    sender_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True 