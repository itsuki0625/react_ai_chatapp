from sqlalchemy import Column, String, Text, UUID, DateTime, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
import uuid
from .base import Base, TimestampMixin
from .enums import PersonalStatementStatus

class PersonalStatement(Base, TimestampMixin):
    __tablename__ = 'personal_statements'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    desired_department_id = Column(UUID(as_uuid=True), ForeignKey('desired_departments.id'), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(SQLAlchemyEnum(PersonalStatementStatus), nullable=False)
    submission_deadline = Column(DateTime)

    # Relationships
    user = relationship("User")
    desired_department = relationship("DesiredDepartment", back_populates="personal_statements")
    submission = relationship("PersonalStatementSubmission", back_populates="personal_statement", uselist=False)
    feedback = relationship("Feedback", back_populates="personal_statement")

class PersonalStatementSubmission(Base, TimestampMixin):
    __tablename__ = 'personal_statement_submissions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    personal_statement_id = Column(UUID(as_uuid=True), ForeignKey('personal_statements.id'), nullable=False, unique=True)
    submitted_at = Column(DateTime)
    submitted_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    # Relationships
    personal_statement = relationship("PersonalStatement", back_populates="submission")
    submitter = relationship("User")

class Feedback(Base, TimestampMixin):
    __tablename__ = 'feedback'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    personal_statement_id = Column(UUID(as_uuid=True), ForeignKey('personal_statements.id'), nullable=False)
    feedback_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)

    # Relationships
    personal_statement = relationship("PersonalStatement", back_populates="feedback")
    feedback_user = relationship("User") 