from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from .base import TimestampMixin

class DesiredSchoolBase(BaseModel):
    university_id: UUID
    preference_order: int

class DesiredSchoolCreate(DesiredSchoolBase):
    user_id: UUID

class DesiredSchoolUpdate(BaseModel):
    preference_order: Optional[int] = None

class DesiredSchoolResponse(DesiredSchoolBase, TimestampMixin):
    id: UUID
    user_id: UUID

    class Config:
        from_attributes = True

class DesiredDepartmentBase(BaseModel):
    department_id: UUID
    admission_method_id: UUID

class DesiredDepartmentCreate(DesiredDepartmentBase):
    desired_school_id: UUID

class DesiredDepartmentUpdate(BaseModel):
    department_id: Optional[UUID] = None
    admission_method_id: Optional[UUID] = None

class DesiredDepartmentResponse(DesiredDepartmentBase, TimestampMixin):
    id: UUID
    desired_school_id: UUID

    class Config:
        from_attributes = True 