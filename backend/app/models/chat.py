from sqlalchemy import Column, String, UUID, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLAlchemyEnum, Integer
from sqlalchemy.orm import relationship
import uuid
from .base import Base, TimestampMixin
from .enums import SessionType, SessionStatus, SenderType, MessageType

class ChatSession(Base, TimestampMixin):
    __tablename__ = 'chat_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    title = Column(String)
    session_type = Column(SQLAlchemyEnum(SessionType))
    status = Column(SQLAlchemyEnum(SessionStatus))
    meta_data = Column(JSON)
    last_message_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")
    checklist_evaluation = relationship("ChecklistEvaluation", back_populates="chat", uselist=False)

class ChatMessage(Base, TimestampMixin):
    __tablename__ = 'chat_messages'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('chat_sessions.id'))
    sender_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    sender_type = Column(SQLAlchemyEnum(SenderType))
    content = Column(Text)
    message_type = Column(SQLAlchemyEnum(MessageType))
    meta_data = Column(JSON)
    is_read = Column(Boolean, default=False)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    user = relationship("User", back_populates="chat_messages")
    attachments = relationship("ChatAttachment", back_populates="message")

class ChatAttachment(Base, TimestampMixin):
    __tablename__ = 'chat_attachments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey('chat_messages.id'))
    file_url = Column(String)
    file_type = Column(String)
    file_size = Column(Integer)

    # Relationships
    message = relationship("ChatMessage", back_populates="attachments")