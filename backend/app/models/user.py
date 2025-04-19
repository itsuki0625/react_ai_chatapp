from sqlalchemy import Column, String, UUID, Boolean, DateTime, Integer, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .base import Base, TimestampMixin

class Role(Base, TimestampMixin):
    __tablename__ = 'roles'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String)
    permissions = Column(String)  # JSONやArrayなど、必要に応じて型を変更

    # Relationships
    users = relationship("User", back_populates="role")

class User(Base, TimestampMixin):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id'))
    school_id = Column(UUID(as_uuid=True), ForeignKey('schools.id'))
    grade = Column(Integer)
    class_number = Column(String)
    student_number = Column(String)
    profile_image_url = Column(String)
    is_active = Column(Boolean, default=True)   
    last_login_at = Column(DateTime)

    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user")
    chat_messages = relationship("ChatMessage", back_populates="user")
    desired_schools = relationship("DesiredSchool", back_populates="user")
    role = relationship("Role", back_populates="users")
    school = relationship("School", back_populates="users")
    subscriptions = relationship("Subscription", back_populates="user")
    payment_history = relationship("PaymentHistory", back_populates="user")
    owned_campaign_codes = relationship("CampaignCode", foreign_keys="[CampaignCode.owner_id]", back_populates="owner")
