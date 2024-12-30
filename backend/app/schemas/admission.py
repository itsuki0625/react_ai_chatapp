from pydantic import BaseModel
from uuid import UUID

class AdmissionMethodResponse(BaseModel):
    id: UUID
    name: str 