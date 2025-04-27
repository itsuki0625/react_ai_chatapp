from sqlalchemy import Column, String, UUID, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from .base import Base, TimestampMixin

class ScheduleEvent(Base, TimestampMixin):
    __tablename__ = 'schedule_events'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    desired_department_id = Column(UUID(as_uuid=True), ForeignKey('desired_departments.id'), nullable=False)
    event_name = Column(String, nullable=False)
    event_date = Column(DateTime, nullable=False)
    event_type = Column(String, nullable=False)

    # Relationships
    desired_department = relationship("DesiredDepartment", back_populates="schedule_events")
    completion = relationship("EventCompletion", back_populates="event", uselist=False)

class EventCompletion(Base, TimestampMixin):
    __tablename__ = 'event_completions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey('schedule_events.id'), nullable=False, unique=True)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    completed_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))

    # Relationships
    event = relationship("ScheduleEvent", back_populates="completion")
    completer = relationship("User") 