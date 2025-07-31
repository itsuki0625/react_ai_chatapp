import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.api.deps import get_current_user, get_async_db, require_permission
from app.models.user import User
# from app.models.university import University, Department # CRUDを使うので直接参照は不要に
from app.schemas.university import UniversityResponse, DepartmentResponse

# --- 追加: crud.university をインポート ---
from app.crud import university as crud_university
# ---------------------------------------

router = APIRouter()

@router.get("/", response_model=List[UniversityResponse])
async def get_universities(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user) # 認証は維持
):
    """大学一覧を取得 (CRUD関数を使用)"""
    universities = await crud_university.get_universities(db=db, limit=1000)

    # レスポンスの構築
    response_data = []
    for univ in universities:
        if not univ.is_active:
            continue

        departments_response = []
        for dept in univ.departments:
             if not dept.is_active:
                 continue
             # --- DepartmentResponseに必要な情報をdeptオブジェクトから渡す ---
             departments_response.append(
                 DepartmentResponse(
                     id=dept.id,
                     name=dept.name,
                     department_code=dept.department_code,  # 必須フィールドを追加
                     university_id=univ.id,
                     is_active=dept.is_active,  # BaseModelの必須フィールド
                     created_at=dept.created_at,
                     updated_at=dept.updated_at
                 )
             )
             # --------------------------------------------------------------

        response_data.append(
            UniversityResponse(
                id=univ.id,
                name=univ.name,
                university_code=univ.university_code,  # 必須フィールドを追加
                is_active=univ.is_active,  # 必須フィールドを追加
                departments=departments_response,  # 学部リストを追加
                created_at=univ.created_at,
                updated_at=univ.updated_at
            )
        )
    return response_data 