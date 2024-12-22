from sqlalchemy import Column, String, UUID, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from .base import Base, TimestampMixin

class ScheduleEvent(Base, TimestampMixin):
    __tablename__ = 'schedule_events'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    desired_department_id = Column(UUID(as_uuid=True), ForeignKey('desired_departments.id'))
    event_name = Column(String, nullable=False)
    date = Column(DateTime)
    type = Column(String)
    completed = Column(Boolean, default=False)

    # Relationships
    desired_department = relationship("DesiredDepartment", back_populates="schedule_events") 