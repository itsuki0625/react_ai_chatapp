from sqlalchemy import Column, String, UUID, Boolean, Integer, ForeignKey, Text, Float, Enum as SQLAlchemyEnum, DateTime
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from .base import Base, TimestampMixin
from .enums import ContentType, DeviceType

class Content(Base, TimestampMixin):
    __tablename__ = 'contents'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text)
    url = Column(String, nullable=False)
    content_type = Column(SQLAlchemyEnum(ContentType), nullable=False)
    thumbnail_url = Column(String)
    duration = Column(Integer)  # 再生時間（秒）
    is_premium = Column(Boolean, default=False)

    # Relationships
    tags = relationship("ContentTag", back_populates="content")
    category_relations = relationship("ContentCategoryRelation", back_populates="content")
    view_history = relationship("ContentViewHistory", back_populates="content")
    ratings = relationship("ContentRating", back_populates="content")

class ContentTag(Base):
    __tablename__ = 'content_tags'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(UUID(as_uuid=True), ForeignKey('contents.id'), nullable=False)
    tag_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    content = relationship("Content", back_populates="tags")

class ContentCategory(Base, TimestampMixin):
    __tablename__ = 'content_categories'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('content_categories.id'))
    display_order = Column(Integer)
    icon_url = Column(String)
    is_active = Column(Boolean, default=True)

    # Relationships
    parent = relationship("ContentCategory", remote_side=[id], backref="children")
    content_relations = relationship("ContentCategoryRelation", back_populates="category")

class ContentCategoryRelation(Base):
    __tablename__ = 'content_category_relations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(UUID(as_uuid=True), ForeignKey('contents.id'), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey('content_categories.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    content = relationship("Content", back_populates="category_relations")
    category = relationship("ContentCategory", back_populates="content_relations")

class ContentViewHistory(Base):
    __tablename__ = 'content_view_history'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    content_id = Column(UUID(as_uuid=True), ForeignKey('contents.id'), nullable=False)
    viewed_at = Column(DateTime, default=datetime.utcnow)
    progress = Column(Float)  # 視聴進捗（秒数または位置、0～100%）
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    duration = Column(Integer)  # セッション継続時間（秒）
    device_type = Column(SQLAlchemyEnum(DeviceType))
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")
    content = relationship("Content", back_populates="view_history")
    view_metadata = relationship("ContentViewHistoryMetaData", back_populates="view_history")

class ContentViewHistoryMetaData(Base):
    __tablename__ = 'content_view_history_metadata'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    view_history_id = Column(UUID(as_uuid=True), ForeignKey('content_view_history.id'), nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    view_history = relationship("ContentViewHistory", back_populates="view_metadata")

class ContentRating(Base, TimestampMixin):
    __tablename__ = 'content_ratings'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    content_id = Column(UUID(as_uuid=True), ForeignKey('contents.id'), nullable=False)
    rating = Column(Integer, nullable=False)  # 1～5
    comment = Column(Text)

    # Relationships
    user = relationship("User")
    content = relationship("Content", back_populates="ratings") 