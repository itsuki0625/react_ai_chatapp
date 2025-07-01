from pydantic import BaseModel, Field, validator
from uuid import UUID
from typing import Optional, List, Dict
from datetime import datetime
from app.models.enums import PersonalStatementStatus, ChatType
from .base import TimestampMixin

class PersonalStatementBase(BaseModel):
    content: str
    status: PersonalStatementStatus = PersonalStatementStatus.DRAFT
    desired_department_id: Optional[UUID] = None
    title: Optional[str] = None
    keywords: Optional[List[str]] = None
    self_analysis_chat_id: Optional[UUID] = None
    submission_deadline: Optional[datetime] = None

class PersonalStatementCreate(PersonalStatementBase):
    pass

class PersonalStatementUpdate(BaseModel):
    content: Optional[str] = None
    status: Optional[PersonalStatementStatus] = None
    desired_department_id: Optional[UUID] = None
    title: Optional[str] = None
    keywords: Optional[List[str]] = None
    self_analysis_chat_id: Optional[UUID] = None
    submission_deadline: Optional[datetime] = None

class PersonalStatementResponse(PersonalStatementBase, TimestampMixin):
    id: UUID
    user_id: UUID
    university_name: Optional[str] = None
    department_name: Optional[str] = None
    feedback_count: int = 0
    latest_feedback_at: Optional[datetime] = None
    word_count: int = 0
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm_with_counts(cls, statement) -> 'PersonalStatementResponse':
        """ORMオブジェクトから計算フィールドを含むレスポンスを作成"""
        # 文字数を計算
        word_count = len(statement.content) if statement.content else 0
        
        # フィードバック数を計算
        feedback_count = len(statement.feedback) if statement.feedback else 0
        
        # 最新フィードバック日時を取得
        latest_feedback_at = None
        if statement.feedback:
            latest_feedback_at = max(f.created_at for f in statement.feedback)
        
        # 大学名・学部名を取得
        university_name = None
        department_name = None
        if statement.desired_department:
            department_name = statement.desired_department.department.name if statement.desired_department.department else None
            if statement.desired_department.department and statement.desired_department.department.university:
                university_name = statement.desired_department.department.university.name
        
        # レスポンスオブジェクトを作成
        return cls(
            id=statement.id,
            user_id=statement.user_id,
            content=statement.content,
            status=statement.status,
            desired_department_id=statement.desired_department_id,
            title=statement.title,
            keywords=statement.keywords or [],
            self_analysis_chat_id=statement.self_analysis_chat_id,
            submission_deadline=statement.submission_deadline,
            created_at=statement.created_at,
            updated_at=statement.updated_at,
            university_name=university_name,
            department_name=department_name,
            feedback_count=feedback_count,
            latest_feedback_at=latest_feedback_at,
            word_count=word_count
        )

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