from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from .base import TimestampMixin

class PersonalStatementBase(BaseModel):
    content: str
    status: str

class PersonalStatementCreate(PersonalStatementBase):
    user_id: UUID
    desired_department_id: UUID

class PersonalStatementUpdate(BaseModel):
    content: Optional[str] = None
    status: Optional[str] = None

class PersonalStatementResponse(PersonalStatementBase, TimestampMixin):
    id: UUID
    user_id: UUID
    desired_department_id: UUID

    class Config:
        from_attributes = True

class FeedbackBase(BaseModel):
    content: str

class FeedbackCreate(FeedbackBase):
    personal_statement_id: UUID
    feedback_user_id: UUID

class FeedbackUpdate(BaseModel):
    content: Optional[str] = None

class FeedbackResponse(FeedbackBase, TimestampMixin):
    id: UUID
    personal_statement_id: UUID
    feedback_user_id: UUID

    class Config:
        from_attributes = True 