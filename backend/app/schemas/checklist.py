from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum
from .base import TimestampMixin

class ChecklistItemStatus(str, Enum):
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    NOT_STARTED = "not_started"
    NOT_APPLICABLE = "not_applicable"

class ChecklistItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: ChecklistItemStatus = ChecklistItemStatus.NOT_STARTED
    priority: int = 0
    deadline: Optional[datetime] = None
    notes: Optional[str] = None

class ChecklistEvaluationBase(BaseModel):
    checklist_items: Dict[str, ChecklistItem]
    completion_status: bool
    ai_feedback: str

class ChecklistEvaluationCreate(ChecklistEvaluationBase):
    chat_id: UUID

class ChecklistEvaluationUpdate(BaseModel):
    checklist_items: Optional[Dict[str, ChecklistItem]] = None
    completion_status: Optional[bool] = None
    ai_feedback: Optional[str] = None

class ChecklistEvaluation(ChecklistEvaluationBase, TimestampMixin):
    id: UUID
    chat_id: UUID
    user_id: UUID
    
    class Config:
        from_attributes = True

class ChecklistTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    items: List[Dict]

class ChecklistTemplateCreate(ChecklistTemplateBase):
    pass

class ChecklistTemplateResponse(ChecklistTemplateBase, TimestampMixin):
    id: UUID
    
    class Config:
        from_attributes = True 