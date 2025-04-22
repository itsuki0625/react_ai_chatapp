from sqlalchemy.orm import Session, joinedload
from app.models.study_plan import StudyPlan, StudyPlanItem, StudyGoal, StudyPlanTemplate
from app.models.learning_path import (
    LearningPath, LearningPathItem, LearningPathPrerequisite, LearningPathAudience,
    UserLearningPath, UserLearningPathItem, UserLearningPathNote
)
from app.schemas.study_plan import (
    StudyPlanCreate, StudyPlanUpdate, StudyPlanItemCreate, StudyPlanItemUpdate,
    StudyGoalCreate, StudyGoalUpdate, StudyProgressUpdate
)
from app.schemas.learning_path import (
    LearningPathCreate, LearningPathUpdate, UserLearningPathCreate
)
from app.schemas.ai_generate import AIGenerateStudyPlanRequest
from typing import List, Optional, Dict, Any
from uuid import UUID
import uuid
import logging
from datetime import datetime, date
from sqlalchemy import desc, func
from app.services.openai_service import generate_study_plan as openai_generate_study_plan

logger = logging.getLogger(__name__)

# 学習計画のCRUD操作
def create_study_plan(db: Session, plan: StudyPlanCreate, user_id: str) -> StudyPlan:
    """
    新しい学習計画を作成する
    """
    # 学習計画の作成
    db_plan = StudyPlan(
        title=plan.title,
        description=plan.description,
        user_id=user_id,
        start_date=plan.start_date,
        end_date=plan.end_date,
        subject=plan.subject,
        level=plan.level,
        is_active=True,
        created_at=datetime.now()
    )
    
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    
    # 目標の追加（もし存在すれば）
    if plan.goals:
        for goal in plan.goals:
            db_goal = StudyGoal(
                title=goal.title,
                description=goal.description,
                study_plan_id=db_plan.id,
                target_date=goal.target_date,
                priority=goal.priority,
                completed=False,
                created_at=datetime.now()
            )
            db.add(db_goal)
        
        db.commit()
        db.refresh(db_plan)
    
    return db_plan

def get_user_study_plans(db: Session, user_id: str) -> List[StudyPlan]:
    """
    ユーザーの学習計画一覧を取得する
    """
    return db.query(StudyPlan).filter(StudyPlan.user_id == user_id).order_by(StudyPlan.created_at.desc()).all()

def get_study_plan_by_id(db: Session, plan_id: str) -> Optional[StudyPlan]:
    """
    IDで学習計画を取得する
    """
    return db.query(StudyPlan).filter(StudyPlan.id == plan_id).first()

def update_study_plan(db: Session, plan_id: str, plan_data: StudyPlanUpdate) -> StudyPlan:
    """
    学習計画を更新する
    """
    db_plan = get_study_plan_by_id(db, plan_id)
    if not db_plan:
        return None
    
    # 更新データがあるフィールドのみ更新
    if plan_data.title is not None:
        db_plan.title = plan_data.title
    
    if plan_data.description is not None:
        db_plan.description = plan_data.description
    
    if plan_data.start_date is not None:
        db_plan.start_date = plan_data.start_date
    
    if plan_data.end_date is not None:
        db_plan.end_date = plan_data.end_date
    
    if plan_data.subject is not None:
        db_plan.subject = plan_data.subject
    
    if plan_data.level is not None:
        db_plan.level = plan_data.level
    
    if plan_data.is_active is not None:
        db_plan.is_active = plan_data.is_active
    
    db_plan.updated_at = datetime.now()
    
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    
    return db_plan

def delete_study_plan(db: Session, plan_id: str) -> bool:
    """
    学習計画を削除する
    """
    db_plan = get_study_plan_by_id(db, plan_id)
    if not db_plan:
        return False
    
    # 関連する目標も削除
    db.query(StudyGoal).filter(StudyGoal.study_plan_id == plan_id).delete()
    
    # 学習計画を削除
    db.delete(db_plan)
    db.commit()
    
    return True

# 学習計画項目のCRUD操作
def create_study_plan_item(db: Session, plan_id: UUID, item: StudyPlanItemCreate) -> StudyPlanItem:
    """学習計画に項目を追加する"""
    # 表示順序が指定されていない場合、最後に追加する
    if item.display_order is None:
        max_order = db.query(func.max(StudyPlanItem.display_order)).filter(
            StudyPlanItem.study_plan_id == plan_id
        ).scalar() or 0
        item.display_order = max_order + 1
    
    db_item = StudyPlanItem(
        id=uuid.uuid4(),
        study_plan_id=plan_id,
        content_id=item.content_id,
        title=item.title,
        description=item.description,
        scheduled_date=item.scheduled_date,
        duration_minutes=item.duration_minutes,
        completed=False,
        display_order=item.display_order
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_study_plan_items(db: Session, plan_id: UUID) -> List[StudyPlanItem]:
    """学習計画の項目一覧を取得する"""
    return db.query(StudyPlanItem).filter(
        StudyPlanItem.study_plan_id == plan_id
    ).order_by(StudyPlanItem.display_order).all()

def update_study_plan_item(db: Session, item_id: UUID, item_data: StudyPlanItemUpdate) -> Optional[StudyPlanItem]:
    """学習計画の項目を更新する"""
    db_item = db.query(StudyPlanItem).filter(StudyPlanItem.id == item_id).first()
    if not db_item:
        return None
    
    # 更新可能なフィールドを設定
    if item_data.title is not None:
        db_item.title = item_data.title
    if item_data.description is not None:
        db_item.description = item_data.description
    if item_data.scheduled_date is not None:
        db_item.scheduled_date = item_data.scheduled_date
    if item_data.duration_minutes is not None:
        db_item.duration_minutes = item_data.duration_minutes
    if item_data.completed is not None:
        db_item.completed = item_data.completed
        if item_data.completed:
            db_item.completed_at = datetime.utcnow()
        else:
            db_item.completed_at = None
    if item_data.display_order is not None:
        db_item.display_order = item_data.display_order
    
    db.commit()
    db.refresh(db_item)
    return db_item

def delete_study_plan_item(db: Session, item_id: UUID) -> bool:
    """学習計画の項目を削除する"""
    db_item = db.query(StudyPlanItem).filter(StudyPlanItem.id == item_id).first()
    if not db_item:
        return False
    
    db.delete(db_item)
    db.commit()
    return True

def get_study_plan_progress(db: Session, plan_id: str) -> Dict[str, Any]:
    """
    学習計画の進捗状況を取得する
    """
    db_plan = get_study_plan_by_id(db, plan_id)
    if not db_plan:
        return None
    
    # 目標の総数と完了数を取得
    total_goals = len(db_plan.goals)
    completed_goals = len([goal for goal in db_plan.goals if goal.completed])
    
    # 進捗率の計算
    completion_rate = 0
    if total_goals > 0:
        completion_rate = (completed_goals / total_goals) * 100
    
    # 日程の進捗状況
    today = date.today()
    total_days = (db_plan.end_date - db_plan.start_date).days
    elapsed_days = (today - db_plan.start_date).days if today > db_plan.start_date else 0
    elapsed_days = min(elapsed_days, total_days)  # 終了日を超えないようにする
    
    time_progress = 0
    if total_days > 0:
        time_progress = (elapsed_days / total_days) * 100
    
    return {
        "plan_id": db_plan.id,
        "title": db_plan.title,
        "total_goals": total_goals,
        "completed_goals": completed_goals,
        "completion_rate": completion_rate,
        "time_progress": time_progress,
        "start_date": db_plan.start_date,
        "end_date": db_plan.end_date,
        "is_active": db_plan.is_active,
        "goals": [
            {
                "id": goal.id,
                "title": goal.title,
                "completed": goal.completed,
                "priority": goal.priority,
                "target_date": goal.target_date,
                "completion_date": goal.completion_date
            }
            for goal in db_plan.goals
        ]
    }

def update_study_progress(db: Session, plan_id: str, progress: StudyProgressUpdate) -> Dict[str, Any]:
    """
    学習進捗を更新する
    """
    if progress.goal_id:
        # 特定の目標のみ更新
        db_goal = get_study_goal_by_id(db, str(progress.goal_id))
        if not db_goal or str(db_goal.study_plan_id) != plan_id:
            return None
        
        db_goal.completed = progress.completed
        if progress.notes:
            db_goal.notes = progress.notes
        
        if progress.completed and not db_goal.completion_date:
            db_goal.completion_date = progress.completion_date or date.today()
        elif not progress.completed:
            db_goal.completion_date = None
        
        db_goal.updated_at = datetime.now()
        
        db.add(db_goal)
        db.commit()
    else:
        # 学習計画全体の進捗を更新（すべての目標を同じ状態に）
        db_plan = get_study_plan_by_id(db, plan_id)
        if not db_plan:
            return None
        
        for goal in db_plan.goals:
            goal.completed = progress.completed
            if progress.notes:
                goal.notes = progress.notes
                
            if progress.completed and not goal.completion_date:
                goal.completion_date = progress.completion_date or date.today()
            elif not progress.completed:
                goal.completion_date = None
                
            goal.updated_at = datetime.now()
            db.add(goal)
        
        db.commit()
    
    # 学習計画の進捗率を更新
    update_plan_completion_rate(db, plan_id)
    
    # 最新の進捗状況を返す
    return get_study_plan_progress(db, plan_id)

def update_plan_completion_rate(db: Session, plan_id: str) -> None:
    """
    学習計画の進捗率を更新する
    """
    db_plan = get_study_plan_by_id(db, plan_id)
    if not db_plan:
        return
    
    # 目標の総数と完了数を取得して進捗率を計算
    total_goals = len(db_plan.goals)
    completed_goals = len([goal for goal in db_plan.goals if goal.completed])
    
    completion_rate = 0
    if total_goals > 0:
        completion_rate = (completed_goals / total_goals) * 100
    
    db_plan.completion_rate = completion_rate
    db_plan.updated_at = datetime.now()
    
    db.add(db_plan)
    db.commit()

# 学習パスのCRUD操作
def create_learning_path(db: Session, learning_path: LearningPathCreate, created_by: UUID) -> LearningPath:
    """新しい学習パスを作成する"""
    db_path = LearningPath(
        id=uuid.uuid4(),
        title=learning_path.title,
        description=learning_path.description,
        difficulty_level=learning_path.difficulty_level,
        estimated_hours=learning_path.estimated_hours,
        created_by=created_by,
        is_public=learning_path.is_public,
        is_featured=learning_path.is_featured
    )
    db.add(db_path)
    db.flush()
    
    # 前提条件の追加
    if learning_path.prerequisites:
        for prerequisite in learning_path.prerequisites:
            db_prerequisite = LearningPathPrerequisite(
                id=uuid.uuid4(),
                learning_path_id=db_path.id,
                prerequisite=prerequisite
            )
            db.add(db_prerequisite)
    
    # 対象者の追加
    if learning_path.target_audience:
        for audience in learning_path.target_audience:
            db_audience = LearningPathAudience(
                id=uuid.uuid4(),
                learning_path_id=db_path.id,
                target_audience=audience
            )
            db.add(db_audience)
    
    db.commit()
    db.refresh(db_path)
    return db_path

def get_learning_path(db: Session, path_id: UUID) -> Optional[LearningPath]:
    """特定の学習パスを取得する"""
    return db.query(LearningPath).filter(LearningPath.id == path_id).options(
        joinedload(LearningPath.prerequisites),
        joinedload(LearningPath.target_audiences),
        joinedload(LearningPath.items)
    ).first()

def get_learning_paths(db: Session, skip: int = 0, limit: int = 20) -> List[LearningPath]:
    """公開されている学習パス一覧を取得する"""
    return db.query(LearningPath).filter(
        LearningPath.is_public == True
    ).order_by(
        LearningPath.is_featured.desc(),
        desc(LearningPath.created_at)
    ).offset(skip).limit(limit).all()

def get_featured_learning_paths(db: Session, limit: int = 5) -> List[LearningPath]:
    """おすすめの学習パス一覧を取得する"""
    return db.query(LearningPath).filter(
        LearningPath.is_public == True,
        LearningPath.is_featured == True
    ).order_by(
        desc(LearningPath.created_at)
    ).limit(limit).all()

def update_learning_path(db: Session, path_id: UUID, path_data: LearningPathUpdate) -> Optional[LearningPath]:
    """学習パスを更新する"""
    db_path = db.query(LearningPath).filter(LearningPath.id == path_id).first()
    if not db_path:
        return None
    
    # 基本情報の更新
    if path_data.title is not None:
        db_path.title = path_data.title
    if path_data.description is not None:
        db_path.description = path_data.description
    if path_data.difficulty_level is not None:
        db_path.difficulty_level = path_data.difficulty_level
    if path_data.estimated_hours is not None:
        db_path.estimated_hours = path_data.estimated_hours
    if path_data.is_public is not None:
        db_path.is_public = path_data.is_public
    if path_data.is_featured is not None:
        db_path.is_featured = path_data.is_featured
    
    # 前提条件の更新
    if path_data.prerequisites is not None:
        # 既存の前提条件を削除
        db.query(LearningPathPrerequisite).filter(
            LearningPathPrerequisite.learning_path_id == path_id
        ).delete()
        
        # 新しい前提条件を追加
        for prerequisite in path_data.prerequisites:
            db_prerequisite = LearningPathPrerequisite(
                id=uuid.uuid4(),
                learning_path_id=db_path.id,
                prerequisite=prerequisite
            )
            db.add(db_prerequisite)
    
    # 対象者の更新
    if path_data.target_audience is not None:
        # 既存の対象者を削除
        db.query(LearningPathAudience).filter(
            LearningPathAudience.learning_path_id == path_id
        ).delete()
        
        # 新しい対象者を追加
        for audience in path_data.target_audience:
            db_audience = LearningPathAudience(
                id=uuid.uuid4(),
                learning_path_id=db_path.id,
                target_audience=audience
            )
            db.add(db_audience)
    
    db.commit()
    db.refresh(db_path)
    return db_path

def delete_learning_path(db: Session, path_id: UUID) -> bool:
    """学習パスを削除する"""
    db_path = db.query(LearningPath).filter(LearningPath.id == path_id).first()
    if not db_path:
        return False
    
    db.delete(db_path)
    db.commit()
    return True

# ユーザー学習パスのCRUD操作
def enroll_in_learning_path(db: Session, user_id: UUID, path_id: UUID) -> UserLearningPath:
    """ユーザーを学習パスに登録する"""
    # 既に登録されていないか確認
    existing = db.query(UserLearningPath).filter(
        UserLearningPath.user_id == user_id,
        UserLearningPath.learning_path_id == path_id
    ).first()
    
    if existing:
        return existing
    
    # 新規登録
    db_user_path = UserLearningPath(
        id=uuid.uuid4(),
        user_id=user_id,
        learning_path_id=path_id,
        start_date=datetime.utcnow(),
        completed=False,
        progress_percentage=0
    )
    db.add(db_user_path)
    
    # パスの項目を取得してユーザー項目を作成
    path_items = db.query(LearningPathItem).filter(
        LearningPathItem.learning_path_id == path_id
    ).order_by(
        LearningPathItem.sequence_number
    ).all()
    
    for item in path_items:
        db_user_item = UserLearningPathItem(
            id=uuid.uuid4(),
            user_learning_path_id=db_user_path.id,
            learning_path_item_id=item.id,
            status="NOT_STARTED"
        )
        db.add(db_user_item)
    
    db.commit()
    db.refresh(db_user_path)
    return db_user_path

def get_user_learning_paths(db: Session, user_id: UUID) -> List[UserLearningPath]:
    """ユーザーの学習パス一覧を取得する"""
    return db.query(UserLearningPath).filter(
        UserLearningPath.user_id == user_id
    ).options(
        joinedload(UserLearningPath.learning_path)
    ).order_by(
        desc(UserLearningPath.created_at)
    ).all()

def get_user_learning_path(db: Session, user_id: UUID, path_id: UUID) -> Optional[UserLearningPath]:
    """ユーザーの特定の学習パスを取得する"""
    return db.query(UserLearningPath).filter(
        UserLearningPath.user_id == user_id,
        UserLearningPath.learning_path_id == path_id
    ).options(
        joinedload(UserLearningPath.learning_path),
        joinedload(UserLearningPath.items).joinedload(UserLearningPathItem.learning_path_item)
    ).first()

def update_learning_path_item_status(
    db: Session, user_id: UUID, item_id: UUID, status: str
) -> Optional[UserLearningPathItem]:
    """学習パス項目のステータスを更新する"""
    # ユーザーの項目を取得
    db_item = db.query(UserLearningPathItem).filter(
        UserLearningPathItem.id == item_id
    ).options(
        joinedload(UserLearningPathItem.user_learning_path)
    ).first()
    
    if not db_item or db_item.user_learning_path.user_id != user_id:
        return None
    
    # ステータスを更新
    db_item.status = status
    
    # 開始日時と完了日時を設定
    if status == "IN_PROGRESS" and not db_item.started_at:
        db_item.started_at = datetime.utcnow()
    elif status == "COMPLETED" and not db_item.completed_at:
        db_item.completed_at = datetime.utcnow()
    
    # 学習パスの進捗を更新
    user_path_id = db_item.user_learning_path_id
    update_learning_path_progress(db, user_path_id)
    
    db.commit()
    db.refresh(db_item)
    return db_item

def add_item_note(db: Session, user_id: UUID, item_id: UUID, note: str) -> UserLearningPathNote:
    """学習パス項目にノートを追加する"""
    # ユーザーの項目を取得
    db_item = db.query(UserLearningPathItem).filter(
        UserLearningPathItem.id == item_id
    ).options(
        joinedload(UserLearningPathItem.user_learning_path)
    ).first()
    
    if not db_item or db_item.user_learning_path.user_id != user_id:
        raise ValueError("指定された項目が見つからないか、アクセス権限がありません")
    
    # ノートを作成
    db_note = UserLearningPathNote(
        id=uuid.uuid4(),
        user_learning_path_item_id=item_id,
        note=note
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

def update_learning_path_progress(db: Session, user_path_id: UUID) -> None:
    """学習パスの進捗を更新する"""
    # ユーザーの学習パス項目を取得
    items = db.query(UserLearningPathItem).filter(
        UserLearningPathItem.user_learning_path_id == user_path_id
    ).all()
    
    total_items = len(items)
    if total_items == 0:
        return
    
    # 完了した項目をカウント
    completed_items = sum(1 for item in items if item.status == "COMPLETED")
    progress_percentage = int((completed_items / total_items) * 100)
    
    # 学習パスの進捗と完了状態を更新
    db.query(UserLearningPath).filter(
        UserLearningPath.id == user_path_id
    ).update({
        "progress_percentage": progress_percentage,
        "completed": progress_percentage == 100,
        "completed_at": datetime.utcnow() if progress_percentage == 100 else None
    })
    
    db.commit()

# AIによる学習計画生成
async def generate_study_plan_with_ai(
    db: Session, user_id: UUID, request: AIGenerateStudyPlanRequest
) -> StudyPlan:
    """AIを使用して学習計画を生成する"""
    try:
        # 既存のopenai_serviceを使用して学習計画を生成
        plan_data = await openai_generate_study_plan(
            subject=request.subject_area,
            goal=request.goal,
            duration=(request.end_date - request.start_date).days,
            level=request.difficulty_level
        )
        
        # 学習計画を作成
        db_plan = StudyPlan(
            id=uuid.uuid4(),
            user_id=user_id,
            title=f"{request.subject_area}の学習計画：{request.goal}",
            description=f"{request.difficulty_level}レベルの{request.subject_area}を学習するための計画です。目標：{request.goal}",
            start_date=request.start_date,
            end_date=request.end_date,
            subject=request.subject_area,
            level=request.difficulty_level,
            is_active=True,
            created_at=datetime.now()
        )
        db.add(db_plan)
        db.flush()
        
        # 目標をStudyGoalとして追加
        if "goals" in plan_data:
            for goal_data in plan_data["goals"]:
                target_date = None
                if "target_date" in goal_data and goal_data["target_date"]:
                    try:
                        target_date = datetime.fromisoformat(goal_data["target_date"]).date()
                    except (ValueError, TypeError):
                        # 日付形式が正しくない場合は無視
                        pass
                
                db_goal = StudyGoal(
                    id=uuid.uuid4(),
                    study_plan_id=db_plan.id,
                    title=goal_data["title"],
                    description=goal_data.get("description", ""),
                    target_date=target_date,
                    priority=goal_data.get("priority", 1),
                    completed=False,
                    created_at=datetime.now()
                )
                db.add(db_goal)
        
        db.commit()
        db.refresh(db_plan)
        return db_plan
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating study plan with AI: {str(e)}")
        raise ValueError(f"学習計画の生成に失敗しました: {str(e)}")

def add_study_goal(db: Session, plan_id: str, goal: StudyGoalCreate) -> StudyGoal:
    """
    学習計画に目標を追加する
    """
    db_goal = StudyGoal(
        title=goal.title,
        description=goal.description,
        study_plan_id=plan_id,
        target_date=goal.target_date,
        priority=goal.priority,
        completed=False,
        created_at=datetime.now()
    )
    
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    
    return db_goal

def get_study_goal_by_id(db: Session, goal_id: str) -> Optional[StudyGoal]:
    """
    IDで学習目標を取得する
    """
    return db.query(StudyGoal).filter(StudyGoal.id == goal_id).first()

def update_study_goal(db: Session, goal_id: str, goal_data: StudyGoalUpdate) -> StudyGoal:
    """
    学習目標を更新する
    """
    db_goal = get_study_goal_by_id(db, goal_id)
    if not db_goal:
        return None
    
    # 更新データがあるフィールドのみ更新
    if goal_data.title is not None:
        db_goal.title = goal_data.title
    
    if goal_data.description is not None:
        db_goal.description = goal_data.description
    
    if goal_data.target_date is not None:
        db_goal.target_date = goal_data.target_date
    
    if goal_data.priority is not None:
        db_goal.priority = goal_data.priority
    
    if goal_data.completed is not None:
        db_goal.completed = goal_data.completed
        if goal_data.completed and not db_goal.completion_date:
            db_goal.completion_date = date.today()
    
    if goal_data.completion_date is not None:
        db_goal.completion_date = goal_data.completion_date
    
    db_goal.updated_at = datetime.now()
    
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    
    # 関連する学習計画の進捗率を更新
    update_plan_completion_rate(db, db_goal.study_plan_id)
    
    return db_goal

def delete_study_goal(db: Session, goal_id: str) -> bool:
    """
    学習目標を削除する
    """
    db_goal = get_study_goal_by_id(db, goal_id)
    if not db_goal:
        return False
    
    study_plan_id = db_goal.study_plan_id
    
    # 目標を削除
    db.delete(db_goal)
    db.commit()
    
    # 関連する学習計画の進捗率を更新
    update_plan_completion_rate(db, study_plan_id)
    
    return True

def get_study_plan_templates(db: Session, subject: Optional[str] = None, level: Optional[str] = None) -> List[StudyPlanTemplate]:
    """
    学習計画テンプレート一覧を取得する
    """
    query = db.query(StudyPlanTemplate)
    
    if subject:
        query = query.filter(StudyPlanTemplate.subject == subject)
    
    if level:
        query = query.filter(StudyPlanTemplate.level == level)
    
    return query.all() 