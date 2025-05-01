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
                     # ★ faculty_name, university_id, created_at, updated_at を追加
                     faculty_name=getattr(dept, 'faculty_name', '不明'), # faculty_nameが存在しない場合もあるためgetattrを使用
                     university_id=univ.id, # 大学のIDを渡す
                     created_at=dept.created_at,
                     updated_at=dept.updated_at,
                     # description は DepartmentBase に含まれる Optional なのでそのままでOK
                     description=getattr(dept.details, 'description', None) if dept.details else None # dept.details から取得
                 )
             )
             # --------------------------------------------------------------

        response_data.append(
            UniversityResponse(
                id=univ.id,
                name=univ.name,
                departments=departments_response,
                # UniversityResponse に必要な他のフィールドも渡す (prefecture など)
                prefecture=getattr(univ.details, 'prefecture', '不明') if univ.details else '不明',
                address=getattr(univ.details, 'address', None) if univ.details else None,
                # HttpUrl 型は str() で囲む必要がある場合があるので注意
                website_url=str(getattr(univ.details, 'website_url', None)) if univ.details and getattr(univ.details, 'website_url', None) else None,
                # UniversityBase に description があるので univ.details から取得？ または univ 自体？ スキーマに合わせて調整
                description=getattr(univ.details, 'description', None) if univ.details else getattr(univ, 'description', None),
                is_national=getattr(univ, 'is_national', False), # Universityモデルにis_nationalがあれば
                logo_url=str(getattr(univ, 'logo_url', None)) if getattr(univ, 'logo_url', None) else None, # Universityモデルにlogo_urlがあれば
                created_at=univ.created_at,
                updated_at=univ.updated_at
            )
        )
    return response_data 