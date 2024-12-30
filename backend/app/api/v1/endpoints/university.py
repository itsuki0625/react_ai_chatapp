from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.university import University, Department
from app.schemas.university import UniversityResponse, DepartmentResponse

router = APIRouter()

@router.get("/", response_model=List[UniversityResponse])
async def get_universities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """大学一覧を取得"""
    universities = db.query(University).filter(
        University.is_active == True
    ).all()
    
    return [
        UniversityResponse(
            id=univ.id,
            name=univ.name,
            departments=[
                DepartmentResponse(
                    id=dept.id,
                    name=dept.name
                )
                for dept in univ.departments
                if dept.is_active
            ]
        )
        for univ in universities
    ] 