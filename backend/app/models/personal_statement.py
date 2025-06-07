from sqlalchemy import Column, String, Text, UUID, DateTime, ForeignKey, Enum as SQLAlchemyEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
import uuid
from .base import Base, TimestampMixin
from .enums import PersonalStatementStatus
from .chat import ChatSession

class PersonalStatement(Base, TimestampMixin):
    __tablename__ = 'personal_statements'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    desired_department_id = Column(UUID(as_uuid=True), ForeignKey('desired_departments.id'), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(SQLAlchemyEnum(PersonalStatementStatus), nullable=False)
    submission_deadline = Column(DateTime)
    self_analysis_chat_id = Column(UUID(as_uuid=True), ForeignKey('chat_sessions.id'), nullable=True)
    title = Column(String, nullable=True)
    keywords = Column(ARRAY(String), nullable=True)

    # Relationships
    user = relationship("User")
    desired_department = relationship("DesiredDepartment", back_populates="personal_statements")
    submission = relationship("PersonalStatementSubmission", back_populates="personal_statement", uselist=False)
    feedback = relationship("Feedback", back_populates="personal_statement")
    self_analysis_chat = relationship("ChatSession", back_populates="linked_personal_statements")
    
    revisions = relationship("PersonalStatementRevision", back_populates="personal_statement", order_by="PersonalStatementRevision.created_at.desc()")
    evaluations = relationship("EvaluationResult", back_populates="personal_statement", order_by="EvaluationResult.created_at.desc()")

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

class PersonalStatementRevision(Base, TimestampMixin):
    __tablename__ = 'personal_statement_revisions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    personal_statement_id = Column(UUID(as_uuid=True), ForeignKey('personal_statements.id'), nullable=False)
    version_number = Column(String, nullable=False)
    content_snapshot = Column(Text, nullable=False)
    edited_by_agent_id = Column(String, nullable=True)

    # Relationships
    personal_statement = relationship("PersonalStatement", back_populates="revisions")

class EvaluationResult(Base, TimestampMixin):
    __tablename__ = 'evaluation_results'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    personal_statement_id = Column(UUID(as_uuid=True), ForeignKey('personal_statements.id'), nullable=False)
    
    evaluator_agent_id = Column(String, nullable=False)
    rubric_id = Column(String, nullable=True)
    score_table = Column(JSON, nullable=False)
    advice_md = Column(Text, nullable=False)

    # Relationships
    personal_statement = relationship("PersonalStatement", back_populates="evaluations") 