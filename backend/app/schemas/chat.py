from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import datetime
from uuid import UUID
# from enum import Enum # 不要な場合が多い
# import enum # 不要

# 既存のユーザースキーマをインポート (必要に応じて調整)
# from .user import User 
# 現状Userスキーマがないためコメントアウト。必要になったら解除。

# from app.models.chat import MessageSender # モデルからのインポートを削除
# 新しい enums.py からインポート
# from app.enums import ChatType, MessageSender, ChatSessionStatus # 変更前: app.enums から ChatSessionStatus をインポート
from app.models.enums import ChatType, MessageSender # 変更後: ChatSessionStatus のインポートを削除
from app.models.enums import SessionStatus as ChatSessionStatus # 変更後: app.models.enums から SessionStatus を ChatSessionStatus としてインポート
from app.models.enums import MessageSender as ModelMessageSender # SessionStatus と ModelMessageSender もインポート

# --- Enums (定義は削除) ---
# class MessageSender(str, enum.Enum): ...
# class ChatType(str, enum.Enum): ...
# class ChatSessionStatus(str, enum.Enum): ...

# --- スキーマ定義 (Enumの参照は変更なし、インポート元が変わるだけ) ---

class Message(BaseModel):
    sender: MessageSender # app.enums.MessageSender を参照
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[UUID] = None
    chat_type: ChatType = ChatType.GENERAL # app.enums.ChatType を参照

class StreamChatRequest(ChatRequest):
    stream: bool = True

class ChatResponse(BaseModel):
    reply: str
    session_id: UUID
    timestamp: datetime

class ChatMessageResponse(BaseModel):
    id: UUID # ★注意: モデルはIntegerだが、ここがUUIDなのは意図的か確認
    content: str
    sender: MessageSender
    created_at: datetime
    meta_data: Optional[Dict] = None
    
    class Config:
        from_attributes = True

class ChatMessageBase(BaseModel):
    content: str

class ChatMessageCreate(ChatMessageBase):
    # ユーザーからのメッセージ作成用スキーマ
    pass # senderはAPI側で'user'として設定

class ChatMessage(ChatMessageBase):
    id: int # ★モデルに合わせてInt
    session_id: UUID # ★モデルに合わせてUUID
    sender: MessageSender # app.enums.MessageSender を参照
    created_at: datetime

    class Config:
        from_attributes = True # v2 Pydantic では orm_mode の代わりに from_attributes

class ChatSessionBase(BaseModel):
    pass # セッション作成時に特別な入力は不要

class ChatSessionCreate(ChatSessionBase):
    chat_type: ChatType = ChatType.SELF_ANALYSIS # app.enums.ChatType を参照

class ChatSession(ChatSessionBase):
    id: UUID # ★モデルに合わせてUUID
    user_id: UUID # ★モデルに合わせてUUID
    chat_type: ChatType # app.enums.ChatType を参照
    created_at: datetime
    updated_at: Optional[datetime] = None
    # messages: List[ChatMessage] = [] # session取得APIでは返さない想定のためコメントアウト

    class Config:
        from_attributes = True

# ユーザー情報を含むセッション詳細スキーマ (任意)
# class ChatSessionWithUser(ChatSession):
#     user: User # ユーザー情報も返す場合

class ChatSessionResponse(BaseModel):
    id: UUID
    title: str
    chat_type: ChatType # app.enums.ChatType を参照
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    status: ChatSessionStatus # ★ app.models.enums.SessionStatus を参照するようになる
    
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

# ChatSidebar で使用するためのセッション概要スキーマ
class ChatSessionSummary(BaseModel):
    id: UUID
    title: Optional[str] = None
    chat_type: ChatType
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_message_summary: Optional[str] = None

    class Config:
        from_attributes = True 