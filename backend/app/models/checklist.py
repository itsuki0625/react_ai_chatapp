from sqlalchemy import Column, String, Boolean, ForeignKey, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base, TimestampMixin

class ChecklistEvaluation(Base, TimestampMixin):
    __tablename__ = "checklist_evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    checklist_item = Column(String, nullable=False)
    is_completed = Column(Boolean, default=False)
    score = Column(Integer)
    evaluator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    evaluated_at = Column(DateTime)

    # Relationships
    chat_session = relationship("ChatSession", back_populates="checklist_evaluation")
    evaluator = relationship("User") 