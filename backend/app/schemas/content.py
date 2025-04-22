from pydantic import BaseModel, HttpUrl, Field, validator
from datetime import datetime
from typing import Optional, List, Dict
from uuid import UUID
from enum import Enum
from .base import TimestampMixin

class ContentType(str, Enum):
    VIDEO = "video"
    SLIDE = "slide"
    PDF = "pdf"
    AUDIO = "audio"
    ARTICLE = "article"
    QUIZ = "quiz"
    EXTERNAL_LINK = "external_link"

class ContentCategory(str, Enum):
    SELF_ANALYSIS = "self_analysis"  # 自己分析
    ADMISSIONS = "admissions"  # 入試対策
    ACADEMIC = "academic"  # 学習一般
    UNIVERSITY_INFO = "university_info"  # 大学情報
    CAREER = "career"  # キャリア
    OTHER = "other"  # その他

class ContentBase(BaseModel):
    title: str
    description: Optional[str] = None
    url: str
    content_type: ContentType
    thumbnail_url: Optional[str] = None
    category: ContentCategory
    tags: Optional[List[str]] = Field(default_factory=list)
    duration_seconds: Optional[int] = None
    is_premium: bool = False
    author: Optional[str] = None
    difficulty: Optional[int] = Field(None, ge=1, le=5)  # 1-5の難易度

    @validator('difficulty')
    def validate_difficulty(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('難易度は1から5の間でなければなりません')
        return v

class ContentCreate(ContentBase):
    created_by_id: UUID

class ContentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    content_type: Optional[ContentType] = None
    thumbnail_url: Optional[str] = None
    category: Optional[ContentCategory] = None
    tags: Optional[List[str]] = None
    duration_seconds: Optional[int] = None
    is_premium: Optional[bool] = None
    author: Optional[str] = None
    difficulty: Optional[int] = Field(None, ge=1, le=5)

class ContentResponse(ContentBase, TimestampMixin):
    id: UUID
    average_rating: Optional[float] = None
    review_count: int = 0
    view_count: int = 0
    created_by_id: UUID
    
    class Config:
        from_attributes = True

class ContentCategoryResponse(BaseModel):
    category: ContentCategory
    name: str
    description: Optional[str] = None
    content_count: int
    
    class Config:
        from_attributes = True

class ReviewBase(BaseModel):
    content_id: UUID
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    
    @validator('rating')
    def validate_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError('評価は1から5の間でなければなりません')
        return v

class ReviewCreate(ReviewBase):
    pass

class ReviewResponse(ReviewBase, TimestampMixin):
    id: UUID
    user_id: UUID
    user_name: str
    
    class Config:
        from_attributes = True

class ContentViewCreate(BaseModel):
    content_id: UUID
    watched_seconds: Optional[int] = None
    completed: bool = False

class ContentViewResponse(BaseModel):
    id: UUID
    content_id: UUID
    user_id: UUID
    watched_seconds: int
    completed: bool
    last_position: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    content: Optional[ContentResponse] = None
    
    class Config:
        from_attributes = True

class ContentRecommendationResponse(BaseModel):
    content: ContentResponse
    recommendation_reason: str
    score: float
    
    class Config:
        from_attributes = True

class FAQBase(BaseModel):
    question: str
    answer: str
    category: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)

class FAQCreate(FAQBase):
    pass

class FAQResponse(FAQBase, TimestampMixin):
    id: UUID
    
    class Config:
        from_attributes = True 