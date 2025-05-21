from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
from app.models.enums import NotificationType
import uuid
from datetime import datetime
from sqlalchemy.orm import relationship

class NotificationSetting(Base):
    __tablename__ = 'notification_settings'
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False)
    email_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=False)
    in_app_enabled = Column(Boolean, default=True)
    quiet_hours_start = Column(DateTime, nullable=True)
    quiet_hours_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="notification_settings") 