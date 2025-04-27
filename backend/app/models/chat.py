from sqlalchemy import Column, String, UUID, Boolean, DateTime, Text, ForeignKey, Enum as SQLAlchemyEnum, Integer
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from .base import Base, TimestampMixin
from .enums import SessionType, SessionStatus, SenderType, MessageType

class ChatSession(Base, TimestampMixin):
    __tablename__ = 'chat_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    title = Column(String, nullable=False)
    session_type = Column(SQLAlchemyEnum(SessionType), nullable=False)
    status = Column(SQLAlchemyEnum(SessionStatus), nullable=False)
    last_message_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")
    session_metadata = relationship("ChatSessionMetaData", back_populates="session")
    checklist_evaluation = relationship("ChecklistEvaluation", back_populates="chat_session", uselist=False)

class ChatSessionMetaData(Base, TimestampMixin):
    __tablename__ = 'chat_session_metadata'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('chat_sessions.id'), nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)

    # Relationships
    session = relationship("ChatSession", back_populates="session_metadata")

class ChatMessage(Base, TimestampMixin):
    __tablename__ = 'chat_messages'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('chat_sessions.id'), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    sender_type = Column(SQLAlchemyEnum(SenderType), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(SQLAlchemyEnum(MessageType), nullable=False)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    user = relationship("User", back_populates="chat_messages")
    attachments = relationship("ChatAttachment", back_populates="message")
    message_metadata = relationship("ChatMessageMetaData", back_populates="message")

class ChatMessageMetaData(Base, TimestampMixin):
    __tablename__ = 'chat_message_metadata'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey('chat_messages.id'), nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)

    # Relationships
    message = relationship("ChatMessage", back_populates="message_metadata")

class ChatAttachment(Base, TimestampMixin):
    __tablename__ = 'chat_attachments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey('chat_messages.id'), nullable=False)
    file_url = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_name = Column(String, nullable=False)

    # Relationships
    message = relationship("ChatMessage", back_populates="attachments")