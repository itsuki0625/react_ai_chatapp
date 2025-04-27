from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from .base import TimestampMixin

# 学習パス前提条件スキーマ
class LearningPathPrerequisiteBase(BaseModel):
    prerequisite: str

class LearningPathPrerequisiteCreate(LearningPathPrerequisiteBase):
    pass

class LearningPathPrerequisiteResponse(LearningPathPrerequisiteBase):
    id: UUID
    learning_path_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# 学習パス対象者スキーマ
class LearningPathAudienceBase(BaseModel):
    target_audience: str

class LearningPathAudienceCreate(LearningPathAudienceBase):
    pass

class LearningPathAudienceResponse(LearningPathAudienceBase):
    id: UUID
    learning_path_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# 学習パス項目スキーマ
class LearningPathItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    sequence_number: int
    is_required: bool = True
    estimated_minutes: Optional[int] = None
    content_id: Optional[UUID] = None
    quiz_id: Optional[UUID] = None

class LearningPathItemCreate(LearningPathItemBase):
    pass

class LearningPathItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    sequence_number: Optional[int] = None
    is_required: Optional[bool] = None
    estimated_minutes: Optional[int] = None
    content_id: Optional[UUID] = None
    quiz_id: Optional[UUID] = None

class LearningPathItemResponse(LearningPathItemBase, TimestampMixin):
    id: UUID
    learning_path_id: UUID

    class Config:
        from_attributes = True

# 学習パススキーマ
class LearningPathBase(BaseModel):
    title: str
    description: Optional[str] = None
    difficulty_level: str
    estimated_hours: Optional[float] = None
    is_public: bool = True
    is_featured: bool = False

class LearningPathCreate(LearningPathBase):
    prerequisites: Optional[List[LearningPathPrerequisiteCreate]] = None
    target_audiences: Optional[List[LearningPathAudienceCreate]] = None
    items: Optional[List[LearningPathItemCreate]] = None

class LearningPathUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    difficulty_level: Optional[str] = None
    estimated_hours: Optional[float] = None
    is_public: Optional[bool] = None
    is_featured: Optional[bool] = None
    prerequisites: Optional[List[LearningPathPrerequisiteCreate]] = None
    target_audiences: Optional[List[LearningPathAudienceCreate]] = None

class LearningPathResponse(LearningPathBase, TimestampMixin):
    id: UUID
    created_by: UUID
    prerequisites: List[LearningPathPrerequisiteResponse] = []
    target_audiences: List[LearningPathAudienceResponse] = []
    items: List[LearningPathItemResponse] = []

    class Config:
        from_attributes = True

# ユーザー学習パス関連スキーマ
class UserLearningPathBase(BaseModel):
    learning_path_id: UUID

class UserLearningPathCreate(UserLearningPathBase):
    pass

class UserLearningPathUpdate(BaseModel):
    completed: Optional[bool] = None
    completed_at: Optional[datetime] = None
    progress_percentage: Optional[float] = None

class UserLearningPathResponse(UserLearningPathBase, TimestampMixin):
    id: UUID
    user_id: UUID
    start_date: Optional[datetime] = None
    completed: bool = False
    completed_at: Optional[datetime] = None
    progress_percentage: float = 0.0

    class Config:
        from_attributes = True

# ユーザー学習パス項目スキーマ
class UserLearningPathItemBase(BaseModel):
    learning_path_item_id: UUID
    status: str

class UserLearningPathItemCreate(UserLearningPathItemBase):
    pass

class UserLearningPathItemUpdate(BaseModel):
    status: Optional[str] = None
    completed_at: Optional[datetime] = None

class UserLearningPathItemResponse(UserLearningPathItemBase, TimestampMixin):
    id: UUID
    user_learning_path_id: UUID
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# ユーザー学習パスノートスキーマ
class UserLearningPathNoteBase(BaseModel):
    note: str

class UserLearningPathNoteCreate(UserLearningPathNoteBase):
    user_learning_path_item_id: UUID

class UserLearningPathNoteResponse(UserLearningPathNoteBase, TimestampMixin):
    id: UUID
    user_learning_path_item_id: UUID
    
    class Config:
        from_attributes = True 