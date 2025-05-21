from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, UUID
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
# from app.db.base_class import Base
from .base import Base

class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    endpoint = Column(String(500), nullable=False)
    auth_token = Column(String(100), nullable=False)
    p256dh_key = Column(String(100), nullable=False)
    device_info = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="push_subscriptions") 