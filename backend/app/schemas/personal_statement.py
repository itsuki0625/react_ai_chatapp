from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime
from app.models.enums import PersonalStatementStatus

class PersonalStatementBase(BaseModel):
    content: str
    status: PersonalStatementStatus = PersonalStatementStatus.DRAFT
    desired_department_id: Optional[UUID] = None

class PersonalStatementCreate(PersonalStatementBase):
    pass

class PersonalStatementUpdate(BaseModel):
    content: Optional[str] = None
    status: Optional[PersonalStatementStatus] = None
    desired_department_id: Optional[UUID] = None

class UniversityInfo(BaseModel):
    name: str

class DepartmentInfo(BaseModel):
    id: UUID
    name: str
    university: UniversityInfo

class DesiredDepartmentInfo(BaseModel):
    id: UUID
    department: DepartmentInfo

class PersonalStatementResponse(BaseModel):
    id: UUID
    content: str
    status: str
    created_at: datetime
    updated_at: datetime
    user_id: UUID
    desired_department_id: Optional[UUID] = None
    desired_department: Optional[DesiredDepartmentInfo] = None

    class Config:
        from_attributes = True

class FeedbackBase(BaseModel):
    content: str

class FeedbackCreate(FeedbackBase):
    pass

class FeedbackUpdate(BaseModel):
    content: Optional[str] = None

class FeedbackResponse(FeedbackBase):
    id: UUID
    personal_statement_id: UUID
    feedback_user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 