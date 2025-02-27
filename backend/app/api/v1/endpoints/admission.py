from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.admission import AdmissionMethod
from app.schemas.admission import AdmissionMethodResponse

router = APIRouter()

@router.get("/", response_model=List[AdmissionMethodResponse])
async def get_admission_methods(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """入試方式一覧を取得"""
    methods = db.query(AdmissionMethod).filter(
        AdmissionMethod.is_active == True
    ).all()
    
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