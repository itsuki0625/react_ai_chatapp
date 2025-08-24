from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.teacher_student import TeacherStudentAssignment
from app.crud.school_tenant import teacher_student
from app.schemas.school_tenant import (
    AssignedStudentResponse,
    StudentDetailResponse, 
    PaginatedResponse,
    APIResponse,
    TeacherStudentAssignmentResponse
)
from app.schemas.chat import ChatSessionResponse
from app.schemas.personal_statement import PersonalStatementResponse
from app.schemas.desired_school import DesiredSchoolResponse
from app.core.permissions import require_permissions


router = APIRouter()


@router.get("/students", response_model=PaginatedResponse)
@require_permissions(["teacher_view_assigned_students"])
async def get_assigned_students(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(20, ge=1, le=100, description="ページサイズ"),
    search: Optional[str] = Query(None, description="生徒名で検索")
) -> PaginatedResponse:
    """
    担当生徒一覧を取得
    
    教員が担当している生徒の一覧を取得します。
    学習進捗情報も含めて返します。
    """
    try:
        skip = (page - 1) * page_size
        
        # 担当生徒を取得
        students = teacher_student.get_assigned_students(
            db,
            teacher_id=current_user.id,
            school_id=current_user.school_id,
            skip=skip,
            limit=page_size
        )
        
        # 検索フィルタリング
        if search:
            students = [s for s in students if search.lower() in s.full_name.lower()]
        
        # レスポンス用データ変換
        student_responses = []
        for student in students:
            # 担当関係情報取得
            assignment = db.query(TeacherStudentAssignment).filter(
                TeacherStudentAssignment.teacher_id == current_user.id,
                TeacherStudentAssignment.student_id == student.id,
                TeacherStudentAssignment.is_active == True
            ).first()
            
            if not assignment:
                continue
            
            # 学習進捗情報取得
            recent_chat_sessions = teacher_student.get_student_chat_sessions(
                db, student_id=student.id, skip=0, limit=5
            )
            
            recent_statements = teacher_student.get_student_statements(
                db, student_id=student.id, skip=0, limit=3
            )
            
            desired_schools = teacher_student.get_student_desired_schools(
                db, student_id=student.id, skip=0, limit=10
            )
            
            student_response = AssignedStudentResponse(
                student=student,
                assignment=assignment,
                recent_chat_sessions_count=len(recent_chat_sessions),
                recent_statements_count=len(recent_statements), 
                total_desired_schools=len(desired_schools),
                last_activity_at=student.last_login_at
            )
            
            student_responses.append(student_response)
        
        # 総数取得（簡易版）
        total_count = len(student_responses)
        total_pages = (total_count + page_size - 1) // page_size
        
        return PaginatedResponse(
            items=student_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"担当生徒の取得に失敗しました: {str(e)}"
        )


@router.get("/students/{student_id}", response_model=StudentDetailResponse)
@require_permissions(["teacher_view_assigned_students"])
async def get_student_detail(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    student_id: UUID
) -> StudentDetailResponse:
    """
    生徒の詳細情報を取得
    
    担当生徒の詳細な学習状況を取得します。
    チャット履歴、志望理由書、志望校情報を含みます。
    """
    try:
        # アクセス権限チェック
        if not teacher_student.can_teacher_access_student(
            db, teacher_id=current_user.id, student_id=student_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="この生徒の情報にアクセスする権限がありません"
            )
        
        # 生徒情報取得
        student = db.query(User).filter(User.id == student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定された生徒が見つかりません"
            )
        
        # 担当関係取得
        assignments = db.query(TeacherStudentAssignment).filter(
            TeacherStudentAssignment.student_id == student_id,
            TeacherStudentAssignment.is_active == True
        ).all()
        
        # 学習データ取得
        chat_sessions = teacher_student.get_student_chat_sessions(
            db, student_id=student_id, skip=0, limit=20
        )
        
        statements = teacher_student.get_student_statements(
            db, student_id=student_id, skip=0, limit=10
        )
        
        desired_schools = teacher_student.get_student_desired_schools(
            db, student_id=student_id, skip=0, limit=20
        )
        
        return StudentDetailResponse(
            student=student,
            assignments=assignments,
            chat_sessions=chat_sessions,
            statements=statements,
            desired_schools=desired_schools,
            total_chat_sessions=len(chat_sessions),
            total_statements=len(statements),
            total_desired_schools=len(desired_schools),
            last_login_at=student.last_login_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生徒詳細情報の取得に失敗しました: {str(e)}"
        )


@router.get("/students/{student_id}/chat-sessions", response_model=List[ChatSessionResponse])
@require_permissions(["teacher_view_student_chat"])
async def get_student_chat_sessions(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    student_id: UUID,
    limit: int = Query(10, ge=1, le=50, description="取得件数"),
    session_type: Optional[str] = Query(None, description="セッションタイプでフィルタ")
) -> List[ChatSessionResponse]:
    """
    生徒のチャットセッション一覧を取得
    
    担当生徒のチャット履歴を取得します。
    """
    try:
        # アクセス権限チェック
        if not teacher_student.can_teacher_access_student(
            db, teacher_id=current_user.id, student_id=student_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="この生徒のチャット情報にアクセスする権限がありません"
            )
        
        # チャットセッション取得
        from app.models.enums import SessionType
        session_type_enum = None
        if session_type:
            try:
                session_type_enum = SessionType(session_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="無効なセッションタイプです"
                )
        
        chat_sessions = teacher_student.get_student_chat_sessions(
            db, 
            student_id=student_id, 
            session_type=session_type_enum,
            skip=0, 
            limit=limit
        )
        
        return chat_sessions
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"チャットセッションの取得に失敗しました: {str(e)}"
        )


@router.get("/students/{student_id}/statements", response_model=List[PersonalStatementResponse])
@require_permissions(["teacher_view_student_statements"])
async def get_student_statements(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    student_id: UUID,
    limit: int = Query(10, ge=1, le=20, description="取得件数")
) -> List[PersonalStatementResponse]:
    """
    生徒の志望理由書一覧を取得
    
    担当生徒の志望理由書リストを取得します。
    """
    try:
        # アクセス権限チェック
        if not teacher_student.can_teacher_access_student(
            db, teacher_id=current_user.id, student_id=student_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="この生徒の志望理由書にアクセスする権限がありません"
            )
        
        # 志望理由書取得
        statements = teacher_student.get_student_statements(
            db, student_id=student_id, skip=0, limit=limit
        )
        
        return statements
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"志望理由書の取得に失敗しました: {str(e)}"
        )


@router.get("/students/{student_id}/desired-schools", response_model=List[DesiredSchoolResponse])
@require_permissions(["teacher_view_student_schools"])
async def get_student_desired_schools(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    student_id: UUID,
    limit: int = Query(20, ge=1, le=50, description="取得件数")
) -> List[DesiredSchoolResponse]:
    """
    生徒の志望校一覧を取得
    
    担当生徒の志望校情報を取得します。
    """
    try:
        # アクセス権限チェック
        if not teacher_student.can_teacher_access_student(
            db, teacher_id=current_user.id, student_id=student_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="この生徒の志望校情報にアクセスする権限がありません"
            )
        
        # 志望校取得
        desired_schools = teacher_student.get_student_desired_schools(
            db, student_id=student_id, skip=0, limit=limit
        )
        
        return desired_schools
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"志望校情報の取得に失敗しました: {str(e)}"
        )


@router.get("/assignments", response_model=List[TeacherStudentAssignmentResponse])
@require_permissions(["teacher_view_assigned_students"])
async def get_my_assignments(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100, description="取得件数")
) -> List[TeacherStudentAssignmentResponse]:
    """
    自分の担当関係一覧を取得
    
    現在の担当生徒の関係情報を取得します。
    """
    try:
        assignments = db.query(TeacherStudentAssignment).filter(
            TeacherStudentAssignment.teacher_id == current_user.id,
            TeacherStudentAssignment.is_active == True
        ).limit(limit).all()
        
        return assignments
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"担当関係の取得に失敗しました: {str(e)}"
        )
