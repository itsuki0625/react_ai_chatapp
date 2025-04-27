from sqlalchemy import Column, String, UUID, Boolean, DateTime, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from .base import Base, TimestampMixin
from .enums import DocumentStatus

class Document(Base, TimestampMixin):
    __tablename__ = 'documents'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    desired_department_id = Column(UUID(as_uuid=True), ForeignKey('desired_departments.id'), nullable=False)
    name = Column(String, nullable=False)
    status = Column(SQLAlchemyEnum(DocumentStatus), nullable=False)
    deadline = Column(DateTime)

    # Relationships
    desired_department = relationship("DesiredDepartment", back_populates="documents")
    submission = relationship("DocumentSubmission", back_populates="document", uselist=False)

class DocumentSubmission(Base, TimestampMixin):
    __tablename__ = 'document_submissions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'), nullable=False, unique=True)
    submitted_at = Column(DateTime)
    submitted_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    # Relationships
    document = relationship("Document", back_populates="submission")
    submitter = relationship("User") 