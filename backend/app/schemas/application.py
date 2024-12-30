from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.enums import DocumentStatus

class ApplicationBase(BaseModel):
    university_id: UUID
    department_id: UUID
    admission_method_id: UUID
    priority: int  # preference_order
    notes: Optional[str] = None

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationUpdate(ApplicationBase):
    pass

class ApplicationResponse(ApplicationBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
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
    pass

class DocumentUpdate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: UUID
    desired_department_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# スケジュール関連のスキーマ
class ScheduleBase(BaseModel):
    event_name: str
    date: datetime
    event_type: str
    notes: Optional[str] = None

class ScheduleCreate(ScheduleBase):
    pass

class ScheduleUpdate(ScheduleBase):
    pass

class ScheduleResponse(ScheduleBase):
    id: UUID
    desired_department_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 拡張されたApplicationResponse
class DesiredDepartmentInfo(BaseModel):
    id: UUID
    department_id: UUID
    department_name: str

class ApplicationDetailResponse(ApplicationResponse):
    documents: List[DocumentResponse]
    schedules: List[ScheduleResponse]
    desired_departments: List[DesiredDepartmentInfo]

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