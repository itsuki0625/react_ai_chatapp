import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.api.deps import get_current_user, get_async_db, require_permission
from app.models.user import User
from app.models.university import University, Department
from app.schemas.university import UniversityResponse, DepartmentResponse

router = APIRouter()

@router.get("/", response_model=List[UniversityResponse])
async def get_universities(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """大学一覧を取得"""
    result = await db.execute(
        select(University).where(University.is_active == True)
    )
    universities = result.scalars().all()
    
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