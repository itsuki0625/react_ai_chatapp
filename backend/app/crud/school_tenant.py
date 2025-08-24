from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, desc
from uuid import UUID
from datetime import datetime, timedelta

from app.models.user import User, Role, UserRole
from app.models.school import School
from app.models.teacher_student import TeacherStudentAssignment, SchoolSettings, SchoolAdminSettings
from app.models.chat import ChatSession
from app.models.personal_statement import PersonalStatement
from app.models.desired_school import DesiredSchool
from app.models.enums import AssignmentType, SessionType
from app.crud.base import CRUDBase


class CRUDSchoolTenant(CRUDBase[School, None, None]):
    """学校テナント管理用CRUD操作"""
    
    def get_school_users(
        self,
        db: Session,
        *,
        school_id: UUID,
        role_name: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        search_query: Optional[str] = None
    ) -> List[User]:
        """学校内のユーザー一覧を取得"""
        query = db.query(User).filter(User.school_id == school_id)
        
        # ロールでフィルタリング
        if role_name:
            query = query.join(UserRole).join(Role).filter(Role.name == role_name)
        
        # 検索クエリでフィルタリング
        if search_query:
            query = query.filter(User.full_name.contains(search_query))
        
        return query.offset(skip).limit(limit).all()
    
    def get_school_user_count(
        self,
        db: Session,
        *,
        school_id: UUID,
        role_name: Optional[str] = None
    ) -> int:
        """学校内のユーザー数を取得"""
        query = db.query(func.count(User.id)).filter(User.school_id == school_id)
        
        if role_name:
            query = query.join(UserRole).join(Role).filter(Role.name == role_name)
        
        return query.scalar()
    
    def get_school_statistics(self, db: Session, *, school_id: UUID) -> dict:
        """学校の統計情報を取得"""
        # ユーザー統計
        total_students = self.get_school_user_count(db, school_id=school_id, role_name="フリー") + \
                        self.get_school_user_count(db, school_id=school_id, role_name="スタンダード") + \
                        self.get_school_user_count(db, school_id=school_id, role_name="プレミアム")
        
        total_teachers = self.get_school_user_count(db, school_id=school_id, role_name="教員")
        total_school_admins = self.get_school_user_count(db, school_id=school_id, role_name="学校管理者")
        
        # アクティブユーザー数（過去30日にログインしたユーザー）
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_students = db.query(func.count(User.id)).filter(
            User.school_id == school_id,
            User.last_login_at >= thirty_days_ago
        ).join(UserRole).join(Role).filter(
            Role.name.in_(["フリー", "スタンダード", "プレミアム"])
        ).scalar() or 0
        
        active_teachers = db.query(func.count(User.id)).filter(
            User.school_id == school_id,
            User.last_login_at >= thirty_days_ago
        ).join(UserRole).join(Role).filter(Role.name == "教員").scalar() or 0
        
        # チャット統計
        total_chat_sessions = db.query(func.count(ChatSession.id)).join(User).filter(
            User.school_id == school_id
        ).scalar() or 0
        
        # 志望理由書統計
        total_statements = db.query(func.count(PersonalStatement.id)).join(User).filter(
            User.school_id == school_id
        ).scalar() or 0
        
        # 先生・生徒の担当関係統計
        total_assignments = db.query(func.count(TeacherStudentAssignment.id)).filter(
            TeacherStudentAssignment.school_id == school_id,
            TeacherStudentAssignment.is_active == True
        ).scalar() or 0
        
        return {
            "user_stats": {
                "total_students": total_students,
                "total_teachers": total_teachers,
                "total_school_admins": total_school_admins,
                "active_students": active_students,
                "active_teachers": active_teachers,
            },
            "activity_stats": {
                "total_chat_sessions": total_chat_sessions,
                "total_statements": total_statements,
                "total_assignments": total_assignments,
            }
        }
    
    def get_teacher_student_assignments(
        self,
        db: Session,
        *,
        school_id: UUID,
        teacher_id: Optional[UUID] = None,
        student_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TeacherStudentAssignment]:
        """先生・生徒の担当関係を取得"""
        query = db.query(TeacherStudentAssignment).filter(
            TeacherStudentAssignment.school_id == school_id,
            TeacherStudentAssignment.is_active == True
        ).options(
            joinedload(TeacherStudentAssignment.teacher),
            joinedload(TeacherStudentAssignment.student)
        )
        
        if teacher_id:
            query = query.filter(TeacherStudentAssignment.teacher_id == teacher_id)
        
        if student_id:
            query = query.filter(TeacherStudentAssignment.student_id == student_id)
        
        return query.offset(skip).limit(limit).all()
    
    def create_teacher_student_assignment(
        self,
        db: Session,
        *,
        teacher_id: UUID,
        student_id: UUID,
        school_id: UUID,
        assigned_by: UUID,
        assignment_type: AssignmentType = AssignmentType.PRIMARY,
        subject: Optional[str] = None,
        notes: Optional[str] = None
    ) -> TeacherStudentAssignment:
        """先生・生徒の担当関係を作成"""
        assignment = TeacherStudentAssignment(
            teacher_id=teacher_id,
            student_id=student_id,
            school_id=school_id,
            assignment_type=assignment_type,
            subject=subject,
            notes=notes,
            is_active=True,
            assigned_by=assigned_by,
            assigned_at=datetime.utcnow()
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment
    
    def remove_teacher_student_assignment(
        self,
        db: Session,
        *,
        assignment_id: UUID
    ) -> bool:
        """先生・生徒の担当関係を削除"""
        assignment = db.query(TeacherStudentAssignment).filter(
            TeacherStudentAssignment.id == assignment_id
        ).first()
        
        if assignment:
            assignment.is_active = False
            assignment.unassigned_at = datetime.utcnow()
            db.commit()
            return True
        return False
    
    def get_school_settings(self, db: Session, *, school_id: UUID) -> Optional[SchoolSettings]:
        """学校設定を取得"""
        return db.query(SchoolSettings).filter(
            SchoolSettings.school_id == school_id
        ).first()
    
    def update_school_settings(
        self,
        db: Session,
        *,
        school_id: UUID,
        settings_data: dict
    ) -> Optional[SchoolSettings]:
        """学校設定を更新"""
        settings = self.get_school_settings(db, school_id=school_id)
        if not settings:
            return None
        
        for field, value in settings_data.items():
            if hasattr(settings, field):
                setattr(settings, field, value)
        
        db.commit()
        db.refresh(settings)
        return settings


class CRUDTeacherStudent(CRUDBase[TeacherStudentAssignment, None, None]):
    """先生・生徒管理用CRUD操作"""
    
    def get_assigned_students(
        self,
        db: Session,
        *,
        teacher_id: UUID,
        school_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """先生の担当生徒一覧を取得"""
        query = db.query(User).join(TeacherStudentAssignment).filter(
            TeacherStudentAssignment.teacher_id == teacher_id,
            TeacherStudentAssignment.is_active == True
        )
        
        if school_id:
            query = query.filter(User.school_id == school_id)
        
        return query.offset(skip).limit(limit).all()
    
    def get_student_teachers(
        self,
        db: Session,
        *,
        student_id: UUID,
        school_id: Optional[UUID] = None
    ) -> List[User]:
        """生徒の担当先生一覧を取得"""
        query = db.query(User).join(TeacherStudentAssignment).filter(
            TeacherStudentAssignment.student_id == student_id,
            TeacherStudentAssignment.is_active == True
        )
        
        if school_id:
            query = query.filter(User.school_id == school_id)
        
        return query.all()
    
    def can_teacher_access_student(
        self,
        db: Session,
        *,
        teacher_id: UUID,
        student_id: UUID
    ) -> bool:
        """先生が生徒にアクセスできるかを確認"""
        assignment = db.query(TeacherStudentAssignment).filter(
            TeacherStudentAssignment.teacher_id == teacher_id,
            TeacherStudentAssignment.student_id == student_id,
            TeacherStudentAssignment.is_active == True
        ).first()
        
        return assignment is not None
    
    def get_student_chat_sessions(
        self,
        db: Session,
        *,
        student_id: UUID,
        session_type: Optional[SessionType] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ChatSession]:
        """生徒のチャットセッション一覧を取得"""
        query = db.query(ChatSession).filter(ChatSession.user_id == student_id)
        
        if session_type:
            query = query.filter(ChatSession.session_type == session_type)
        
        return query.order_by(desc(ChatSession.created_at)).offset(skip).limit(limit).all()
    
    def get_student_statements(
        self,
        db: Session,
        *,
        student_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[PersonalStatement]:
        """生徒の志望理由書一覧を取得"""
        return db.query(PersonalStatement).filter(
            PersonalStatement.user_id == student_id
        ).order_by(desc(PersonalStatement.created_at)).offset(skip).limit(limit).all()
    
    def get_student_desired_schools(
        self,
        db: Session,
        *,
        student_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[DesiredSchool]:
        """生徒の志望校一覧を取得"""
        return db.query(DesiredSchool).filter(
            DesiredSchool.user_id == student_id
        ).offset(skip).limit(limit).all()


class CRUDTeacherStudent(CRUDBase[TeacherStudentAssignment, None, None]):
    """先生・生徒担当関係管理用CRUD操作"""
    
    def get_assigned_students(
        self,
        db: Session,
        *,
        teacher_id: UUID,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """先生の担当生徒一覧を取得"""
        return db.query(User).join(TeacherStudentAssignment).filter(
            TeacherStudentAssignment.teacher_id == teacher_id,
            TeacherStudentAssignment.school_id == school_id,
            TeacherStudentAssignment.is_active == True
        ).offset(skip).limit(limit).all()
    
    def can_teacher_access_student(
        self, db: Session, *, teacher_id: UUID, student_id: UUID
    ) -> bool:
        """先生が生徒にアクセスできるかチェック"""
        assignment = db.query(TeacherStudentAssignment).filter(
            TeacherStudentAssignment.teacher_id == teacher_id,
            TeacherStudentAssignment.student_id == student_id,
            TeacherStudentAssignment.is_active == True
        ).first()
        return assignment is not None
    
    def get_student_chat_sessions(
        self, db: Session, *, student_id: UUID, session_type=None, skip: int = 0, limit: int = 100
    ):
        """生徒のチャットセッション取得（簡易版）"""
        # 実装は既存のChatSessionモデルに依存
        from app.models.chat import ChatSession
        query = db.query(ChatSession).filter(ChatSession.user_id == student_id)
        if session_type:
            query = query.filter(ChatSession.session_type == session_type)
        return query.offset(skip).limit(limit).all()
    
    def get_student_statements(
        self, db: Session, *, student_id: UUID, skip: int = 0, limit: int = 100
    ):
        """生徒の志望理由書取得（簡易版）"""
        from app.models.personal_statement import PersonalStatement
        return db.query(PersonalStatement).filter(
            PersonalStatement.user_id == student_id
        ).offset(skip).limit(limit).all()
    
    def get_student_desired_schools(
        self, db: Session, *, student_id: UUID, skip: int = 0, limit: int = 100
    ):
        """生徒の志望校取得（簡易版）"""
        return db.query(DesiredSchool).filter(
            DesiredSchool.user_id == student_id
        ).offset(skip).limit(limit).all()


school_tenant = CRUDSchoolTenant(School)
teacher_student = CRUDTeacherStudent(TeacherStudentAssignment)
