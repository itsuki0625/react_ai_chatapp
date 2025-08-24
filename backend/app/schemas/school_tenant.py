from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.enums import AssignmentType
from app.schemas.user import UserResponse
from app.schemas.chat import ChatSessionResponse
from app.schemas.personal_statement import PersonalStatementResponse
from app.schemas.desired_school import DesiredSchoolResponse


# ベーススキーマ
class SchoolTenantBase(BaseModel):
    pass


# 学校統計情報
class SchoolUserStats(BaseModel):
    total_students: int = Field(..., description="生徒総数")
    total_teachers: int = Field(..., description="先生総数")
    total_school_admins: int = Field(..., description="学校管理者総数")
    active_students: int = Field(..., description="アクティブ生徒数（過去30日）")
    active_teachers: int = Field(..., description="アクティブ先生数（過去30日）")


class SchoolActivityStats(BaseModel):
    total_chat_sessions: int = Field(..., description="チャットセッション総数")
    total_statements: int = Field(..., description="志望理由書総数")
    total_assignments: int = Field(..., description="担当関係総数")


class SchoolStatistics(BaseModel):
    user_stats: SchoolUserStats
    activity_stats: SchoolActivityStats


# 先生・生徒の担当関係
class TeacherStudentAssignmentBase(BaseModel):
    teacher_id: UUID
    student_id: UUID
    school_id: UUID
    assignment_type: AssignmentType = AssignmentType.PRIMARY
    subject: Optional[str] = None
    notes: Optional[str] = None


class TeacherStudentAssignmentCreate(TeacherStudentAssignmentBase):
    pass


class TeacherStudentAssignmentUpdate(BaseModel):
    assignment_type: Optional[AssignmentType] = None
    subject: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class TeacherStudentAssignmentResponse(TeacherStudentAssignmentBase):
    id: UUID
    is_active: bool
    assigned_at: datetime
    unassigned_at: Optional[datetime] = None
    assigned_by: UUID
    created_at: datetime
    updated_at: datetime
    
    # リレーション
    teacher: Optional[UserResponse] = None
    student: Optional[UserResponse] = None

    class Config:
        from_attributes = True


# 学校設定
class SchoolSettingsBase(BaseModel):
    allow_student_chat: bool = True
    require_statement_approval: bool = True
    enable_analytics: bool = True
    enable_teacher_student_assignment: bool = True
    primary_color: str = "#3B82F6"
    secondary_color: str = "#10B981"
    accent_color: str = "#F59E0B"
    school_logo_url: Optional[str] = None
    email_notifications_enabled: bool = True
    push_notifications_enabled: bool = True
    digest_frequency: str = "weekly"
    custom_settings: Optional[str] = None


class SchoolSettingsUpdate(SchoolSettingsBase):
    allow_student_chat: Optional[bool] = None
    require_statement_approval: Optional[bool] = None
    enable_analytics: Optional[bool] = None
    enable_teacher_student_assignment: Optional[bool] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    school_logo_url: Optional[str] = None
    email_notifications_enabled: Optional[bool] = None
    push_notifications_enabled: Optional[bool] = None
    digest_frequency: Optional[str] = None
    custom_settings: Optional[str] = None


class SchoolSettingsResponse(SchoolSettingsBase):
    id: UUID
    school_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 学校ユーザー管理
class SchoolUserListResponse(BaseModel):
    users: List[UserResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class SchoolUserFilterParams(BaseModel):
    role_name: Optional[str] = Field(None, description="ロール名でフィルタリング")
    search_query: Optional[str] = Field(None, description="検索クエリ（名前）")
    page: int = Field(1, ge=1, description="ページ番号")
    page_size: int = Field(20, ge=1, le=100, description="ページサイズ")


# 先生・生徒管理
class AssignedStudentResponse(BaseModel):
    student: UserResponse
    assignment: TeacherStudentAssignmentResponse
    
    # 学習進捗情報
    recent_chat_sessions_count: int = 0
    recent_statements_count: int = 0
    total_desired_schools: int = 0
    last_activity_at: Optional[datetime] = None


class StudentDetailResponse(BaseModel):
    student: UserResponse
    assignments: List[TeacherStudentAssignmentResponse]
    
    # 詳細情報
    chat_sessions: List[ChatSessionResponse]
    statements: List[PersonalStatementResponse]
    desired_schools: List[DesiredSchoolResponse]
    
    # 統計情報
    total_chat_sessions: int
    total_statements: int
    total_desired_schools: int
    last_login_at: Optional[datetime] = None


# API レスポンス
class APIResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None


class PaginatedResponse(BaseModel):
    items: List[Any]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


# エラーレスポンス
class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# 学校管理者ダッシュボード用
class SchoolDashboardData(BaseModel):
    school_info: Dict[str, Any]
    statistics: SchoolStatistics
    recent_activities: List[Dict[str, Any]]
    settings: SchoolSettingsResponse


# バルク操作
class BulkAssignmentCreate(BaseModel):
    teacher_id: UUID
    student_ids: List[UUID]
    assignment_type: AssignmentType = AssignmentType.PRIMARY
    subject: Optional[str] = None
    notes: Optional[str] = None


class BulkAssignmentResponse(BaseModel):
    success_count: int
    failed_count: int
    created_assignments: List[TeacherStudentAssignmentResponse]
    errors: List[Dict[str, Any]]