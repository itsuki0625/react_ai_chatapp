from sqlalchemy import Column, String, UUID, Boolean, JSON, Text, ForeignKey, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
import uuid
from .base import Base, TimestampMixin
from datetime import datetime
from .enums import NotificationType, NotificationPriority, AuditLogAction, AuditLogStatus

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

class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text)
    notification_type = Column(SQLAlchemyEnum(NotificationType), nullable=False)
    related_entity_type = Column(String)  # 'chat_message', 'subscription'等
    related_entity_id = Column(UUID(as_uuid=True))
    broadcast_notification_id = Column(UUID(as_uuid=True), ForeignKey('broadcast_notifications.id'))
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    is_action_required = Column(Boolean, default=False)
    action_url = Column(String)
    sent_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    priority = Column(SQLAlchemyEnum(NotificationPriority), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
    broadcast_notification = relationship("BroadcastNotification", back_populates="notifications")
    notification_metadata = relationship("NotificationMetaData", back_populates="notification")

class NotificationMetaData(Base):
    __tablename__ = 'notification_metadata'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notification_id = Column(UUID(as_uuid=True), ForeignKey('notifications.id'), nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    notification = relationship("Notification", back_populates="notification_metadata")

class NotificationSetting(Base, TimestampMixin):
    __tablename__ = 'notification_settings'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    notification_type = Column(SQLAlchemyEnum(NotificationType), nullable=False)
    email_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)
    quiet_hours_start = Column(DateTime)
    quiet_hours_end = Column(DateTime)

    # Relationships
    user = relationship("User")

class BroadcastNotification(Base, TimestampMixin):
    __tablename__ = 'broadcast_notifications'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    content = Column(Text)
    notification_type = Column(SQLAlchemyEnum(NotificationType), nullable=False)
    action_url = Column(String)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    scheduled_at = Column(DateTime)
    sent_at = Column(DateTime)
    expires_at = Column(DateTime)
    priority = Column(SQLAlchemyEnum(NotificationPriority), nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    creator = relationship("User")
    target_roles = relationship("BroadcastTargetRole", back_populates="broadcast_notification")
    target_schools = relationship("BroadcastTargetSchool", back_populates="broadcast_notification")
    broadcast_metadata = relationship("BroadcastNotificationMetaData", back_populates="broadcast_notification")
    notifications = relationship("Notification", back_populates="broadcast_notification")

class BroadcastTargetRole(Base):
    __tablename__ = 'broadcast_target_roles'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    broadcast_notification_id = Column(UUID(as_uuid=True), ForeignKey('broadcast_notifications.id'), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    broadcast_notification = relationship("BroadcastNotification", back_populates="target_roles")
    role = relationship("Role")

class BroadcastTargetSchool(Base):
    __tablename__ = 'broadcast_target_schools'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    broadcast_notification_id = Column(UUID(as_uuid=True), ForeignKey('broadcast_notifications.id'), nullable=False)
    school_id = Column(UUID(as_uuid=True), ForeignKey('schools.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    broadcast_notification = relationship("BroadcastNotification", back_populates="target_schools")
    school = relationship("School")

class BroadcastNotificationMetaData(Base):
    __tablename__ = 'broadcast_notification_metadata'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    broadcast_notification_id = Column(UUID(as_uuid=True), ForeignKey('broadcast_notifications.id'), nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    broadcast_notification = relationship("BroadcastNotification", back_populates="broadcast_metadata")

class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    action = Column(SQLAlchemyEnum(AuditLogAction), nullable=False)
    entity_type = Column(String, nullable=False)  # 'user', 'role', 'subscription'等
    entity_id = Column(UUID(as_uuid=True))
    ip_address = Column(String)
    user_agent = Column(String)
    status = Column(SQLAlchemyEnum(AuditLogStatus), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")
    details = relationship("AuditLogDetails", back_populates="audit_log")
    additional_info = relationship("AuditLogAdditionalInfo", back_populates="audit_log")

class AuditLogDetails(Base):
    __tablename__ = 'audit_log_details'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_log_id = Column(UUID(as_uuid=True), ForeignKey('audit_logs.id'), nullable=False)
    key = Column(String, nullable=False)
    old_value = Column(Text)
    new_value = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    audit_log = relationship("AuditLog", back_populates="details")

class AuditLogAdditionalInfo(Base):
    __tablename__ = 'audit_log_additional_info'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_log_id = Column(UUID(as_uuid=True), ForeignKey('audit_logs.id'), nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    audit_log = relationship("AuditLog", back_populates="additional_info")

class SystemSetting(Base, TimestampMixin):
    __tablename__ = 'system_settings'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    setting_key = Column(String, unique=True, nullable=False)
    setting_value = Column(Text)
    data_type = Column(String)
    description = Column(Text)
    is_public = Column(Boolean, default=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))

    # Relationships
    updater = relationship("User") 