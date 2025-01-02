from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from .base import Base

class ChecklistEvaluation(Base):
    __tablename__ = "checklist_evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"))
    checklist_items = Column(JSON)  # チェックリストの項目と状態
    completion_status = Column(String)  # booleanからstringに変更
    ai_feedback = Column(Text)

    chat = relationship("ChatSession", back_populates="checklist_evaluation") 