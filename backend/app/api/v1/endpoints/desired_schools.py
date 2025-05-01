from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any
from uuid import UUID

from app import crud, models
from app.crud import admission as crud_admission
from app.api import deps
from app.core.exceptions import NotFoundError, ConflictError, DatabaseError, ForbiddenError
from app.schemas.desired_school import DesiredSchoolResponse, DesiredSchoolCreate, DesiredSchoolUpdate, DesiredSchoolListResponse

router = APIRouter()

@router.post(
    "/",
    response_model=DesiredSchoolResponse,
    status_code=status.HTTP_201_CREATED,
    summary="志望校を登録",
    description="ログイン中のユーザーの新しい志望校と関連する学部/入試方式を登録します。",
)
async def create_desired_school(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    desired_school_in: DesiredSchoolCreate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """ユーザーの新しい志望校を作成します。"""
    try:
        university = await crud.university.get_university(db, university_id=desired_school_in.university_id)
        if not university:
            raise NotFoundError(f"大学ID {desired_school_in.university_id} が見つかりません")
            
        for dept_in in desired_school_in.desired_departments:
            department = await crud.university.get_department(db, department_id=dept_in.department_id)
            if not department:
                raise NotFoundError(f"学部ID {dept_in.department_id} が見つかりません")
            admission_method = await crud_admission.get_admission_method(db, method_id=dept_in.admission_method_id)
            if not admission_method:
                raise NotFoundError(f"入試方式ID {dept_in.admission_method_id} が見つかりません")
                
        created_school = await crud.desired_school.create_desired_school(
            db=db, user_id=current_user.id, obj_in=desired_school_in
        )
        return created_school
    except (NotFoundError, ConflictError, DatabaseError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        print(f"Error creating desired school: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="志望校の作成中にサーバーエラーが発生しました。"
        )

@router.get(
    "/me",
    response_model=DesiredSchoolListResponse,
    summary="自分の志望校リストを取得",
    description="ログイン中のユーザーが登録した志望校のリストを取得します。志望順位でソートされます。",
)
async def read_my_desired_schools(
    db: AsyncSession = Depends(deps.get_async_db),
    current_user: models.User = Depends(deps.get_current_user),
    skip: int = Query(0, ge=0, description="スキップする項目数"),
    limit: int = Query(100, ge=1, le=100, description="取得する最大項目数"),
) -> Any:
    """ログインユーザーの志望校リストを取得します。"""
    try:
        schools, total_count = await crud.desired_school.get_desired_schools_by_user_with_count(
            db=db, user_id=current_user.id, skip=skip, limit=limit
        )
        return DesiredSchoolListResponse(total=total_count, desired_schools=schools)
    except Exception as e:
        print(f"Error reading desired schools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="志望校リストの取得中にサーバーエラーが発生しました。"
        )

@router.get(
    "/{desired_school_id}",
    response_model=DesiredSchoolResponse,
    summary="特定の志望校情報を取得",
    description="指定されたIDの志望校情報を取得します。",
)
def read_desired_school(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    desired_school_id: UUID,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """特定の志望校情報を取得します。"""
    db_school = crud.desired_school.get_desired_school(db, desired_school_id=desired_school_id)
    if not db_school:
        raise NotFoundError("志望校が見つかりません")
        
    # 権限チェック: 自分の志望校か、または管理者か
    is_admin = any(role.role.name == '管理者' for role in current_user.user_roles)
    if db_school.user_id != current_user.id and not is_admin:
        raise ForbiddenError("この志望校情報にアクセスする権限がありません")
        
    return db_school

@router.patch(
    "/{desired_school_id}",
    response_model=DesiredSchoolResponse,
    summary="志望校情報を更新",
    description="指定されたIDの志望校情報（志望順位など）を更新します。",
)
def update_desired_school(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    desired_school_id: UUID,
    desired_school_in: DesiredSchoolUpdate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """志望校情報を更新します。"""
    db_school = crud.desired_school.get_desired_school(db, desired_school_id=desired_school_id)
    if not db_school:
        raise NotFoundError("志望校が見つかりません")
    
    if db_school.user_id != current_user.id:
        raise ForbiddenError("この志望校を更新する権限がありません")

    try:
        updated_school = crud.desired_school.update_desired_school(
            db=db, db_obj=db_school, obj_in=desired_school_in
        )
        return updated_school
    except (ConflictError, DatabaseError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        print(f"Error updating desired school: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="志望校の更新中にサーバーエラーが発生しました。"
        )

@router.delete(
    "/{desired_school_id}",
    response_model=DesiredSchoolResponse,
    status_code=status.HTTP_200_OK,
    summary="志望校を削除",
    description="指定されたIDの志望校情報を削除します。",
)
def delete_desired_school(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    desired_school_id: UUID,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """志望校情報を削除します。"""
    db_school = crud.desired_school.get_desired_school(db, desired_school_id=desired_school_id)
    if not db_school:
        raise NotFoundError("志望校が見つかりません")
        
    if db_school.user_id != current_user.id:
        raise ForbiddenError("この志望校を削除する権限がありません")

    try:
        deleted_school = crud.desired_school.delete_desired_school(db=db, desired_school_id=desired_school_id)
        return deleted_school
    except (NotFoundError, DatabaseError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        print(f"Error deleting desired school: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="志望校の削除中にサーバーエラーが発生しました。"
        ) 