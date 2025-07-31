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
        # まず基本情報のクエリ実行をテスト
        print(f"Attempting to fetch desired schools for user: {current_user.id}")
        
        schools, total_count = await crud.desired_school.get_desired_schools_by_user_with_count(
            db=db, user_id=current_user.id, skip=skip, limit=limit
        )
        
        print(f"Successfully fetched {len(schools)} schools")
        
        # 手動でスキーマ互換のデータを作成
        safe_schools = []
        for school in schools:
            try:
                safe_school = {
                    "id": str(school.id),
                    "user_id": str(school.user_id),
                    "university_id": str(school.university_id),
                    "preference_order": school.preference_order,
                    "created_at": school.created_at.isoformat() if hasattr(school, 'created_at') and school.created_at else None,
                    "updated_at": school.updated_at.isoformat() if hasattr(school, 'updated_at') and school.updated_at else None,
                    "desired_departments": [],
                    "university": None
                }
                
                # Universityの情報を安全に追加
                if hasattr(school, 'university') and school.university:
                    safe_school["university"] = {
                        "id": str(school.university.id),
                        "name": school.university.name,
                        "university_code": school.university.university_code,
                        "is_active": getattr(school.university, 'is_active', True),
                        "created_at": school.university.created_at.isoformat() if hasattr(school.university, 'created_at') and school.university.created_at else None,
                        "updated_at": school.university.updated_at.isoformat() if hasattr(school.university, 'updated_at') and school.university.updated_at else None,
                    }
                
                # DesiredDepartmentsの情報を安全に追加  
                if hasattr(school, 'desired_departments') and school.desired_departments:
                    for dept in school.desired_departments:
                        safe_dept = {
                            "id": str(dept.id),
                            "desired_school_id": str(dept.desired_school_id),
                            "department_id": str(dept.department_id),
                            "admission_method_id": str(dept.admission_method_id),
                            "created_at": dept.created_at.isoformat() if hasattr(dept, 'created_at') and dept.created_at else None,
                            "updated_at": dept.updated_at.isoformat() if hasattr(dept, 'updated_at') and dept.updated_at else None,
                            "department": None,
                            "admission_method": None
                        }
                        
                        # Departmentの情報を安全に追加
                        if hasattr(dept, 'department') and dept.department:
                            safe_dept["department"] = {
                                "id": str(dept.department.id),
                                "name": dept.department.name,
                                "department_code": dept.department.department_code,
                                "university_id": str(dept.department.university_id),
                                "is_active": getattr(dept.department, 'is_active', True),
                                "created_at": dept.department.created_at.isoformat() if hasattr(dept.department, 'created_at') and dept.department.created_at else None,
                                "updated_at": dept.department.updated_at.isoformat() if hasattr(dept.department, 'updated_at') and dept.department.updated_at else None,
                            }
                        
                        # AdmissionMethodの情報を安全に追加
                        if hasattr(dept, 'admission_method') and dept.admission_method:
                            safe_dept["admission_method"] = {
                                "id": str(dept.admission_method.id),
                                "name": dept.admission_method.name,
                                "description": getattr(dept.admission_method, 'description', None),
                                "is_active": getattr(dept.admission_method, 'is_active', True),
                                "created_at": dept.admission_method.created_at.isoformat() if hasattr(dept.admission_method, 'created_at') and dept.admission_method.created_at else None,
                                "updated_at": dept.admission_method.updated_at.isoformat() if hasattr(dept.admission_method, 'updated_at') and dept.admission_method.updated_at else None,
                            }
                        
                        safe_school["desired_departments"].append(safe_dept)
                        
                safe_schools.append(safe_school)
                
            except Exception as school_error:
                print(f"Error processing individual school {school.id}: {school_error}")
                continue
        
        print(f"Successfully processed {len(safe_schools)} schools")
        return {
            "total": total_count,
            "desired_schools": safe_schools
        }
        
    except Exception as e:
        import traceback
        print(f"Error reading desired schools: {e}")
        print(f"Traceback: {traceback.format_exc()}")
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