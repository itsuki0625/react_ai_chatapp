from sqlalchemy import Column, String, UUID, Boolean, ForeignKey, Enum as SQLAlchemyEnum, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .base import Base, TimestampMixin
from .enums import AssignmentType

class TeacherStudentAssignment(Base, TimestampMixin):
    """先生と生徒の担当関係を管理するモデル"""
    __tablename__ = 'teacher_student_assignments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    school_id = Column(UUID(as_uuid=True), ForeignKey('schools.id'), nullable=False)
    
    # 担当の種別
    assignment_type = Column(SQLAlchemyEnum(AssignmentType), nullable=False, default=AssignmentType.PRIMARY)
    subject = Column(String, nullable=True)  # 担当教科（任意）
    
    # 担当状態
    is_active = Column(Boolean, default=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)  # 担当を設定した管理者
    
    # 備考・メモ
    notes = Column(String, nullable=True)

    # Relationships
    teacher = relationship("User", foreign_keys=[teacher_id], back_populates="teacher_assignments")
    student = relationship("User", foreign_keys=[student_id], back_populates="student_assignments") 
    school = relationship("School")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])

class SchoolAdminSettings(Base, TimestampMixin):
    """学校管理者固有の設定を管理するモデル"""
    __tablename__ = 'school_admin_settings'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    school_id = Column(UUID(as_uuid=True), ForeignKey('schools.id'), nullable=False)
    
    # 管理者権限レベル
    permission_level = Column(String, default='standard')  # 'standard', 'full'
    
    # 通知設定
    notification_settings = Column(String, nullable=True)  # JSON文字列
    
    # その他設定
    dashboard_preferences = Column(String, nullable=True)  # ダッシュボードの設定
    
    # Relationships
    user = relationship("User")
    school = relationship("School")

class SchoolSettings(Base, TimestampMixin):
    """学校固有の設定を管理するモデル"""
    __tablename__ = 'school_settings'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey('schools.id'), nullable=False, unique=True)
    
    # 機能設定
    allow_student_chat = Column(Boolean, default=True)
    require_statement_approval = Column(Boolean, default=True)
    enable_analytics = Column(Boolean, default=True)
    enable_teacher_student_assignment = Column(Boolean, default=True)
    
    # ブランディング設定
    primary_color = Column(String, default='#3B82F6')
    secondary_color = Column(String, default='#10B981')
    accent_color = Column(String, default='#F59E0B')
    school_logo_url = Column(String, nullable=True)
    
    # 通知設定
    email_notifications_enabled = Column(Boolean, default=True)
    push_notifications_enabled = Column(Boolean, default=True)
    digest_frequency = Column(String, default='weekly')  # 'daily', 'weekly', 'monthly'
    
    # その他設定
    custom_settings = Column(String, nullable=True)  # JSON文字列で追加設定を保存
    
    # Relationships
    school = relationship("School", back_populates="settings")
