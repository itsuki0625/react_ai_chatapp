from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict
from uuid import UUID
from enum import Enum
from datetime import datetime
from .base import TimestampMixin

class UniversityBase(BaseModel):
    name: str
    university_code: str
    is_active: bool = True

class UniversityCreate(UniversityBase):
    pass

class UniversityUpdate(BaseModel):
    name: Optional[str] = None
    university_code: Optional[str] = None
    is_active: Optional[bool] = None

class DepartmentBase(BaseModel):
    name: str
    department_code: str
    is_active: bool = True

class DepartmentCreate(DepartmentBase):
    university_id: UUID

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    department_code: Optional[str] = None
    is_active: Optional[bool] = None

class DepartmentResponse(DepartmentBase, TimestampMixin):
    id: UUID
    university_id: UUID
    
    class Config:
        from_attributes = True

class UniversityResponse(UniversityBase, TimestampMixin):
    id: UUID
    departments: Optional[List['DepartmentResponse']] = []
    
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

class UniversitySearchParams(BaseModel):
    name: Optional[str] = None
    prefecture: Optional[str] = None
    is_national: Optional[bool] = None
    faculty_name: Optional[str] = None
    department_name: Optional[str] = None
    limit: int = 10
    offset: int = 0

class RecommendedUniversityResponse(BaseModel):
    university: UniversityResponse
    matching_score: float
    matching_reasons: List[str]
    
    class Config:
        from_attributes = True 