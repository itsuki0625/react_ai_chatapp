from pydantic import BaseModel
from typing import Dict, Optional

class ChecklistEvaluationBase(BaseModel):
    checklist_items: Dict
    completion_status: bool
    ai_feedback: str

class ChecklistEvaluationCreate(ChecklistEvaluationBase):
    chat_id: int

class ChecklistEvaluationUpdate(ChecklistEvaluationBase):
    pass

class ChecklistEvaluation(ChecklistEvaluationBase):
    id: int
    chat_id: int

    class Config:
        from_attributes = True 