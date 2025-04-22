from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from uuid import UUID

class AIGenerateStudyPlanRequest(BaseModel):
    """AI生成学習計画リクエスト"""
    goal: str = Field(..., description="学習目標")
    start_date: date = Field(..., description="開始日")
    end_date: date = Field(..., description="終了日")
    subject_area: str = Field(..., description="学習分野")
    difficulty_level: str = Field(..., description="難易度レベル")
    additional_requirements: Optional[str] = Field(None, description="追加要件や制約条件")

class AIGenerateContentRequest(BaseModel):
    """AI生成コンテンツリクエスト"""
    topic: str = Field(..., description="トピック")
    content_type: str = Field(..., description="コンテンツタイプ（記事、問題、解説など）")
    difficulty_level: str = Field(..., description="難易度レベル")
    length: Optional[int] = Field(None, description="コンテンツの長さ（単語数など）")
    additional_requirements: Optional[str] = Field(None, description="追加要件や制約条件")

class AIGenerateQuizRequest(BaseModel):
    """AI生成クイズリクエスト"""
    topic: str = Field(..., description="クイズのトピック")
    question_count: int = Field(..., description="質問数", ge=1, le=20)
    difficulty_level: str = Field(..., description="難易度レベル")
    question_types: list[str] = Field(..., description="質問タイプ（選択式、記述式など）")
    additional_requirements: Optional[str] = Field(None, description="追加要件や制約条件")

class AIGenerateResponse(BaseModel):
    """AI生成レスポンス基本クラス"""
    success: bool
    message: str
    content: Optional[dict] = None 