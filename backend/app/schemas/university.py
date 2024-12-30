from pydantic import BaseModel
from typing import List
from uuid import UUID

class DepartmentResponse(BaseModel):
    id: UUID
    name: str

class UniversityResponse(BaseModel):
    id: UUID
    name: str
    departments: List[DepartmentResponse] 