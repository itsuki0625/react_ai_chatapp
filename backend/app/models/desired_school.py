from sqlalchemy import Column, String, UUID, Integer, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from .base import Base, TimestampMixin

class DesiredSchool(Base, TimestampMixin):
    __tablename__ = 'desired_schools'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    university_id = Column(UUID(as_uuid=True), ForeignKey('universities.id'))
    preference_order = Column(Integer)

    # Relationships
    user = relationship("User", back_populates="desired_schools")
    university = relationship("University", back_populates="desired_schools")
    desired_departments = relationship("DesiredDepartment", back_populates="desired_school")

class DesiredDepartment(Base, TimestampMixin):
    __tablename__ = 'desired_departments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    desired_school_id = Column(UUID(as_uuid=True), ForeignKey('desired_schools.id'))
    department_id = Column(UUID(as_uuid=True), ForeignKey('departments.id'))
    admission_method_id = Column(UUID(as_uuid=True), ForeignKey('admission_methods.id'))

    # Relationships
    desired_school = relationship("DesiredSchool", back_populates="desired_departments")
    department = relationship("Department", back_populates="desired_departments")
    admission_method = relationship("AdmissionMethod", back_populates="desired_departments")
    documents = relationship("Document", back_populates="desired_department")
    schedule_events = relationship("ScheduleEvent", back_populates="desired_department")
    personal_statements = relationship("PersonalStatement", back_populates="desired_department") 