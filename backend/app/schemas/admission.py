from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum
from .base import TimestampMixin

class AdmissionStatisticsType(str, Enum):
    OVERALL = "overall"
    BY_UNIVERSITY = "by_university"
    BY_DEPARTMENT = "by_department"
    BY_METHOD = "by_method"
    BY_YEAR = "by_year"

class AdmissionStatistics(BaseModel):
    type: AdmissionStatisticsType
    year: Optional[int] = None
    data: Dict[str, Any]
    university_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    admission_method_id: Optional[UUID] = None

class AdmissionExample(BaseModel):
    university_id: UUID
    department_id: UUID
    admission_method_id: UUID
    year: int
    profile: Dict[str, Any]  # 合格者プロフィール（点数、活動実績等）
    description: str
    
    class Config:
        from_attributes = True

class AdmissionExampleResponse(AdmissionExample, TimestampMixin):
    id: UUID
    
    class Config:
        from_attributes = True

class AdmissionMethodDetailResponse(BaseModel):
    id: UUID
    name: str
    description: str
    category: str
    university_id: UUID
    university_name: str
    required_documents: List[str]
    selection_process: str
    important_dates: Dict[str, datetime]
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DepartmentDetailResponse(BaseModel):
    id: UUID
    name: str
    faculty_name: str
    description: str
    university_id: UUID
    university_name: str
    admission_methods: List[Dict]
    quota: Optional[int] = None
    curriculum: Optional[str] = None
    career_paths: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AdmissionMethodBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True

class AdmissionMethodCreate(AdmissionMethodBase):
    pass

class AdmissionMethodUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class AdmissionMethodResponse(AdmissionMethodBase, TimestampMixin):
    id: UUID
    
    class Config:
        from_attributes = True 