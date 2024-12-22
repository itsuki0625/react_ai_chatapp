from sqlalchemy import Column, String, UUID, Boolean, JSON, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import uuid
from .base import Base, TimestampMixin
from datetime import datetime

class SystemLog(Base):
    __tablename__ = 'system_logs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    log_type = Column(String)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    action = Column(String)
    ip_address = Column(String)
    user_agent = Column(String)
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemSetting(Base, TimestampMixin):
    __tablename__ = 'system_settings'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    setting_key = Column(String, unique=True, nullable=False)
    setting_value = Column(Text)
    data_type = Column(String)
    description = Column(Text)
    is_public = Column(Boolean, default=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))

class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    title = Column(String)
    content = Column(Text)
    notification_type = Column(String)
    is_read = Column(Boolean, default=False)
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow) 