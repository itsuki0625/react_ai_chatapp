from sqlalchemy import Column, String, Enum as SQLAlchemyEnum, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.models.base import Base

class ContentType(str, enum.Enum):
    VIDEO = "VIDEO"
    SLIDE = "SLIDE"
    PDF = "PDF"

class Content(Base):
    __tablename__ = "contents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    url = Column(String(1024), nullable=False)
    content_type = Column(SQLAlchemyEnum(ContentType), nullable=False)
    thumbnail_url = Column(String(1024))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # オプション: カテゴリーやタグを追加
    category = Column(String(100))
    tags = Column(String(255))  # カンマ区切りで保存 