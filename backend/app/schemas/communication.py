from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from uuid import UUID

class MessageBase(BaseModel):
    """メッセージの基本情報"""
    content: str = Field(..., description="メッセージの内容")
    message_type: str = Field("text", description="メッセージの種類 (text, image, file, etc)")

class MessageCreate(MessageBase):
    """メッセージ作成リクエスト"""
    pass

class MessageResponse(MessageBase):
    """メッセージレスポンス"""
    id: UUID = Field(..., description="メッセージID")
    conversation_id: UUID = Field(..., description="会話ID")
    sender_id: UUID = Field(..., description="送信者のユーザーID")
    sender_name: Optional[str] = Field(None, description="送信者の名前")
    sender_avatar: Optional[str] = Field(None, description="送信者のアバター画像URL")
    read: bool = Field(False, description="既読フラグ")
    created_at: datetime = Field(..., description="作成日時")

    class Config:
        orm_mode = True

class ConversationBase(BaseModel):
    """会話の基本情報"""
    title: Optional[str] = Field(None, description="会話のタイトル")

class ConversationCreate(ConversationBase):
    """会話作成リクエスト"""
    recipient_id: UUID = Field(..., description="相手のユーザーID")
    initial_message: Optional[str] = Field(None, description="最初のメッセージ (オプション)")

class ConversationResponse(ConversationBase):
    """会話レスポンス"""
    id: UUID = Field(..., description="会話ID")
    user1_id: UUID = Field(..., description="ユーザー1のID")
    user2_id: UUID = Field(..., description="ユーザー2のID")
    last_message: Optional[MessageResponse] = Field(None, description="最後のメッセージ")
    unread_count: int = Field(0, description="未読メッセージ数")
    user1_name: Optional[str] = Field(None, description="ユーザー1の名前")
    user2_name: Optional[str] = Field(None, description="ユーザー2の名前")
    user1_avatar: Optional[str] = Field(None, description="ユーザー1のアバター画像URL")
    user2_avatar: Optional[str] = Field(None, description="ユーザー2のアバター画像URL")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: Optional[datetime] = Field(None, description="更新日時")

    class Config:
        orm_mode = True

class ConversationUpdate(BaseModel):
    """会話更新リクエスト"""
    title: Optional[str] = Field(None, description="会話のタイトル") 