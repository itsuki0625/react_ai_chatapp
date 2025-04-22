from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.study_plan import (
    StudyPlanCreate,
    StudyPlanResponse,
    StudyPlanUpdate,
    StudyGoalCreate,
    StudyGoalResponse,
    StudyGoalUpdate,
    StudyProgressUpdate,
    StudyPlanTemplateResponse,
    StudyPlanItemCreate,
    StudyPlanItemUpdate,
    StudyPlanItemResponse
)
from app.crud.study_plan import (
    create_study_plan,
    get_user_study_plans,
    get_study_plan_by_id,
    update_study_plan,
    delete_study_plan,
    add_study_goal,
    update_study_goal,
    delete_study_goal,
    get_study_plan_progress,
    update_study_progress,
    get_study_plan_templates,
    create_study_plan_item,
    get_study_plan_items,
    update_study_plan_item,
    delete_study_plan_item
)

router = APIRouter()

@router.post("", response_model=StudyPlanResponse)
async def create_new_study_plan(
    study_plan: StudyPlanCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    新しい学習計画を作成
    """
    return create_study_plan(db, study_plan, current_user.id)

@router.get("", response_model=List[StudyPlanResponse])
async def get_all_study_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ユーザーの学習計画一覧を取得
    """
    return get_user_study_plans(db, current_user.id)

@router.get("/{plan_id}", response_model=StudyPlanResponse)
async def get_study_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    特定の学習計画の詳細を取得
    """
    study_plan = get_study_plan_by_id(db, plan_id)
    if not study_plan or study_plan.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学習計画が見つかりません"
        )
    return study_plan

@router.put("/{plan_id}", response_model=StudyPlanResponse)
async def update_existing_study_plan(
    plan_id: str,
    study_plan: StudyPlanUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    学習計画を更新
    """
    existing_plan = get_study_plan_by_id(db, plan_id)
    if not existing_plan or existing_plan.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学習計画が見つかりません"
        )
    return update_study_plan(db, plan_id, study_plan)

@router.delete("/{plan_id}")
async def delete_existing_study_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    学習計画を削除
    """
    existing_plan = get_study_plan_by_id(db, plan_id)
    if not existing_plan or existing_plan.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学習計画が見つかりません"
        )
    
    success = delete_study_plan(db, plan_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="学習計画の削除に失敗しました"
        )
    
    return {"message": "学習計画が正常に削除されました"}

@router.post("/{plan_id}/goals", response_model=StudyGoalResponse)
async def add_goal_to_plan(
    plan_id: str,
    goal: StudyGoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    学習目標を追加
    """
    existing_plan = get_study_plan_by_id(db, plan_id)
    if not existing_plan or existing_plan.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学習計画が見つかりません"
        )
    
    return add_study_goal(db, plan_id, goal)

@router.put("/{plan_id}/goals/{goal_id}", response_model=StudyGoalResponse)
async def update_existing_goal(
    plan_id: str,
    goal_id: str,
    goal: StudyGoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    学習目標を更新
    """
    existing_plan = get_study_plan_by_id(db, plan_id)
    if not existing_plan or existing_plan.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学習計画が見つかりません"
        )
    
    updated_goal = update_study_goal(db, goal_id, goal)
    if not updated_goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学習目標が見つかりません"
        )
    
    return updated_goal

@router.delete("/{plan_id}/goals/{goal_id}")
async def delete_existing_goal(
    plan_id: str,
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    学習目標を削除
    """
    existing_plan = get_study_plan_by_id(db, plan_id)
    if not existing_plan or existing_plan.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学習計画が見つかりません"
        )
    
    success = delete_study_goal(db, goal_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学習目標が見つかりません"
        )
    
    return {"message": "学習目標が正常に削除されました"}

@router.get("/{plan_id}/progress")
async def get_progress(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    学習計画の進捗状況を取得
    """
    existing_plan = get_study_plan_by_id(db, plan_id)
    if not existing_plan or existing_plan.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学習計画が見つかりません"
        )
    
    return get_study_plan_progress(db, plan_id)

@router.post("/{plan_id}/progress")
async def update_progress(
    plan_id: str,
    progress: StudyProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    学習進捗を更新
    """
    existing_plan = get_study_plan_by_id(db, plan_id)
    if not existing_plan or existing_plan.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学習計画が見つかりません"
        )
    
    return update_study_progress(db, plan_id, progress)

@router.get("/templates", response_model=List[StudyPlanTemplateResponse])
async def get_templates(
    subject: Optional[str] = None,
    level: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    学習計画テンプレート一覧を取得
    """
    return get_study_plan_templates(db, subject, level)

@router.post("/ai-generate", response_model=StudyPlanResponse)
async def generate_plan_with_ai(
    request_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AIによる学習計画の自動生成を実行
    """
    try:
        # OpenAI APIを使用して学習計画を生成
        from app.services.openai_service import generate_study_plan
        
        # リクエストデータから必要な情報を取得
        subject = request_data.get("subject", "")
        goal = request_data.get("goal", "")
        duration = request_data.get("duration", 30)
        level = request_data.get("level", "中級")
        
        # AIによる学習計画生成
        plan_data = await generate_study_plan(subject, goal, duration, level)
        
        # 学習計画の作成
        study_plan_create = StudyPlanCreate(
            title=f"{subject}の学習計画",
            description=goal,
            start_date=datetime.now().date(),
            end_date=datetime.now().date().replace(day=datetime.now().day + duration),
            subject=subject,
            level=level,
            goals=[StudyGoalCreate(**goal) for goal in plan_data["goals"]]
        )
        
        # データベースに保存
        study_plan = create_study_plan(db, study_plan_create, current_user.id)
        
        return study_plan
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"学習計画の自動生成に失敗しました: {str(e)}"
        )

@router.post("/{plan_id}/items", response_model=StudyPlanItemResponse)
async def add_item_to_plan(
    plan_id: str,
    item: StudyPlanItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    学習計画に項目を追加
    """
    existing_plan = get_study_plan_by_id(db, plan_id)
    if not existing_plan or existing_plan.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学習計画が見つかりません"
        )
    
    return create_study_plan_item(db, plan_id, item)

@router.get("/{plan_id}/items", response_model=List[StudyPlanItemResponse])
async def get_study_plan_items_endpoint(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    学習計画の項目一覧を取得
    """
    existing_plan = get_study_plan_by_id(db, plan_id)
    if not existing_plan or existing_plan.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学習計画が見つかりません"
        )
    
    return get_study_plan_items(db, plan_id)

@router.put("/{plan_id}/items/{item_id}", response_model=StudyPlanItemResponse)
async def update_study_plan_item_endpoint(
    plan_id: str,
    item_id: str,
    item: StudyPlanItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    学習計画の項目を更新
    """
    existing_plan = get_study_plan_by_id(db, plan_id)
    if not existing_plan or existing_plan.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学習計画が見つかりません"
        )
    
    updated_item = update_study_plan_item(db, item_id, item)
    if not updated_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学習計画項目が見つかりません"
        )
    
    return updated_item

@router.delete("/{plan_id}/items/{item_id}")
async def delete_study_plan_item_endpoint(
    plan_id: str,
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    学習計画の項目を削除
    """
    existing_plan = get_study_plan_by_id(db, plan_id)
    if not existing_plan or existing_plan.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学習計画が見つかりません"
        )
    
    success = delete_study_plan_item(db, item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学習計画項目が見つかりません"
        )
    
    return {"message": "学習計画項目が正常に削除されました"} 