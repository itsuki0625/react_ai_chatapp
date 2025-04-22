from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID
from app.models.enums import DocumentStatus
from .base import TimestampMixin

class ApplicationBase(BaseModel):
    university_id: UUID
    department_id: UUID
    admission_method_id: UUID
    priority: int  # preference_order
    notes: Optional[str] = None

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationUpdate(BaseModel):
    university_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    admission_method_id: Optional[UUID] = None
    priority: Optional[int] = None
    notes: Optional[str] = None

class ApplicationResponse(ApplicationBase, TimestampMixin):
    id: UUID
    user_id: UUID
    university_name: str
    department_name: str
    admission_method_name: str

    class Config:
        from_attributes = True

# 書類関連のスキーマ
class DocumentBase(BaseModel):
    name: str
    status: DocumentStatus
    deadline: datetime
    notes: Optional[str] = None

class DocumentCreate(DocumentBase):
    application_id: UUID

class DocumentUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[DocumentStatus] = None
    deadline: Optional[datetime] = None
    notes: Optional[str] = None

class DocumentResponse(DocumentBase, TimestampMixin):
    id: UUID
    application_id: UUID

    class Config:
        from_attributes = True

# スケジュール関連のスキーマ
class ScheduleBase(BaseModel):
    event_name: str
    date: datetime
    type: str
    location: Optional[str] = None
    description: Optional[str] = None

class ScheduleCreate(ScheduleBase):
    application_id: UUID

class ScheduleUpdate(BaseModel):
    event_name: Optional[str] = None
    date: Optional[datetime] = None
    type: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None

class ScheduleResponse(ScheduleBase, TimestampMixin):
    id: UUID
    application_id: UUID

    class Config:
        from_attributes = True

# 志望校詳細レスポンス
class ApplicationDepartmentInfo(BaseModel):
    id: UUID
    department_id: UUID
    department_name: str
    faculty_name: str

class ApplicationDetailResponse(ApplicationResponse):
    documents: List[DocumentResponse]
    schedules: List[ScheduleResponse]
    department_details: List[ApplicationDepartmentInfo]

    class Config:
        from_attributes = True

class UniversityResponse(BaseModel):
    name: str

class DepartmentResponse(BaseModel):
    id: UUID
    name: str
    university: UniversityResponse

class DesiredDepartmentResponse(BaseModel):
    id: UUID
    department: DepartmentResponse

    class Config:
        from_attributes = True

# 志望校の優先順位を更新するためのスキーマ
class ReorderApplications(BaseModel):
    application_order: Dict[str, int]  # 志望校ID: 優先順位 