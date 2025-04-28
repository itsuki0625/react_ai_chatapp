from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.api.deps import get_current_user, get_async_db
from app.models.user import User
from app.models.admission import AdmissionMethod
from app.schemas.admission import AdmissionMethodResponse

router = APIRouter()

@router.get("/", response_model=List[AdmissionMethodResponse])
async def get_admission_methods(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """入試方式一覧を取得"""
    result = await db.execute(
        select(AdmissionMethod).where(AdmissionMethod.is_active == True)
    )
    methods = result.scalars().all()
    
    # デバッグ用のログ
    print("Fetched admission methods:", methods)
    
    response_data = [
        AdmissionMethodResponse(
            id=method.id,
            name=method.name
        )
        for method in methods
    ]
    
    # デバッグ用のログ
    print("Response data:", response_data)
    
    return response_data 