from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from uuid import UUID

class StudyGoalBase(BaseModel):
    """学習目標の基本情報"""
    title: str = Field(..., description="目標タイトル")
    description: Optional[str] = Field(None, description="目標の詳細説明")
    target_date: Optional[date] = Field(None, description="目標達成予定日")
    priority: Optional[int] = Field(1, description="優先度（1-5）", ge=1, le=5)

class StudyGoalCreate(StudyGoalBase):
    """学習目標作成リクエスト"""
    pass

class StudyGoalUpdate(BaseModel):
    """学習目標更新リクエスト"""
    title: Optional[str] = Field(None, description="目標タイトル")
    description: Optional[str] = Field(None, description="目標の詳細説明")
    target_date: Optional[date] = Field(None, description="目標達成予定日")
    priority: Optional[int] = Field(None, description="優先度（1-5）", ge=1, le=5)
    completed: Optional[bool] = Field(None, description="完了フラグ")
    completion_date: Optional[date] = Field(None, description="実際の達成日")

class StudyGoalResponse(StudyGoalBase):
    """学習目標レスポンス"""
    id: UUID = Field(..., description="目標ID")
    study_plan_id: UUID = Field(..., description="紐づく学習計画ID")
    completed: bool = Field(False, description="完了フラグ")
    completion_date: Optional[date] = Field(None, description="実際の達成日")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: Optional[datetime] = Field(None, description="更新日時")

    # ★ Pydantic V2 の model_config を使用
    model_config = {
        "from_attributes": True,
    }

class StudyPlanBase(BaseModel):
    """学習計画の基本情報"""
    title: str = Field(..., description="計画タイトル")
    description: Optional[str] = Field(None, description="計画の詳細説明")
    start_date: date = Field(..., description="開始日")
    end_date: date = Field(..., description="終了予定日")
    subject: Optional[str] = Field(None, description="学習科目")
    level: Optional[str] = Field(None, description="学習レベル")

class StudyPlanCreate(StudyPlanBase):
    """学習計画作成リクエスト"""
    goals: Optional[List[StudyGoalCreate]] = Field([], description="初期の学習目標")

class StudyPlanUpdate(BaseModel):
    """学習計画更新リクエスト"""
    title: Optional[str] = Field(None, description="計画タイトル")
    description: Optional[str] = Field(None, description="計画の詳細説明")
    start_date: Optional[date] = Field(None, description="開始日")
    end_date: Optional[date] = Field(None, description="終了予定日")
    subject: Optional[str] = Field(None, description="学習科目")
    level: Optional[str] = Field(None, description="学習レベル")
    is_active: Optional[bool] = Field(None, description="アクティブフラグ")

class StudyPlanResponse(StudyPlanBase):
    """学習計画レスポンス"""
    id: UUID = Field(..., description="計画ID")
    user_id: UUID = Field(..., description="ユーザーID")
    goals: List[StudyGoalResponse] = Field([], description="学習目標リスト")
    items: List[StudyPlanItemResponse] = Field([], description="学習計画項目リスト")
    is_active: bool = Field(True, description="アクティブフラグ")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: Optional[datetime] = Field(None, description="更新日時")
    completion_rate: Optional[float] = Field(0, description="完了率")

    # ★ Pydantic V2 の model_config を使用
    model_config = {
        "from_attributes": True,
    }

class StudyProgressUpdate(BaseModel):
    """学習進捗更新リクエスト"""
    goal_id: Optional[UUID] = Field(None, description="目標ID（指定された場合はその目標のみ更新）")
    completed: bool = Field(..., description="完了フラグ")
    notes: Optional[str] = Field(None, description="進捗に関するメモ")
    completion_date: Optional[date] = Field(None, description="達成日")

class StudyPlanTemplateBase(BaseModel):
    """学習計画テンプレートの基本情報"""
    title: str = Field(..., description="テンプレートタイトル")
    description: str = Field(..., description="テンプレートの詳細説明")
    subject: str = Field(..., description="対象学習科目")
    level: str = Field(..., description="対象学習レベル")
    duration_days: int = Field(..., description="推奨期間（日数）")

class StudyPlanTemplateResponse(StudyPlanTemplateBase):
    """学習計画テンプレートレスポンス"""
    id: UUID = Field(..., description="テンプレートID")
    goals: List[dict] = Field(..., description="テンプレート目標リスト")
    created_at: datetime = Field(..., description="作成日時")

    # ★ Pydantic V2 の model_config を使用
    model_config = {
        "from_attributes": True,
    }

class StudyPlanItemBase(BaseModel):
    """学習計画項目の基本情報"""
    title: str = Field(..., description="項目タイトル")
    description: Optional[str] = Field(None, description="項目の詳細説明")
    scheduled_date: Optional[datetime] = Field(None, description="予定日時")
    duration_minutes: Optional[int] = Field(None, description="予定時間（分）")
    display_order: Optional[int] = Field(None, description="表示順序")

class StudyPlanItemCreate(StudyPlanItemBase):
    """学習計画項目作成リクエスト"""
    content_id: Optional[UUID] = Field(None, description="関連コンテンツID")

class StudyPlanItemUpdate(BaseModel):
    """学習計画項目更新リクエスト"""
    title: Optional[str] = Field(None, description="項目タイトル")
    description: Optional[str] = Field(None, description="項目の詳細説明")
    scheduled_date: Optional[datetime] = Field(None, description="予定日時")
    duration_minutes: Optional[int] = Field(None, description="予定時間（分）")
    completed: Optional[bool] = Field(None, description="完了フラグ")
    display_order: Optional[int] = Field(None, description="表示順序")
    content_id: Optional[UUID] = Field(None, description="関連コンテンツID")

class StudyPlanItemResponse(StudyPlanItemBase):
    """学習計画項目レスポンス"""
    id: UUID = Field(..., description="項目ID")
    study_plan_id: UUID = Field(..., description="紐づく学習計画ID")
    content_id: Optional[UUID] = Field(None, description="関連コンテンツID")
    completed: bool = Field(False, description="完了フラグ")
    completed_at: Optional[datetime] = Field(None, description="完了日時")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: Optional[datetime] = Field(None, description="更新日時")

    # ★ Pydantic V2 の model_config を使用
    model_config = {
        "from_attributes": True,
    } 