from sqlalchemy.orm import Session
from app.models.user import User, Role
from app.models.chat import ChatSession, ChatMessage
from app.models.desired_school import DesiredSchool, DesiredDepartment
from app.models.personal_statement import PersonalStatement
from app.models.content import Content, ContentViewHistory
from app.models.university import University, Department
from app.models.enums import SessionType, SessionStatus, MessageType
from typing import Dict, List, Any, Optional
from uuid import UUID
from sqlalchemy import func, desc
from datetime import datetime, timedelta

def get_student_dashboard(db: Session, user_id: UUID) -> Dict[str, Any]:
    """学生向けダッシュボード情報を取得する"""
    # 基本情報
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "ユーザーが見つかりません"}
    
    # 総合情報を取得
    result = {
        "user": {
            "id": str(user.id),
            "name": user.full_name,
            "email": user.email,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
        },
        "chat_stats": get_chat_stats(db, user_id),
        "applications": get_user_applications_summary(db, user_id),
        "learning_progress": get_learning_progress(db, user_id),
        "upcoming_events": get_upcoming_events(db, user_id),
        "recent_contents": get_recent_contents(db, user_id),
        "recommendations": get_recommendations(db, user_id)
    }
    
    return result

def get_teacher_dashboard(db: Session, user_id: UUID) -> Dict[str, Any]:
    """教師向けダッシュボード情報を取得する"""
    # 教師情報
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "ユーザーが見つかりません"}
    
    # 担当生徒情報（仮の実装 - 実際のデータモデルに応じて適切に実装すること）
    # この例では、教師は自分が所属する学校の生徒をすべて担当すると仮定
    students = []
    if user.school_id:
        students = db.query(User).filter(
            User.school_id == user.school_id,
            User.id != user_id  # 自分自身を除外
        ).all()
    
    # 総合情報
    result = {
        "user": {
            "id": str(user.id),
            "name": user.full_name,
            "email": user.email,
        },
        "students_count": len(students),
        "students_summary": [{"id": str(s.id), "name": s.full_name} for s in students[:10]],  # 最初の10人だけ
        "feedback_requests": get_pending_feedback_requests(db, user_id),
        "recent_activities": get_recent_teacher_activities(db, user_id),
        "student_performance": get_student_performance_summary(db, user_id)
    }
    
    return result

def get_admin_dashboard(db: Session, user_id: UUID) -> Dict[str, Any]:
    """管理者向けダッシュボード情報を取得する"""
    # 管理者情報
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "ユーザーが見つかりません"}
    
    # 統計情報
    user_count = db.query(func.count(User.id)).scalar()
    
    active_sessions = db.query(func.count(ChatSession.id)).filter(
        ChatSession.status == SessionStatus.ACTIVE
    ).scalar()
    
    # 総合情報
    result = {
        "user": {
            "id": str(user.id),
            "name": user.full_name,
            "email": user.email,
        },
        "system_stats": {
            "total_users": user_count,
            "active_users": db.query(func.count(User.id)).filter(User.is_active == True).scalar(),
            "active_chat_sessions": active_sessions,
            "total_universities": db.query(func.count(University.id)).scalar(),
            "total_departments": db.query(func.count(Department.id)).scalar(),
            "total_contents": db.query(func.count(Content.id)).scalar()
        },
        "recent_signups": get_recent_signups(db),
        "user_activity": get_user_activity_summary(db),
        "content_usage": get_content_usage_summary(db),
        "ai_chat_stats": get_ai_chat_stats(db)
    }
    
    return result

def get_chat_stats(db: Session, user_id: UUID) -> Dict[str, Any]:
    """チャット統計情報を取得する"""
    # セッション数
    total_sessions = db.query(func.count(ChatSession.id)).filter(
        ChatSession.user_id == user_id
    ).scalar()
    
    # アクティブセッション数
    active_sessions = db.query(func.count(ChatSession.id)).filter(
        ChatSession.user_id == user_id,
        ChatSession.status == SessionStatus.ACTIVE
    ).scalar()
    
    # 最近のメッセージ数
    recent_messages = db.query(func.count(ChatMessage.id)).join(
        ChatSession, ChatSession.id == ChatMessage.session_id
    ).filter(
        ChatSession.user_id == user_id,
        ChatMessage.created_at >= datetime.utcnow() - timedelta(days=7)
    ).scalar()
    
    return {
        "total_sessions": total_sessions,
        "active_sessions": active_sessions,
        "recent_messages": recent_messages
    }

def get_user_applications_summary(db: Session, user_id: UUID) -> Dict[str, Any]:
    """志望校の概要を取得する"""
    # 志望校数
    desired_schools_count = db.query(func.count(DesiredSchool.id)).filter(
        DesiredSchool.user_id == user_id
    ).scalar()
    
    # 志望学部数
    desired_departments_count = db.query(func.count(DesiredDepartment.id)).join(
        DesiredSchool, DesiredSchool.id == DesiredDepartment.desired_school_id
    ).filter(
        DesiredSchool.user_id == user_id
    ).scalar()
    
    # 志望理由書数
    statements_count = db.query(func.count(PersonalStatement.id)).filter(
        PersonalStatement.user_id == user_id
    ).scalar()
    
    # 上位3つの志望校を取得
    top_schools = db.query(
        DesiredSchool, University.name.label("university_name")
    ).join(
        University, University.id == DesiredSchool.university_id
    ).filter(
        DesiredSchool.user_id == user_id
    ).order_by(
        DesiredSchool.preference_order
    ).limit(3).all()
    
    top_schools_list = [{
        "id": str(school.DesiredSchool.id),
        "university_id": str(school.DesiredSchool.university_id),
        "university_name": school.university_name,
        "preference_order": school.DesiredSchool.preference_order
    } for school in top_schools]
    
    return {
        "total_schools": desired_schools_count,
        "total_departments": desired_departments_count,
        "total_statements": statements_count,
        "top_schools": top_schools_list
    }

def get_learning_progress(db: Session, user_id: UUID) -> Dict[str, Any]:
    """学習進捗情報を取得する"""
    # シンプルな実装 - コンテンツ視聴履歴ベース
    total_views = db.query(func.count(ContentViewHistory.id)).filter(
        ContentViewHistory.user_id == user_id
    ).scalar()
    
    completed_views = db.query(func.count(ContentViewHistory.id)).filter(
        ContentViewHistory.user_id == user_id,
        ContentViewHistory.completed == True
    ).scalar()
    
    recent_views = db.query(func.count(ContentViewHistory.id)).filter(
        ContentViewHistory.user_id == user_id,
        ContentViewHistory.viewed_at >= datetime.utcnow() - timedelta(days=7)
    ).scalar()
    
    # 視聴進捗率
    progress_percentage = 0
    if total_views > 0:
        progress_percentage = int((completed_views / total_views) * 100)
    
    return {
        "total_content_views": total_views,
        "completed_content_views": completed_views,
        "recent_views": recent_views,
        "progress_percentage": progress_percentage
    }

def get_upcoming_events(db: Session, user_id: UUID) -> List[Dict[str, Any]]:
    """予定されているイベント情報を取得する"""
    # シンプルな実装 - 実際のデータモデルに合わせて実装する必要がある
    # 例えば、ScheduleEventテーブルから取得する
    from app.models.desired_school import ScheduleEvent, EventCompletion
    
    # 今日から1ヶ月間のイベントを取得
    now = datetime.utcnow()
    one_month_later = now + timedelta(days=30)
    
    upcoming_events = db.query(
        ScheduleEvent, DesiredDepartment, DesiredSchool, University
    ).join(
        DesiredDepartment, DesiredDepartment.id == ScheduleEvent.desired_department_id
    ).join(
        DesiredSchool, DesiredSchool.id == DesiredDepartment.desired_school_id
    ).join(
        University, University.id == DesiredSchool.university_id
    ).outerjoin(
        EventCompletion, EventCompletion.event_id == ScheduleEvent.id
    ).filter(
        DesiredSchool.user_id == user_id,
        ScheduleEvent.event_date.between(now, one_month_later),
        (EventCompletion.completed == False) | (EventCompletion.id == None)
    ).order_by(
        ScheduleEvent.event_date
    ).limit(5).all()
    
    result = []
    for event, dept, school, university in upcoming_events:
        result.append({
            "id": str(event.id),
            "name": event.event_name,
            "date": event.event_date.isoformat(),
            "type": event.event_type,
            "university_name": university.name,
            "days_remaining": (event.event_date - now).days
        })
    
    return result

def get_recent_contents(db: Session, user_id: UUID) -> List[Dict[str, Any]]:
    """最近視聴したコンテンツ情報を取得する"""
    recent_content_views = db.query(
        ContentViewHistory, Content
    ).join(
        Content, Content.id == ContentViewHistory.content_id
    ).filter(
        ContentViewHistory.user_id == user_id
    ).order_by(
        ContentViewHistory.viewed_at.desc()
    ).limit(5).all()
    
    result = []
    for view, content in recent_content_views:
        result.append({
            "id": str(content.id),
            "title": content.title,
            "type": content.content_type,
            "thumbnail_url": content.thumbnail_url,
            "progress": view.progress,
            "viewed_at": view.viewed_at.isoformat(),
            "is_completed": view.completed
        })
    
    return result

def get_recommendations(db: Session, user_id: UUID) -> Dict[str, Any]:
    """ユーザーへのレコメンデーション情報を取得する"""
    # 実際の実装ではAIベースのレコメンデーションシステムと連携する
    # ここではシンプルな例を示す
    
    # 1. よく見られているコンテンツ上位5件を推奨
    popular_contents = db.query(
        Content,
        func.count(ContentViewHistory.id).label("view_count")
    ).join(
        ContentViewHistory, ContentViewHistory.content_id == Content.id
    ).group_by(
        Content.id
    ).order_by(
        desc("view_count")
    ).limit(5).all()
    
    content_recommendations = [{
        "id": str(content.Content.id),
        "title": content.Content.title,
        "type": content.Content.content_type,
        "thumbnail_url": content.Content.thumbnail_url,
        "view_count": content.view_count
    } for content in popular_contents]
    
    # 2. 志望校の推奨（仮実装）
    # 実際の実装では、ユーザーのプロフィールや興味に基づいて推奨する
    recommended_universities = db.query(
        University
    ).order_by(
        func.random()
    ).limit(3).all()
    
    university_recommendations = [{
        "id": str(university.id),
        "name": university.name
    } for university in recommended_universities]
    
    return {
        "recommended_contents": content_recommendations,
        "recommended_universities": university_recommendations,
        "actions": [
            {"type": "complete_profile", "message": "プロフィールを完成させましょう"},
            {"type": "view_content", "message": "おすすめのコンテンツを見ましょう"},
            {"type": "explore_universities", "message": "志望校を探してみましょう"}
        ]
    }

def get_pending_feedback_requests(db: Session, teacher_id: UUID) -> List[Dict[str, Any]]:
    """教師へのフィードバック要求を取得する"""
    # 実際の実装では、フィードバック要求テーブルからデータを取得
    # ここではシンプルな例を示す
    from app.models.personal_statement import FeedbackRequest
    
    # 存在しないテーブルを仮定しているためコメントアウト
    # pending_requests = db.query(
    #     FeedbackRequest, PersonalStatement, User
    # ).join(
    #     PersonalStatement, PersonalStatement.id == FeedbackRequest.personal_statement_id
    # ).join(
    #     User, User.id == PersonalStatement.user_id
    # ).filter(
    #     FeedbackRequest.teacher_id == teacher_id,
    #     FeedbackRequest.status == "pending"
    # ).order_by(
    #     FeedbackRequest.requested_at.desc()
    # ).limit(10).all()
    
    # 仮のデータを返す
    return [
        {
            "id": "1",
            "student_name": "山田太郎",
            "statement_title": "東京大学文学部志望理由書",
            "requested_at": "2023-05-01T10:30:00Z"
        },
        {
            "id": "2",
            "student_name": "佐藤花子",
            "statement_title": "京都大学経済学部志望理由書",
            "requested_at": "2023-05-02T14:15:00Z"
        }
    ]

def get_recent_teacher_activities(db: Session, teacher_id: UUID) -> List[Dict[str, Any]]:
    """教師の最近の活動を取得する"""
    # 実際の実装では、教師の活動履歴テーブルからデータを取得
    # ここではシンプルな例を示す
    
    # 仮のデータを返す
    return [
        {
            "type": "feedback_provided",
            "target": "山田太郎の志望理由書",
            "datetime": "2023-05-03T09:45:00Z"
        },
        {
            "type": "document_reviewed",
            "target": "佐藤花子の小論文",
            "datetime": "2023-05-02T16:30:00Z"
        },
        {
            "type": "message_sent",
            "target": "鈴木一郎",
            "datetime": "2023-05-01T11:20:00Z"
        }
    ]

def get_student_performance_summary(db: Session, teacher_id: UUID) -> Dict[str, Any]:
    """生徒のパフォーマンス概要を取得する"""
    # 実際の実装では、学生の進捗やパフォーマンスデータを取得
    # ここではシンプルな例を示す
    
    # 仮のデータを返す
    return {
        "total_students": 25,
        "active_students": 20,
        "inactive_students": 5,
        "progress_categories": {
            "excellent": 5,
            "good": 10,
            "average": 7,
            "needs_improvement": 3
        },
        "recent_achievements": [
            {"student_name": "山田太郎", "achievement": "志望理由書完成", "date": "2023-05-03"},
            {"student_name": "佐藤花子", "achievement": "模擬面接完了", "date": "2023-05-02"}
        ]
    }

def get_recent_signups(db: Session) -> List[Dict[str, Any]]:
    """最近のサインアップを取得する"""
    recent_users = db.query(User).order_by(
        User.created_at.desc()
    ).limit(10).all()
    
    return [{
        "id": str(user.id),
        "name": user.full_name,
        "email": user.email,
        "created_at": user.created_at.isoformat(),
        "is_active": user.is_active
    } for user in recent_users]

def get_user_activity_summary(db: Session) -> Dict[str, Any]:
    """ユーザー活動の概要を取得する"""
    # 今日のアクティブユーザー数
    today = datetime.utcnow().date()
    today_active_users = db.query(func.count(User.id)).filter(
        func.date(User.updated_at) == today
    ).scalar()
    
    # 過去7日間のアクティブユーザー数
    week_ago = today - timedelta(days=7)
    weekly_active_users = db.query(func.count(User.id)).filter(
        func.date(User.updated_at) >= week_ago
    ).scalar()
    
    # 過去30日間のアクティブユーザー数
    month_ago = today - timedelta(days=30)
    monthly_active_users = db.query(func.count(User.id)).filter(
        func.date(User.updated_at) >= month_ago
    ).scalar()
    
    return {
        "daily_active_users": today_active_users,
        "weekly_active_users": weekly_active_users,
        "monthly_active_users": monthly_active_users,
    }

def get_content_usage_summary(db: Session) -> Dict[str, Any]:
    """コンテンツ利用の概要を取得する"""
    # 総視聴回数
    total_views = db.query(func.count(ContentViewHistory.id)).scalar()
    
    # 完了率
    completed_views = db.query(func.count(ContentViewHistory.id)).filter(
        ContentViewHistory.completed == True
    ).scalar()
    
    completion_rate = 0
    if total_views > 0:
        completion_rate = round((completed_views / total_views) * 100, 2)
    
    # 人気コンテンツトップ5
    popular_contents = db.query(
        Content.id,
        Content.title,
        Content.content_type,
        func.count(ContentViewHistory.id).label("view_count")
    ).join(
        ContentViewHistory, ContentViewHistory.content_id == Content.id
    ).group_by(
        Content.id
    ).order_by(
        desc("view_count")
    ).limit(5).all()
    
    popular_content_list = [{
        "id": str(content.id),
        "title": content.title,
        "type": content.content_type,
        "view_count": content.view_count
    } for content in popular_contents]
    
    return {
        "total_views": total_views,
        "completed_views": completed_views,
        "completion_rate": completion_rate,
        "popular_contents": popular_content_list
    }

def get_ai_chat_stats(db: Session) -> Dict[str, Any]:
    """AIチャットの統計情報を取得する"""
    # 総セッション数
    total_sessions = db.query(func.count(ChatSession.id)).scalar()
    
    # セッションタイプ別の数
    session_types = db.query(
        ChatSession.session_type,
        func.count(ChatSession.id).label("count")
    ).group_by(
        ChatSession.session_type
    ).all()
    
    session_type_counts = {
        str(session_type.session_type): session_type.count
        for session_type in session_types
    }
    
    # 過去7日間のセッション数
    week_ago = datetime.utcnow() - timedelta(days=7)
    weekly_sessions = db.query(func.count(ChatSession.id)).filter(
        ChatSession.created_at >= week_ago
    ).scalar()
    
    # 過去7日間のメッセージ数
    weekly_messages = db.query(func.count(ChatMessage.id)).filter(
        ChatMessage.created_at >= week_ago
    ).scalar()
    
    return {
        "total_sessions": total_sessions,
        "session_types": session_type_counts,
        "weekly_sessions": weekly_sessions,
        "weekly_messages": weekly_messages,
        "average_messages_per_session": round(weekly_messages / weekly_sessions, 2) if weekly_sessions > 0 else 0
    } 