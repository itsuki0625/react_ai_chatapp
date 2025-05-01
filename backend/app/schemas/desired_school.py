from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from .base import TimestampMixin
# 循環参照を避けるために Optional で型ヒント、または forward ref を検討
# from .university import UniversityResponse 
# from .department import DepartmentResponse
# from .admission import AdmissionMethodResponse

# --- DesiredDepartment Schemas ---

class DesiredDepartmentBase(BaseModel):
    department_id: UUID
    admission_method_id: UUID

class DesiredDepartmentCreate(DesiredDepartmentBase):
    pass

class DesiredDepartmentResponse(DesiredDepartmentBase, TimestampMixin):
    id: UUID
    desired_school_id: UUID
    # TODO: Populate related data if needed in response
    # department: Optional[DepartmentResponse] = None
    # admission_method: Optional[AdmissionMethodResponse] = None

    model_config = {
        "from_attributes": True,
    }

# --- DesiredSchool Schemas ---

class DesiredSchoolBase(BaseModel):
    university_id: UUID
    preference_order: int = Field(..., ge=1) # 志望順位は1以上

class DesiredSchoolCreate(DesiredSchoolBase):
    desired_departments: List[DesiredDepartmentCreate] = []

class DesiredSchoolUpdate(BaseModel):
    preference_order: Optional[int] = Field(None, ge=1)
    # 学部の追加/削除/更新は別途エンドポイントを用意するか、
    # このスキーマでリスト全体を置き換える方式にするか検討
    # desired_departments: Optional[List[DesiredDepartmentCreate]] = None

class DesiredSchoolResponse(DesiredSchoolBase, TimestampMixin):
    id: UUID
    user_id: UUID
    desired_departments: List[DesiredDepartmentResponse] = []
    # TODO: Populate related university data if needed
    # university: Optional[UniversityResponse] = None

    model_config = {
        "from_attributes": True,
    }

# List response
class DesiredSchoolListResponse(BaseModel):
    total: int
    desired_schools: List[DesiredSchoolResponse] 