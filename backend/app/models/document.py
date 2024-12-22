from sqlalchemy import Column, String, UUID, DateTime, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
import uuid
from .base import Base, TimestampMixin
from .enums import DocumentStatus

class Document(Base, TimestampMixin):
    __tablename__ = 'documents'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    desired_department_id = Column(UUID(as_uuid=True), ForeignKey('desired_departments.id'))
    name = Column(String, nullable=False)
    status = Column(SQLAlchemyEnum(DocumentStatus))
    deadline = Column(DateTime)

    # Relationships
    desired_department = relationship("DesiredDepartment", back_populates="documents") 