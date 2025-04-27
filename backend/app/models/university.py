from sqlalchemy import Column, String, UUID, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from .base import Base, TimestampMixin

class University(Base, TimestampMixin):
    __tablename__ = 'universities'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    university_code = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    details = relationship("UniversityDetails", back_populates="university", uselist=False)
    contacts = relationship("UniversityContact", back_populates="university")
    departments = relationship("Department", back_populates="university")
    desired_schools = relationship("DesiredSchool", back_populates="university")

class UniversityDetails(Base, TimestampMixin):
    __tablename__ = 'university_details'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    university_id = Column(UUID(as_uuid=True), ForeignKey('universities.id'), nullable=False, unique=True)
    address = Column(Text)
    prefecture = Column(String)
    city = Column(String)
    zip_code = Column(String)
    president_name = Column(String)
    website_url = Column(String)

    # Relationships
    university = relationship("University", back_populates="details")

class UniversityContact(Base, TimestampMixin):
    __tablename__ = 'university_contacts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    university_id = Column(UUID(as_uuid=True), ForeignKey('universities.id'), nullable=False)
    contact_type = Column(String)  # 'phone', 'email', 'fax'等
    contact_value = Column(String)
    is_primary = Column(Boolean, default=False)

    # Relationships
    university = relationship("University", back_populates="contacts")

class Department(Base, TimestampMixin):
    __tablename__ = 'departments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    university_id = Column(UUID(as_uuid=True), ForeignKey('universities.id'), nullable=False)
    name = Column(String, nullable=False)
    department_code = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    university = relationship("University", back_populates="departments")
    details = relationship("DepartmentDetails", back_populates="department", uselist=False)
    desired_departments = relationship("DesiredDepartment", back_populates="department")

class DepartmentDetails(Base, TimestampMixin):
    __tablename__ = 'department_details'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id = Column(UUID(as_uuid=True), ForeignKey('departments.id'), nullable=False, unique=True)
    description = Column(Text)

    # Relationships
    department = relationship("Department", back_populates="details") 