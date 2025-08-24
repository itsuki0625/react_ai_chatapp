from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.teacher_student import TeacherStudentAssignment, SchoolSettings
from app.crud.school_tenant import school_tenant
from app.schemas.school_tenant import (
    SchoolStatistics,
    SchoolUserListResponse,
    SchoolUserFilterParams,
    TeacherStudentAssignmentResponse,
    TeacherStudentAssignmentCreate,
    SchoolSettingsResponse,
    SchoolSettingsUpdate,
    BulkAssignmentCreate,
    BulkAssignmentResponse,
    APIResponse,
    SchoolDashboardData
)
from app.schemas.user import UserResponse
from app.core.permissions import require_permissions


router = APIRouter()


@router.get("/dashboard", response_model=SchoolDashboardData)
@require_permissions(["school_admin_access"])
async def get_school_dashboard(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SchoolDashboardData:
    """
    学校管理者ダッシュボード情報を取得
    
    学校の統計情報、設定、最近の活動を取得します。
    """
    try:
        if not current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="学校に所属していないユーザーです"
            )
        
        # 統計情報取得
        statistics = school_tenant.get_school_statistics(
            db, school_id=current_user.school_id
        )
        
        # 学校設定取得
        settings = school_tenant.get_school_settings(
            db, school_id=current_user.school_id
        )
        
        # 最近の活動（簡易版）
        recent_activities = [
            {
                "id": "activity-1",
                "type": "user_login",
                "description": "新しいユーザーがログインしました",
                "timestamp": "2024-01-20T10:30:00Z",
                "user": "田中太郎"
            },
            {
                "id": "activity-2", 
                "type": "statement_created",
                "description": "志望理由書が作成されました",
                "timestamp": "2024-01-20T09:15:00Z",
                "user": "佐藤花子"
            }
        ]
        
        return SchoolDashboardData(
            school_info={
                "id": str(current_user.school_id),
                "name": current_user.school.name if current_user.school else "未設定",
                "total_users": statistics["user_stats"]["total_students"] + 
                              statistics["user_stats"]["total_teachers"] + 
                              statistics["user_stats"]["total_school_admins"]
            },
            statistics=SchoolStatistics(
                user_stats=statistics["user_stats"],
                activity_stats=statistics["activity_stats"]
            ),
            recent_activities=recent_activities,
            settings=settings
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ダッシュボード情報の取得に失敗しました: {str(e)}"
        )


@router.get("/statistics", response_model=SchoolStatistics)
@require_permissions(["school_view_analytics"])
async def get_school_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SchoolStatistics:
    """
    学校の統計情報を取得
    
    ユーザー数、活動状況などの統計データを取得します。
    """
    try:
        if not current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="学校に所属していないユーザーです"
            )
        
        statistics = school_tenant.get_school_statistics(
            db, school_id=current_user.school_id
        )
        
        return SchoolStatistics(
            user_stats=statistics["user_stats"],
            activity_stats=statistics["activity_stats"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"統計情報の取得に失敗しました: {str(e)}"
        )


@router.get("/users", response_model=SchoolUserListResponse)
@require_permissions(["school_manage_users"])
async def get_school_users(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    role_name: Optional[str] = Query(None, description="ロール名でフィルタリング"),
    search_query: Optional[str] = Query(None, description="名前で検索"),
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(20, ge=1, le=100, description="ページサイズ")
) -> SchoolUserListResponse:
    """
    学校内ユーザー一覧を取得
    
    学校に所属するユーザーの一覧を取得します。
    ロールや検索条件でフィルタリング可能です。
    """
    try:
        if not current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="学校に所属していないユーザーです"
            )
        
        skip = (page - 1) * page_size
        
        # ユーザー一覧取得
        users = school_tenant.get_school_users(
            db,
            school_id=current_user.school_id,
            role_name=role_name,
            skip=skip,
            limit=page_size,
            search_query=search_query
        )
        
        # 総数取得
        total_count = school_tenant.get_school_user_count(
            db,
            school_id=current_user.school_id,
            role_name=role_name
        )
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return SchoolUserListResponse(
            users=users,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ユーザー一覧の取得に失敗しました: {str(e)}"
        )


@router.get("/teachers", response_model=List[UserResponse])
@require_permissions(["school_view_all_teachers"])
async def get_school_teachers(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100, description="取得件数")
) -> List[UserResponse]:
    """
    学校内の教員一覧を取得
    """
    try:
        if not current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="学校に所属していないユーザーです"
            )
        
        teachers = school_tenant.get_school_users(
            db,
            school_id=current_user.school_id,
            role_name="教員",
            skip=0,
            limit=limit
        )
        
        return teachers
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"教員一覧の取得に失敗しました: {str(e)}"
        )


@router.get("/students", response_model=List[UserResponse])
@require_permissions(["school_view_all_students"])
async def get_school_students(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=200, description="取得件数")
) -> List[UserResponse]:
    """
    学校内の生徒一覧を取得
    """
    try:
        if not current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="学校に所属していないユーザーです"
            )
        
        # 生徒ロールのユーザーを取得（フリー、スタンダード、プレミアム）
        students = []
        for role in ["フリー", "スタンダード", "プレミアム"]:
            role_users = school_tenant.get_school_users(
                db,
                school_id=current_user.school_id,
                role_name=role,
                skip=0,
                limit=limit // 3
            )
            students.extend(role_users)
        
        return students[:limit]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生徒一覧の取得に失敗しました: {str(e)}"
        )


@router.get("/assignments", response_model=List[TeacherStudentAssignmentResponse])
@require_permissions(["school_manage_assignments"])
async def get_school_assignments(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    teacher_id: Optional[UUID] = Query(None, description="教員IDでフィルタ"),
    student_id: Optional[UUID] = Query(None, description="生徒IDでフィルタ"),
    limit: int = Query(50, ge=1, le=100, description="取得件数")
) -> List[TeacherStudentAssignmentResponse]:
    """
    学校内の担当関係一覧を取得
    """
    try:
        if not current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="学校に所属していないユーザーです"
            )
        
        assignments = school_tenant.get_teacher_student_assignments(
            db,
            school_id=current_user.school_id,
            teacher_id=teacher_id,
            student_id=student_id,
            skip=0,
            limit=limit
        )
        
        return assignments
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"担当関係一覧の取得に失敗しました: {str(e)}"
        )


@router.post("/assignments", response_model=TeacherStudentAssignmentResponse)
@require_permissions(["school_manage_assignments"])
async def create_teacher_student_assignment(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    assignment_data: TeacherStudentAssignmentCreate
) -> TeacherStudentAssignmentResponse:
    """
    新しい担当関係を作成
    """
    try:
        if not current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="学校に所属していないユーザーです"
            )
        
        assignment = school_tenant.create_teacher_student_assignment(
            db,
            teacher_id=assignment_data.teacher_id,
            student_id=assignment_data.student_id,
            school_id=current_user.school_id,
            assigned_by=current_user.id,
            assignment_type=assignment_data.assignment_type,
            subject=assignment_data.subject,
            notes=assignment_data.notes
        )
        
        return assignment
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"担当関係の作成に失敗しました: {str(e)}"
        )


@router.post("/assignments/bulk", response_model=BulkAssignmentResponse)
@require_permissions(["school_manage_assignments"])
async def create_bulk_assignments(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    bulk_data: BulkAssignmentCreate
) -> BulkAssignmentResponse:
    """
    複数の担当関係を一括作成
    """
    try:
        if not current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="学校に所属していないユーザーです"
            )
        
        created_assignments = []
        errors = []
        
        for student_id in bulk_data.student_ids:
            try:
                assignment = school_tenant.create_teacher_student_assignment(
                    db,
                    teacher_id=bulk_data.teacher_id,
                    student_id=student_id,
                    school_id=current_user.school_id,
                    assigned_by=current_user.id,
                    assignment_type=bulk_data.assignment_type,
                    subject=bulk_data.subject,
                    notes=bulk_data.notes
                )
                created_assignments.append(assignment)
            except Exception as e:
                errors.append({
                    "student_id": str(student_id),
                    "error": str(e)
                })
        
        return BulkAssignmentResponse(
            success_count=len(created_assignments),
            failed_count=len(errors),
            created_assignments=created_assignments,
            errors=errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"一括担当関係の作成に失敗しました: {str(e)}"
        )


@router.delete("/assignments/{assignment_id}", response_model=APIResponse)
@require_permissions(["school_manage_assignments"])
async def remove_teacher_student_assignment(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    assignment_id: UUID
) -> APIResponse:
    """
    担当関係を削除
    """
    try:
        success = school_tenant.remove_teacher_student_assignment(
            db, assignment_id=assignment_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定された担当関係が見つかりません"
            )
        
        return APIResponse(
            success=True,
            message="担当関係を削除しました"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"担当関係の削除に失敗しました: {str(e)}"
        )


@router.get("/settings", response_model=SchoolSettingsResponse)
@require_permissions(["school_manage_settings"])
async def get_school_settings(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SchoolSettingsResponse:
    """
    学校設定を取得
    """
    try:
        if not current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="学校に所属していないユーザーです"
            )
        
        settings = school_tenant.get_school_settings(
            db, school_id=current_user.school_id
        )
        
        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="学校設定が見つかりません"
            )
        
        return settings
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"学校設定の取得に失敗しました: {str(e)}"
        )


@router.put("/settings", response_model=SchoolSettingsResponse)
@require_permissions(["school_manage_settings"])
async def update_school_settings(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings_data: SchoolSettingsUpdate
) -> SchoolSettingsResponse:
    """
    学校設定を更新
    """
    try:
        if not current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="学校に所属していないユーザーです"
            )
        
        # 更新データを辞書に変換（Noneではない項目のみ）
        update_data = settings_data.dict(exclude_unset=True)
        
        settings = school_tenant.update_school_settings(
            db,
            school_id=current_user.school_id,
            settings_data=update_data
        )
        
        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="学校設定が見つかりません"
            )
        
        return settings
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"学校設定の更新に失敗しました: {str(e)}"
        )
