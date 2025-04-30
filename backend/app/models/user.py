from sqlalchemy import Column, String, UUID, Boolean, DateTime, Integer, ForeignKey, Enum as SQLAlchemyEnum, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
import uuid
from .base import Base, TimestampMixin
from .enums import AccountLockReason, TokenBlacklistReason, RoleType, UserStatus
from typing import Optional

class Role(Base, TimestampMixin):
    __tablename__ = 'roles'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String)
    is_active = Column(Boolean, default=True)

    # Relationships
    user_roles = relationship("UserRole", back_populates="role")
    role_permissions = relationship("RolePermission", back_populates="role")
    permissions = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
        overlaps="role_permissions",
        lazy="selectin"
    )

class Permission(Base, TimestampMixin):
    __tablename__ = 'permissions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)

    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission")
    roles = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions",
        overlaps="role_permissions",
        lazy="selectin"
    )

class RolePermission(Base, TimestampMixin):
    __tablename__ = 'role_permissions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id'), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey('permissions.id'), nullable=False)
    is_granted = Column(Boolean, default=True)

    # Relationships
    role = relationship("Role", back_populates="role_permissions", overlaps="permissions,roles")
    permission = relationship("Permission", back_populates="role_permissions", overlaps="permissions,roles")

class User(Base, TimestampMixin):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100))
    is_active = Column(Boolean, default=True)  # Active status for user
    school_id = Column(UUID(as_uuid=True), ForeignKey('schools.id'))
    status = Column(SQLAlchemyEnum(UserStatus), nullable=False, default=UserStatus.PENDING)
    
    # 追加: 直接UserモデルにE-mail検証と2FA関連のフィールドを追加
    is_verified = Column(Boolean, default=False)  # メール検証が完了しているか
    is_2fa_enabled = Column(Boolean, default=False)  # 二要素認証が有効か
    totp_secret = Column(String, nullable=True)  # TOTPシークレット

    # Profile information
    grade: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    prefecture: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    profile_image_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    login_info = relationship("UserLoginInfo", back_populates="user", uselist=False)
    email_verification = relationship("UserEmailVerification", back_populates="user", uselist=False)
    two_factor_auth = relationship("UserTwoFactorAuth", back_populates="user", uselist=False)
    user_roles = relationship("UserRole", back_populates="user")
    contact_info = relationship("UserContactInfo", back_populates="user")
    school = relationship("School", back_populates="users")
    chat_sessions = relationship("ChatSession", back_populates="user")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    desired_schools = relationship("DesiredSchool", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")
    payment_history = relationship("PaymentHistory", back_populates="user")
    token_blacklist = relationship("TokenBlacklist", back_populates="user")
    study_plans = relationship("StudyPlan", back_populates="user")
    created_quizzes = relationship("Quiz", back_populates="creator")
    quiz_attempts = relationship("UserQuizAttempt", back_populates="user")
    
    # 学習パス関連
    created_learning_paths = relationship("LearningPath", foreign_keys="LearningPath.created_by")
    learning_paths = relationship("UserLearningPath", foreign_keys="UserLearningPath.user_id")
    
    # フォーラム関連
    forum_categories = relationship("ForumCategory", foreign_keys="ForumCategory.created_by")
    forum_topics = relationship("ForumTopic", foreign_keys="ForumTopic.created_by")
    forum_posts = relationship("ForumPost", foreign_keys="ForumPost.created_by")
    forum_topic_views = relationship("ForumTopicView", foreign_keys="ForumTopicView.user_id")
    
    # 通信機能のためのリレーションシップ
    conversations_as_user1 = relationship("Conversation", foreign_keys="Conversation.user1_id", back_populates="user1")
    conversations_as_user2 = relationship("Conversation", foreign_keys="Conversation.user2_id", back_populates="user2")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")

class UserProfile(Base, TimestampMixin):
    __tablename__ = 'user_profiles'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, unique=True)
    grade = Column(Integer)
    class_number = Column(String)
    student_number = Column(String)
    profile_image_url = Column(String)
    
    # Relationships
    user = relationship("User", back_populates="profile")

class UserLoginInfo(Base, TimestampMixin):
    __tablename__ = 'user_login_info'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, unique=True)
    last_login_at = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    last_failed_login_at = Column(DateTime)
    locked_until = Column(DateTime)
    account_lock_reason = Column(SQLAlchemyEnum(AccountLockReason))
    
    # Relationships
    user = relationship("User", back_populates="login_info")

class UserEmailVerification(Base, TimestampMixin):
    __tablename__ = 'user_email_verification'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, unique=True)
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String)
    email_verification_sent_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="email_verification")
    
    def sync_with_user(self):
        """ユーザーモデルと同期する"""
        if self.user:
            self.user.is_verified = self.email_verified

class UserTwoFactorAuth(Base, TimestampMixin):
    __tablename__ = 'user_two_factor_auth'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, unique=True)
    enabled = Column(Boolean, default=False)
    secret = Column(String)
    
    # Relationships
    user = relationship("User", back_populates="two_factor_auth")
    
    def sync_with_user(self):
        """ユーザーモデルと同期する"""
        if self.user:
            self.user.is_2fa_enabled = self.enabled
            self.user.totp_secret = self.secret

class UserRole(Base, TimestampMixin):
    __tablename__ = 'user_roles'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id'), nullable=False)
    is_primary = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    assignment = relationship("UserRoleAssignment", back_populates="user_role", uselist=False)
    role_metadata = relationship("UserRoleMetadata", back_populates="user_role")

class UserRoleAssignment(Base):
    __tablename__ = 'user_role_assignments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_role_id = Column(UUID(as_uuid=True), ForeignKey('user_roles.id'), nullable=False, unique=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user_role = relationship("UserRole", back_populates="assignment")
    assigner = relationship("User", foreign_keys=[assigned_by])

class UserRoleMetadata(Base):
    __tablename__ = 'user_role_metadata'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_role_id = Column(UUID(as_uuid=True), ForeignKey('user_roles.id'), nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user_role = relationship("UserRole", back_populates="role_metadata")

class TokenBlacklist(Base):
    __tablename__ = 'token_blacklist'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_jti = Column(String, nullable=False, unique=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    reason = Column(SQLAlchemyEnum(TokenBlacklistReason), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="token_blacklist")

class UserContactInfo(Base, TimestampMixin):
    __tablename__ = 'user_contact_info'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    contact_type = Column(String)  # 'phone', 'email', 'address'等
    contact_value = Column(String)
    is_primary = Column(Boolean, default=False)
    verified = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="contact_info")
