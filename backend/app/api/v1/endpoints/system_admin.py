from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, desc
from uuid import UUID
from datetime import datetime, timedelta

from app.api.deps import get_db, get_current_user
from app.models.user import User, Role, UserRole, UserLoginInfo
from app.models.school import School
from app.models.teacher_student import TeacherStudentAssignment, SchoolSettings
from app.schemas.school_tenant import (
    SchoolStatistics,
    SchoolSettingsResponse,
    APIResponse
)
from app.schemas.user import UserResponse
from app.core.permissions import require_permissions


router = APIRouter()


@router.get("/schools", response_model=List[Dict[str, Any]])
@require_permissions(["admin_access"])
async def get_all_schools(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None, description="学校名で検索"),
    active_only: bool = Query(True, description="アクティブな学校のみ")
) -> List[Dict[str, Any]]:
    """
    全学校一覧を取得（システム管理者用）
    
    サービス運営者が全ての学校を管理するための一覧取得
    """
    try:
        print(f"[DEBUG] システム管理者API: 学校一覧取得開始 (skip={skip}, limit={limit}, search={search}, active_only={active_only})")
        
        query = db.query(School).options(
            joinedload(School.details),
            joinedload(School.settings)
        )
        
        # データベース内の学校総数を確認
        total_schools = db.query(School).count()
        print(f"[DEBUG] データベース内の学校総数: {total_schools}")
        
        if active_only:
            query = query.filter(School.is_active == True)
        
        if search:
            query = query.filter(School.name.ilike(f"%{search}%"))
        
        schools = query.offset(skip).limit(limit).all()
        print(f"[DEBUG] クエリ実行結果: {len(schools)}件の学校を取得")
        
        result = []
        for school in schools:
            # 各学校の統計情報を取得
            stats = get_school_statistics_data(db, school.id)
            
            result.append({
                "id": str(school.id),
                "name": school.name,
                "school_code": school.school_code,
                "is_active": school.is_active,
                "created_at": school.created_at.isoformat() if school.created_at else None,
                "updated_at": school.updated_at.isoformat() if school.updated_at else None,
                
                # 基本情報
                "details": {
                    "address": school.details.address if school.details else None,
                    "prefecture": school.details.prefecture if school.details else None,
                    "city": school.details.city if school.details else None,
                    "principal_name": school.details.principal_name if school.details else None,
                } if school.details else None,
                
                # 統計情報
                "statistics": stats,
                
                # 設定情報
                "settings": {
                    "allow_student_chat": school.settings.allow_student_chat if school.settings else True,
                    "enable_analytics": school.settings.enable_analytics if school.settings else True,
                } if school.settings else None
                         })
        
        print(f"[DEBUG] API応答: {len(result)}件の学校データを返します")
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"学校一覧の取得に失敗しました: {str(e)}"
        )


@router.get("/schools/{school_id}", response_model=Dict[str, Any])
@require_permissions(["admin_access"])
async def get_school_detail(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    school_id: UUID
) -> Dict[str, Any]:
    """
    学校詳細情報を取得（システム管理者用）
    """
    try:
        school = db.query(School).options(
            joinedload(School.details),
            joinedload(School.settings)
        ).filter(School.id == school_id).first()
        
        if not school:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定された学校が見つかりません"
            )
        
        # 詳細統計情報を取得
        stats = get_school_detailed_statistics(db, school_id)
        
        # 学校管理者一覧を取得
        school_admins = db.query(User).options(
            joinedload(User.login_info)
        ).join(UserRole).join(Role).filter(
            User.school_id == school_id,
            Role.name == "学校管理者"
        ).all()
        
        # 最近のアクティビティを取得（簡易版）
        recent_activities = get_school_recent_activities(db, school_id, limit=10)
        
        return {
            "id": str(school.id),
            "name": school.name,
            "school_code": school.school_code,
            "is_active": school.is_active,
            "created_at": school.created_at.isoformat() if school.created_at else None,
            "updated_at": school.updated_at.isoformat() if school.updated_at else None,
            
            # 詳細情報
            "details": {
                "address": school.details.address if school.details else None,
                "prefecture": school.details.prefecture if school.details else None,
                "city": school.details.city if school.details else None,
                "zip_code": school.details.zip_code if school.details else None,
                "principal_name": school.details.principal_name if school.details else None,
                "website_url": school.details.website_url if school.details else None,
            } if school.details else None,
            
            # 統計情報
            "statistics": stats,
            
            # 学校管理者
            "school_admins": [
                {
                    "id": str(admin.id),
                    "full_name": admin.full_name,
                    "email": admin.email,
                    "is_active": admin.is_active,
                    "last_login_at": admin.login_info.last_login_at.isoformat() if admin.login_info and admin.login_info.last_login_at else None
                }
                for admin in school_admins
            ],
            
            # 最近のアクティビティ
            "recent_activities": recent_activities,
            
            # 設定
            "settings": {
                "allow_student_chat": school.settings.allow_student_chat if school.settings else True,
                "require_statement_approval": school.settings.require_statement_approval if school.settings else True,
                "enable_analytics": school.settings.enable_analytics if school.settings else True,
                "enable_teacher_student_assignment": school.settings.enable_teacher_student_assignment if school.settings else True,
                "primary_color": school.settings.primary_color if school.settings else "#3B82F6",
                "email_notifications_enabled": school.settings.email_notifications_enabled if school.settings else True,
            } if school.settings else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"学校詳細情報の取得に失敗しました: {str(e)}"
        )


@router.get("/schools/{school_id}/users", response_model=List[UserResponse])
@require_permissions(["admin_access"])
async def get_school_users_admin(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    school_id: UUID,
    role: Optional[str] = Query(None, description="ロール名でフィルタ"),
    limit: int = Query(50, ge=1, le=200)
) -> List[UserResponse]:
    """
    指定学校のユーザー一覧を取得（システム管理者用）
    """
    try:
        query = db.query(User).filter(User.school_id == school_id)
        
        if role:
            query = query.join(UserRole).join(Role).filter(Role.name == role)
        
        users = query.limit(limit).all()
        return users
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"学校ユーザー一覧の取得に失敗しました: {str(e)}"
        )


@router.get("/analytics/overview", response_model=Dict[str, Any])
@require_permissions(["admin_access"])
async def get_system_analytics_overview(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    システム全体の統計概要を取得（システム管理者用）
    """
    try:
        print(f"[DEBUG] システム統計API: 概要取得開始")
        
        # 全学校数
        total_schools = db.query(School).count()
        active_schools = db.query(School).filter(School.is_active == True).count()
        print(f"[DEBUG] 学校統計: 総数={total_schools}, 有効={active_schools}")
        
        # 全ユーザー数（ロール別）
        user_stats = db.query(
            Role.name,
            func.count(User.id).label('count')
        ).select_from(Role).join(
            UserRole, Role.id == UserRole.role_id
        ).join(
            User, UserRole.user_id == User.id
        ).group_by(Role.name).all()
        
        user_counts = {stat.name: stat.count for stat in user_stats}
        
        # 今月のアクティビティ統計
        month_ago = datetime.now() - timedelta(days=30)
        active_users_month = db.query(User).join(
            UserLoginInfo, User.id == UserLoginInfo.user_id
        ).filter(
            UserLoginInfo.last_login_at >= month_ago
        ).count()
        
        # 担当関係統計
        total_assignments = db.query(TeacherStudentAssignment).count()
        active_assignments = db.query(TeacherStudentAssignment).filter(
            TeacherStudentAssignment.is_active == True
        ).count()
        
        return {
            "schools": {
                "total": total_schools,
                "active": active_schools,
                "inactive": total_schools - active_schools
            },
            "users": {
                "total": sum(user_counts.values()),
                "by_role": user_counts,
                "active_this_month": active_users_month
            },
            "assignments": {
                "total": total_assignments,
                "active": active_assignments,
                "inactive": total_assignments - active_assignments
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"システム統計の取得に失敗しました: {str(e)}"
        )


@router.put("/schools/{school_id}/status", response_model=APIResponse)
@require_permissions(["admin_access"])
async def update_school_status(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    school_id: UUID,
    is_active: bool = Body(..., description="学校の有効/無効状態")
) -> APIResponse:
    """
    学校の有効/無効状態を変更（システム管理者用）
    """
    try:
        school = db.query(School).filter(School.id == school_id).first()
        
        if not school:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定された学校が見つかりません"
            )
        
        school.is_active = is_active
        school.updated_at = datetime.now()
        
        db.commit()
        
        return APIResponse(
            success=True,
            message=f"学校「{school.name}」の状態を{'有効' if is_active else '無効'}に変更しました"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"学校状態の更新に失敗しました: {str(e)}"
        )


# ヘルパー関数
def get_school_statistics_data(db: Session, school_id: UUID) -> Dict[str, Any]:
    """学校の統計データを取得（簡易版）"""
    try:
        # ユーザー数統計
        user_counts = db.query(
            Role.name,
            func.count(User.id).label('count')
        ).select_from(Role).join(
            UserRole, Role.id == UserRole.role_id
        ).join(
            User, UserRole.user_id == User.id
        ).filter(
            User.school_id == school_id
        ).group_by(Role.name).all()
        
        user_stats = {stat.name: stat.count for stat in user_counts}
        
        # 担当関係数
        total_assignments = db.query(TeacherStudentAssignment).filter(
            TeacherStudentAssignment.school_id == school_id
        ).count()
        
        active_assignments = db.query(TeacherStudentAssignment).filter(
            and_(
                TeacherStudentAssignment.school_id == school_id,
                TeacherStudentAssignment.is_active == True
            )
        ).count()
        
        return {
            "users": user_stats,
            "total_users": sum(user_stats.values()),
            "assignments": {
                "total": total_assignments,
                "active": active_assignments
            }
        }
        
    except Exception:
        return {
            "users": {},
            "total_users": 0,
            "assignments": {"total": 0, "active": 0}
        }


def get_school_detailed_statistics(db: Session, school_id: UUID) -> Dict[str, Any]:
    """学校の詳細統計データを取得"""
    basic_stats = get_school_statistics_data(db, school_id)
    
    # 追加の統計情報
    month_ago = datetime.now() - timedelta(days=30)
    active_users_month = db.query(User).join(
        UserLoginInfo, User.id == UserLoginInfo.user_id
    ).filter(
        and_(
            User.school_id == school_id,
            UserLoginInfo.last_login_at >= month_ago
        )
    ).count()
    
    return {
        **basic_stats,
        "active_users_this_month": active_users_month,
        "user_activity_rate": (active_users_month / max(basic_stats["total_users"], 1)) * 100
    }


def get_school_recent_activities(db: Session, school_id: UUID, limit: int = 10) -> List[Dict[str, Any]]:
    """学校の最近のアクティビティを取得（簡易版）"""
    try:
        # 最近作成された担当関係
        recent_assignments = db.query(TeacherStudentAssignment).filter(
            TeacherStudentAssignment.school_id == school_id
        ).order_by(desc(TeacherStudentAssignment.created_at)).limit(limit//2).all()
        
        # 最近ログインしたユーザー
        recent_logins = db.query(User).options(
            joinedload(User.login_info)
        ).join(
            UserLoginInfo, User.id == UserLoginInfo.user_id
        ).filter(
            User.school_id == school_id,
            UserLoginInfo.last_login_at.isnot(None)
        ).order_by(desc(UserLoginInfo.last_login_at)).limit(limit//2).all()
        
        activities = []
        
        for assignment in recent_assignments:
            activities.append({
                "type": "assignment_created",
                "description": "新しい担当関係が作成されました",
                "timestamp": assignment.created_at.isoformat() if assignment.created_at else None,
                "details": {
                    "assignment_id": str(assignment.id),
                    "assignment_type": assignment.assignment_type.value if assignment.assignment_type else None
                }
            })
        
        for user in recent_logins:
            activities.append({
                "type": "user_login",
                "description": f"{user.full_name}がログインしました",
                "timestamp": user.login_info.last_login_at.isoformat() if user.login_info and user.login_info.last_login_at else None,
                "details": {
                    "user_id": str(user.id),
                    "user_name": user.full_name
                }
            })
        
        # 時刻順でソート
        activities.sort(key=lambda x: x["timestamp"] or "", reverse=True)
        
        return activities[:limit]
        
    except Exception:
        return []
