from sqlalchemy import Column, String, UUID, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from .base import Base, TimestampMixin

class AdmissionMethod(Base, TimestampMixin):
    __tablename__ = 'admission_methods'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    details = relationship("AdmissionMethodDetails", back_populates="admission_method", uselist=False)
    desired_departments = relationship("DesiredDepartment", back_populates="admission_method")

class AdmissionMethodDetails(Base, TimestampMixin):
    __tablename__ = 'admission_method_details'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_method_id = Column(UUID(as_uuid=True), ForeignKey('admission_methods.id'), nullable=False, unique=True)
    description = Column(Text)

    # Relationships
    admission_method = relationship("AdmissionMethod", back_populates="details") 