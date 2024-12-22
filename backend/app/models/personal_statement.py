from sqlalchemy import Column, String, UUID, Text, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
import uuid
from .base import Base, TimestampMixin
from .enums import PersonalStatementStatus

class PersonalStatement(Base, TimestampMixin):
    __tablename__ = 'personal_statements'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    desired_department_id = Column(UUID(as_uuid=True), ForeignKey('desired_departments.id'))
    content = Column(Text)
    status = Column(SQLAlchemyEnum(PersonalStatementStatus))

    # Relationships
    desired_department = relationship("DesiredDepartment", back_populates="personal_statements")
    feedbacks = relationship("Feedback", back_populates="personal_statement")

class Feedback(Base, TimestampMixin):
    __tablename__ = 'feedbacks'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    personal_statement_id = Column(UUID(as_uuid=True), ForeignKey('personal_statements.id'))
    feedback_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    content = Column(Text)

    # Relationships
    personal_statement = relationship("PersonalStatement", back_populates="feedbacks")
    feedback_user = relationship("User") 