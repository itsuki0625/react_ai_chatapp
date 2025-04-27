from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, DateTime, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from .base import Base, TimestampMixin
from .study_plan import StudyPlanItem


class LearningPath(Base, TimestampMixin):
    """学習パス"""
    __tablename__ = "learning_paths"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    difficulty_level = Column(String, nullable=False)  # enum: DifficultyLevel
    estimated_hours = Column(Float, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)

    # リレーションシップ
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_learning_paths")
    prerequisites = relationship("LearningPathPrerequisite", back_populates="learning_path", cascade="all, delete-orphan")
    target_audiences = relationship("LearningPathAudience", back_populates="learning_path", cascade="all, delete-orphan")
    items = relationship("LearningPathItem", back_populates="learning_path", cascade="all, delete-orphan")
    user_enrollments = relationship("UserLearningPath", back_populates="learning_path", cascade="all, delete-orphan")


class LearningPathPrerequisite(Base):
    """学習パス前提条件"""
    __tablename__ = "learning_path_prerequisites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learning_path_id = Column(UUID(as_uuid=True), ForeignKey("learning_paths.id"), nullable=False)
    prerequisite = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # リレーションシップ
    learning_path = relationship("LearningPath", back_populates="prerequisites")


class LearningPathAudience(Base):
    """学習パス対象者"""
    __tablename__ = "learning_path_audiences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learning_path_id = Column(UUID(as_uuid=True), ForeignKey("learning_paths.id"), nullable=False)
    target_audience = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # リレーションシップ
    learning_path = relationship("LearningPath", back_populates="target_audiences")


class LearningPathItem(Base, TimestampMixin):
    """学習パス項目"""
    __tablename__ = "learning_path_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learning_path_id = Column(UUID(as_uuid=True), ForeignKey("learning_paths.id"), nullable=False)
    content_id = Column(UUID(as_uuid=True), ForeignKey("contents.id"), nullable=True)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    sequence_number = Column(Integer, nullable=False)
    is_required = Column(Boolean, default=True)
    estimated_minutes = Column(Integer, nullable=True)

    # リレーションシップ
    learning_path = relationship("LearningPath", back_populates="items")
    content = relationship("Content", foreign_keys=[content_id])
    quiz = relationship("Quiz", foreign_keys=[quiz_id])
    user_progress = relationship("UserLearningPathItem", back_populates="learning_path_item", cascade="all, delete-orphan")


class UserLearningPath(Base, TimestampMixin):
    """ユーザー学習パス"""
    __tablename__ = "user_learning_paths"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    learning_path_id = Column(UUID(as_uuid=True), ForeignKey("learning_paths.id"), nullable=False)
    start_date = Column(DateTime, nullable=True)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    progress_percentage = Column(Float, default=0.0)

    # リレーションシップ
    user = relationship("User", back_populates="learning_paths")
    learning_path = relationship("LearningPath", back_populates="user_enrollments")
    items = relationship("UserLearningPathItem", back_populates="user_learning_path", cascade="all, delete-orphan")


class UserLearningPathItem(Base, TimestampMixin):
    """ユーザー学習パス項目"""
    __tablename__ = "user_learning_path_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_learning_path_id = Column(UUID(as_uuid=True), ForeignKey("user_learning_paths.id"), nullable=False)
    learning_path_item_id = Column(UUID(as_uuid=True), ForeignKey("learning_path_items.id"), nullable=False)
    status = Column(String, nullable=False)  # enum: LearningItemStatus
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # リレーションシップ
    user_learning_path = relationship("UserLearningPath", back_populates="items")
    learning_path_item = relationship("LearningPathItem", back_populates="user_progress")
    notes = relationship("UserLearningPathNote", back_populates="user_learning_path_item", cascade="all, delete-orphan")


class UserLearningPathNote(Base, TimestampMixin):
    """ユーザー学習パス項目ノート"""
    __tablename__ = "user_learning_path_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_learning_path_item_id = Column(UUID(as_uuid=True), ForeignKey("user_learning_path_items.id"), nullable=False)
    note = Column(Text, nullable=False)

    # リレーションシップ
    user_learning_path_item = relationship("UserLearningPathItem", back_populates="notes") 