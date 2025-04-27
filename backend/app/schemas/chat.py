from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import datetime
from uuid import UUID
from enum import Enum

class MessageSender(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatType(str, Enum):
    SELF_ANALYSIS = "self_analysis"  # 自己分析AI
    ADMISSION = "admission"  # 総合型選抜AI 
    STUDY_SUPPORT = "study_support"  # 汎用学習支援AI
    GENERAL = "general"  # 一般的なチャット

class ChatSessionStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class Message(BaseModel):
    sender: MessageSender
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[UUID] = None
    chat_type: ChatType = ChatType.GENERAL

class StreamChatRequest(ChatRequest):
    stream: bool = True

class ChatResponse(BaseModel):
    reply: str
    session_id: UUID
    timestamp: datetime

class ChatMessageResponse(BaseModel):
    id: UUID
    content: str
    sender: MessageSender
    created_at: datetime
    meta_data: Optional[Dict] = None
    
    class Config:
        from_attributes = True

class ChatMessageCreate(BaseModel):
    content: str
    sender: MessageSender
    message_type: Literal["TEXT", "IMAGE", "FILE"] = "TEXT"
    meta_data: Optional[Dict] = None

class ChatSessionCreate(BaseModel):
    title: Optional[str] = None
    chat_type: ChatType = ChatType.GENERAL
    initial_message: Optional[str] = None

class ChatSessionResponse(BaseModel):
    id: UUID
    title: str
    chat_type: ChatType
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    status: ChatSessionStatus = ChatSessionStatus.ACTIVE
    
    class Config:
        from_attributes = True

class ChatSessionDetailResponse(ChatSessionResponse):
    messages: List[ChatMessageResponse]
    
    class Config:
        from_attributes = True

class ChatSessionArchiveRequest(BaseModel):
    session_id: UUID

class SelfAnalysisRequest(BaseModel):
    message: str
    session_id: Optional[UUID] = None
    interests: Optional[List[str]] = None
    previous_analysis: Optional[Dict] = None

class SelfAnalysisReportResponse(BaseModel):
    user_id: UUID
    report: Dict
    strengths: List[str]
    interests: List[str]
    suitable_departments: List[Dict]
    created_at: datetime
    
    class Config:
        from_attributes = True

class AdmissionChatRequest(BaseModel):
    message: str
    session_id: Optional[UUID] = None
    university_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    admission_method_id: Optional[UUID] = None

class ChatAnalysisResponse(BaseModel):
    user_id: UUID
    analysis_type: str
    analysis_data: Dict
    created_at: datetime
    
    class Config:
        from_attributes = True 