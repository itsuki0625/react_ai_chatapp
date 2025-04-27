from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict
from uuid import UUID
from enum import Enum
from datetime import datetime
from .base import TimestampMixin

class UniversityBase(BaseModel):
    name: str
    prefecture: str
    address: Optional[str] = None
    website_url: Optional[HttpUrl] = None
    description: Optional[str] = None
    is_national: bool = False  # 国公立か私立か
    logo_url: Optional[HttpUrl] = None

class UniversityCreate(UniversityBase):
    pass

class UniversityUpdate(BaseModel):
    name: Optional[str] = None
    prefecture: Optional[str] = None
    address: Optional[str] = None
    website_url: Optional[HttpUrl] = None
    description: Optional[str] = None
    is_national: Optional[bool] = None
    logo_url: Optional[HttpUrl] = None

class DepartmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    faculty_name: str  # 学部名

class DepartmentCreate(DepartmentBase):
    university_id: UUID

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    faculty_name: Optional[str] = None

class DepartmentResponse(DepartmentBase, TimestampMixin):
    id: UUID
    university_id: UUID
    
    class Config:
        from_attributes = True

class UniversityResponse(UniversityBase, TimestampMixin):
    id: UUID
    departments: Optional[List[DepartmentResponse]] = None
    
    class Config:
        from_attributes = True

class AdmissionMethodBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str  # 一般入試、総合型選抜、学校推薦型など

class AdmissionMethodCreate(AdmissionMethodBase):
    university_id: UUID

class AdmissionMethodUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None

class AdmissionMethodResponse(AdmissionMethodBase, TimestampMixin):
    id: UUID
    university_id: UUID
    
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