from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, DateTime, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from .base import Base, TimestampMixin


class ForumCategory(Base, TimestampMixin):
    """フォーラムカテゴリ"""
    __tablename__ = "forum_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("forum_categories.id"), nullable=True)
    display_order = Column(Integer, default=0)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)

    # リレーションシップ
    parent = relationship("ForumCategory", remote_side=[id], backref="subcategories")
    topics = relationship("ForumTopic", back_populates="category")
    creator = relationship("User", foreign_keys=[created_by], back_populates="forum_categories")


class ForumTopic(Base, TimestampMixin):
    """フォーラムトピック"""
    __tablename__ = "forum_topics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = Column(UUID(as_uuid=True), ForeignKey("forum_categories.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    views_count = Column(Integer, default=0)
    is_pinned = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    last_post_at = Column(DateTime, nullable=True)

    # リレーションシップ
    category = relationship("ForumCategory", back_populates="topics")
    posts = relationship("ForumPost", back_populates="topic", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by], back_populates="forum_topics")
    views = relationship("ForumTopicView", back_populates="topic", cascade="all, delete-orphan")

    # インデックス
    __table_args__ = (
        Index('idx_forum_topic_category', category_id),
        Index('idx_forum_topic_created_by', created_by),
    )


class ForumPost(Base, TimestampMixin):
    """フォーラム投稿"""
    __tablename__ = "forum_posts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("forum_topics.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("forum_posts.id"), nullable=True)
    is_solution = Column(Boolean, default=False)

    # リレーションシップ
    topic = relationship("ForumTopic", back_populates="posts")
    parent = relationship("ForumPost", remote_side=[id], backref="replies")
    creator = relationship("User", foreign_keys=[created_by], back_populates="forum_posts")
    reactions = relationship("ForumPostReaction", back_populates="post", cascade="all, delete-orphan")

    # インデックス
    __table_args__ = (
        Index('idx_forum_post_topic', topic_id),
        Index('idx_forum_post_created_by', created_by),
        Index('idx_forum_post_parent', parent_id),
    )


class ForumPostReaction(Base, TimestampMixin):
    """フォーラム投稿リアクション"""
    __tablename__ = "forum_post_reactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(UUID(as_uuid=True), ForeignKey("forum_posts.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reaction_type = Column(String, nullable=False)  # enum: ReactionType

    # リレーションシップ
    post = relationship("ForumPost", back_populates="reactions")
    user = relationship("User")

    # インデックス
    __table_args__ = (
        Index('idx_forum_post_reaction_post', post_id),
        Index('idx_forum_post_reaction_user', user_id),
    )


class ForumTopicView(Base):
    """フォーラムトピック閲覧履歴"""
    __tablename__ = "forum_topic_views"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("forum_topics.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    viewed_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # リレーションシップ
    topic = relationship("ForumTopic", back_populates="views")
    user = relationship("User", back_populates="forum_topic_views")

    # インデックス
    __table_args__ = (
        Index('idx_forum_topic_view_topic', topic_id),
        Index('idx_forum_topic_view_user', user_id),
    ) 