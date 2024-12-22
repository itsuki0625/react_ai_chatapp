from sqlalchemy import Column, String, UUID, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from .base import Base, TimestampMixin

class AdmissionMethod(Base, TimestampMixin):
    __tablename__ = 'admission_methods'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String)
    is_active = Column(Boolean, default=True)

    # Relationships
    desired_departments = relationship("DesiredDepartment", back_populates="admission_method") 