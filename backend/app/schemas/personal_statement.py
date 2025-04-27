from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List, Dict
from datetime import datetime
from app.models.enums import PersonalStatementStatus
from .base import TimestampMixin

class PersonalStatementBase(BaseModel):
    content: str
    status: PersonalStatementStatus = PersonalStatementStatus.DRAFT
    desired_department_id: Optional[UUID] = None
    title: Optional[str] = None
    keywords: Optional[List[str]] = None

class PersonalStatementCreate(PersonalStatementBase):
    pass

class PersonalStatementUpdate(BaseModel):
    content: Optional[str] = None
    status: Optional[PersonalStatementStatus] = None
    desired_department_id: Optional[UUID] = None
    title: Optional[str] = None
    keywords: Optional[List[str]] = None

class PersonalStatementResponse(PersonalStatementBase, TimestampMixin):
    id: UUID
    user_id: UUID
    university_name: Optional[str] = None
    department_name: Optional[str] = None
    feedback_count: int = 0
    latest_feedback_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class FeedbackBase(BaseModel):
    content: str
    highlights: Optional[Dict[str, str]] = None  # 指摘箇所と提案のマッピング
    rating: Optional[int] = None  # 評価（5段階など）

class FeedbackCreate(FeedbackBase):
    personal_statement_id: UUID

class FeedbackUpdate(BaseModel):
    content: Optional[str] = None
    highlights: Optional[Dict[str, str]] = None
    rating: Optional[int] = None

class FeedbackResponse(FeedbackBase, TimestampMixin):
    id: UUID
    personal_statement_id: UUID
    feedback_user_id: UUID
    feedback_user_name: Optional[str] = None
    is_teacher: bool = False

    class Config:
        from_attributes = True

class AIImprovementRequest(BaseModel):
    personal_statement_id: UUID
    focus_areas: Optional[List[str]] = None  # 「文章構造」「説得力」「具体性」など

class AIImprovementResponse(BaseModel):
    id: UUID
    personal_statement_id: UUID
    original_content: str
    improved_content: str
    changes_explanation: Dict[str, str]  # 変更点と説明
    created_at: datetime
    
    class Config:
        from_attributes = True 