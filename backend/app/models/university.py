from sqlalchemy import Column, String, UUID, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from .base import Base, TimestampMixin

class University(Base, TimestampMixin):
    __tablename__ = 'universities'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    university_code = Column(String, unique=True, nullable=False)
    address = Column(Text)
    prefecture = Column(String)
    city = Column(String)
    zip_code = Column(String)
    contact_email = Column(String)
    contact_phone = Column(String)
    president_name = Column(String)
    website_url = Column(String)
    is_active = Column(Boolean, default=True)

    # Relationships
    departments = relationship("Department", back_populates="university")
    desired_schools = relationship("DesiredSchool", back_populates="university")

class Department(Base, TimestampMixin):
    __tablename__ = 'departments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    university_id = Column(UUID(as_uuid=True), ForeignKey('universities.id'))
    name = Column(String, nullable=False)
    department_code = Column(String, unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    # Relationships
    university = relationship("University", back_populates="departments")
    desired_departments = relationship("DesiredDepartment", back_populates="department") 