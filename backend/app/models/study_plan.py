from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Date, Text, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, date
import uuid
from .base import Base, TimestampMixin

class StudyPlan(Base):
    """学習計画モデル"""
    __tablename__ = "study_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    subject = Column(String(100), nullable=True)
    level = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    completion_rate = Column(Float, default=0.0)
    created_at = Column(Date, default=datetime.now)
    updated_at = Column(Date, nullable=True)

    # リレーションシップ
    user = relationship("User", back_populates="study_plans")
    goals = relationship("StudyGoal", back_populates="study_plan", cascade="all, delete-orphan")
    items = relationship("StudyPlanItem", back_populates="study_plan", cascade="all, delete-orphan")

class StudyPlanItem(Base):
    """学習計画項目モデル"""
    __tablename__ = "study_plan_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_plan_id = Column(UUID(as_uuid=True), ForeignKey("study_plans.id"), nullable=False)
    content_id = Column(UUID(as_uuid=True), nullable=True)  # コンテンツへの参照（オプション）
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    scheduled_date = Column(Date, nullable=True)
    duration_minutes = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    completed_at = Column(Date, nullable=True)
    display_order = Column(Integer, default=0)
    created_at = Column(Date, default=datetime.now)
    updated_at = Column(Date, nullable=True)

    # リレーションシップ
    study_plan = relationship("StudyPlan", back_populates="items")

class StudyGoal(Base):
    """学習目標モデル"""
    __tablename__ = "study_goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_plan_id = Column(UUID(as_uuid=True), ForeignKey("study_plans.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_date = Column(Date, nullable=True)
    priority = Column(Integer, default=1)  # 1-5で優先度を表す
    completed = Column(Boolean, default=False)
    completion_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(Date, default=datetime.now)
    updated_at = Column(Date, nullable=True)

    # リレーションシップ
    study_plan = relationship("StudyPlan", back_populates="goals")

class StudyPlanTemplate(Base):
    """学習計画テンプレートモデル"""
    __tablename__ = "study_plan_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    subject = Column(String(100), nullable=False)
    level = Column(String(50), nullable=False)
    duration_days = Column(Integer, nullable=False)
    goals = Column(JSON, nullable=False)  # 目標のJSONデータ
    created_at = Column(Date, default=datetime.now)
    updated_at = Column(Date, nullable=True) 