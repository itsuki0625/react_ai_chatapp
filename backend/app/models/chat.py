from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
# import enum # 標準のenumは不要に
# from app.schemas.chat import ChatType # スキーマからのインポートを削除
# 新しい enums.py からインポート
from app.models.enums import ChatType, MessageSender
from app.models.enums import SessionStatus # 追加: models.enums からインポート

from .base import Base

# MessageSender Enum の定義は enums.py に移動したので削除
# class MessageSender(str, enum.Enum):
#     USER = "user"
#     AI = "ai"

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    # demo_data.py で使われているカラムを追加
    title = Column(String, nullable=True)
    status = Column(Enum(SessionStatus, name="session_status_enum"), nullable=False, index=True, server_default=SessionStatus.ACTIVE.value)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    # --- ここまで追加 ---
    # Enum() に渡す ChatType が enums からインポートされたものを使用する
    chat_type = Column(Enum(ChatType, name="chat_type_enum"), 
                       nullable=False, 
                       index=True, 
                       server_default=ChatType.GENERAL.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User") # Userモデルとのリレーション (Userモデルが存在する前提)
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    # ChecklistEvaluation とのリレーションシップを追加
    checklist_evaluations = relationship("ChecklistEvaluation", back_populates="chat_session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    # Enum() に渡す MessageSender が enums からインポートされたものを使用する
    # また、Enumに name を指定することが推奨される場合がある (DB側での型名)
    sender = Column(Enum(MessageSender, name="message_sender_enum"), nullable=False) 
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("ChatSession", back_populates="messages")
    user = relationship("User", back_populates="chat_messages")
    # ChatAttachment との One-to-Many リレーションシップを追加
    attachments = relationship("ChatAttachment", back_populates="message", cascade="all, delete-orphan")
    # リレーションシップの名前を 'metadata' から 'message_metadata' に変更
    message_metadata = relationship("ChatMessageMetadata", back_populates="message", cascade="all, delete-orphan")

# ChatAttachment モデルを追加
class ChatAttachment(Base):
    __tablename__ = "chat_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # message_id の型を ChatMessage.id の型 (Integer) に合わせる
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=False, index=True)
    file_url = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    message = relationship("ChatMessage", back_populates="attachments")

# ChatMessageMetadata モデルを追加
class ChatMessageMetadata(Base):
    __tablename__ = "chat_message_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # message_id の型を ChatMessage.id の型 (Integer) に合わせる
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=False, index=True)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False) # JSONBなども検討可
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    message = relationship("ChatMessage", back_populates="message_metadata")