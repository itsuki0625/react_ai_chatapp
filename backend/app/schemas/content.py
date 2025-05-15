from pydantic import BaseModel, HttpUrl, Field, validator, computed_field
from datetime import datetime
from typing import Optional, List, Dict, Any
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

class ContentBase(BaseModel):
    title: str
    description: Optional[str] = None
    url: str
    content_type: ContentType
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None
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
    tags: Optional[List[str]] = Field(default_factory=list)
    category_id: Optional[UUID] = None
    provider: Optional[str] = None
    provider_item_id: Optional[str] = None

class ContentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    content_type: Optional[ContentType] = None
    thumbnail_url: Optional[str] = None
    category_id: Optional[UUID] = None
    duration: Optional[int] = None
    is_premium: Optional[bool] = None
    author: Optional[str] = None
    difficulty: Optional[int] = Field(None, ge=1, le=5)
    provider: Optional[str] = None
    provider_item_id: Optional[str] = None

class ContentCategoryInfo(BaseModel):
    id: UUID
    name: str  # 英語の識別子
    description: Optional[str] = None  # 日本語の表示名として利用
    display_order: Optional[int] = None
    icon_url: Optional[HttpUrl] = None
    is_active: Optional[bool] = None

    class Config:
        from_attributes = True

class ContentCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, description="カテゴリの英語識別子 (例: self_analysis)")
    description: Optional[str] = Field(None, description="カテゴリの日本語名 (表示用)")
    display_order: int = Field(0, description="表示順 (小さいほど先に表示)")
    icon_url: Optional[HttpUrl] = Field(None, description="アイコン画像のURL")
    is_active: bool = Field(True, description="有効フラグ")

class ContentCategoryCreate(ContentCategoryBase):
    pass

class ContentCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    display_order: Optional[int] = None
    icon_url: Optional[HttpUrl] = None
    is_active: Optional[bool] = None

class ContentResponse(ContentBase, TimestampMixin):
    id: UUID
    average_rating: Optional[float] = None
    review_count: int = 0
    view_count: int = 0
    created_by_id: Optional[UUID] = None
    category_info: Optional[ContentCategoryInfo] = None
    provider: Optional[str] = None
    provider_item_id: Optional[str] = None
    
    @computed_field
    @property
    def tags(self) -> List[str]:
        orm_tags_value = self.__dict__.get('tags')
        if isinstance(orm_tags_value, list):
            return [tag.tag_name for tag in orm_tags_value if hasattr(tag, 'tag_name')]
        return []

    class Config:
        from_attributes = True

class ContentCategoryResponse(BaseModel):
    category: ContentType
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