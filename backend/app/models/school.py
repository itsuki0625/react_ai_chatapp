from sqlalchemy import Column, String, UUID, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from .base import Base, TimestampMixin

class School(Base, TimestampMixin):
    __tablename__ = 'schools'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    school_code = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    details = relationship("SchoolDetails", back_populates="school", uselist=False)
    contacts = relationship("SchoolContact", back_populates="school")
    users = relationship("User", back_populates="school")

class SchoolDetails(Base, TimestampMixin):
    __tablename__ = 'school_details'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey('schools.id'), nullable=False, unique=True)
    address = Column(Text)
    prefecture = Column(String)
    city = Column(String)
    zip_code = Column(String)
    principal_name = Column(String)
    website_url = Column(String)

    # Relationships
    school = relationship("School", back_populates="details")

class SchoolContact(Base, TimestampMixin):
    __tablename__ = 'school_contacts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey('schools.id'), nullable=False)
    contact_type = Column(String)  # 'phone', 'email', 'fax'等
    contact_value = Column(String)
    is_primary = Column(Boolean, default=False)

    # Relationships
    school = relationship("School", back_populates="contacts") 