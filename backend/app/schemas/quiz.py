from pydantic import BaseModel, Field, UUID4, validator
from typing import List, Optional, Union, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID

# Enumクラス
class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    SINGLE_CHOICE = "single_choice"
    TRUE_FALSE = "true_false"
    TEXT_INPUT = "TEXT_INPUT"
    ESSAY = "ESSAY"

class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"

# クイズ回答スキーマ
class QuizAnswerBase(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    is_correct: bool = False
    explanation: Optional[str] = None

class QuizAnswerCreate(QuizAnswerBase):
    pass

class QuizAnswerUpdate(BaseModel):
    text: Optional[str] = Field(None, min_length=1, max_length=500)
    is_correct: Optional[bool] = None
    explanation: Optional[str] = None

class QuizAnswer(QuizAnswerBase):
    id: UUID4
    question_id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# クイズ問題スキーマ
class QuizQuestionBase(BaseModel):
    text: str = Field(..., min_length=3, max_length=1000)
    question_type: QuestionType
    points: int = Field(1, ge=1, le=10)
    order: int = 0
    image_url: Optional[str] = None

class QuizQuestionCreate(QuizQuestionBase):
    answers: List[QuizAnswerCreate] = Field(..., min_items=2)

    @validator('answers')
    def validate_answers(cls, answers, values):
        # 回答が少なくとも2つあることを確認
        if len(answers) < 2:
            raise ValueError("少なくとも2つの回答選択肢が必要です")

        # 少なくとも1つの正解があることを確認
        if not any(answer.is_correct for answer in answers):
            raise ValueError("少なくとも1つの正解が必要です")

        # 問題タイプが含まれていることを確認
        if 'question_type' not in values:
            return answers

        # 単一選択問題の場合、正解は1つだけであることを確認
        if values['question_type'] == QuestionType.SINGLE_CHOICE:
            correct_count = sum(1 for answer in answers if answer.is_correct)
            if correct_count != 1:
                raise ValueError("単一選択問題では、正解は1つだけである必要があります")

        # 真偽問題の場合、選択肢は2つであり、1つだけが正解であることを確認
        if values['question_type'] == QuestionType.TRUE_FALSE:
            if len(answers) != 2:
                raise ValueError("真偽問題では、選択肢は2つである必要があります")
            
            correct_count = sum(1 for answer in answers if answer.is_correct)
            if correct_count != 1:
                raise ValueError("真偽問題では、正解は1つだけである必要があります")

        return answers

class QuizQuestionUpdate(BaseModel):
    text: Optional[str] = Field(None, min_length=3, max_length=1000)
    question_type: Optional[QuestionType] = None
    points: Optional[int] = Field(None, ge=1, le=10)
    order: Optional[int] = None
    image_url: Optional[str] = None
    answers: Optional[List[QuizAnswerCreate]] = None

    @validator('answers')
    def validate_answers(cls, answers, values):
        if answers is None:
            return None
            
        # 回答が少なくとも2つあることを確認
        if len(answers) < 2:
            raise ValueError("少なくとも2つの回答選択肢が必要です")

        # 少なくとも1つの正解があることを確認
        if not any(answer.is_correct for answer in answers):
            raise ValueError("少なくとも1つの正解が必要です")

        # 問題タイプが更新されている場合、または既存の問題タイプがある場合
        question_type = values.get('question_type')
        if question_type:
            # 単一選択問題の場合、正解は1つだけであることを確認
            if question_type == QuestionType.SINGLE_CHOICE:
                correct_count = sum(1 for answer in answers if answer.is_correct)
                if correct_count != 1:
                    raise ValueError("単一選択問題では、正解は1つだけである必要があります")

            # 真偽問題の場合、選択肢は2つであり、1つだけが正解であることを確認
            if question_type == QuestionType.TRUE_FALSE:
                if len(answers) != 2:
                    raise ValueError("真偽問題では、選択肢は2つである必要があります")
                
                correct_count = sum(1 for answer in answers if answer.is_correct)
                if correct_count != 1:
                    raise ValueError("真偽問題では、正解は1つだけである必要があります")

        return answers

class QuizQuestion(QuizQuestionBase):
    id: UUID4
    quiz_id: UUID4
    answers: List[QuizAnswer]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# クイズスキーマ
class QuizBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    time_limit: Optional[int] = Field(None, ge=30, description="制限時間（秒）")
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    is_active: bool = True
    pass_percentage: float = Field(70.0, ge=0.0, le=100.0)
    max_attempts: Optional[int] = Field(None, ge=1, description="最大挑戦回数（Noneは無制限）")

class QuizCreate(QuizBase):
    questions: List[QuizQuestionCreate] = Field(..., min_items=1)

    @validator('questions')
    def validate_questions(cls, questions):
        # 少なくとも1つの問題があることを確認
        if len(questions) < 1:
            raise ValueError("クイズには少なくとも1つの問題が必要です")
        return questions

class QuizUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    time_limit: Optional[int] = Field(None, ge=30)
    difficulty: Optional[DifficultyLevel] = None
    is_active: Optional[bool] = None
    pass_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    max_attempts: Optional[int] = Field(None, ge=1)
    questions: Optional[List[QuizQuestionCreate]] = None

    @validator('questions')
    def validate_questions(cls, questions):
        if questions is None:
            return None
            
        # 少なくとも1つの問題があることを確認
        if len(questions) < 1:
            raise ValueError("クイズには少なくとも1つの問題が必要です")
        return questions

class Quiz(QuizBase):
    id: UUID4
    created_by: UUID4
    created_at: datetime
    updated_at: datetime
    questions: List[QuizQuestion]

    class Config:
        orm_mode = True

# ユーザー回答スキーマ
class UserQuizAnswerBase(BaseModel):
    question_id: UUID4
    selected_answer_id: UUID4

class UserQuizAnswerCreate(UserQuizAnswerBase):
    pass

class UserQuizAnswer(UserQuizAnswerBase):
    id: UUID4
    attempt_id: UUID4
    created_at: datetime

    class Config:
        orm_mode = True

# クイズ回答提出スキーマ
class QuizAnswerSubmit(BaseModel):
    question_id: UUID4
    answer_id: Optional[UUID4] = None  # 選択式の場合
    user_text_answer: Optional[str] = None  # 記述式の場合
    time_spent_seconds: Optional[int] = None

# クイズ挑戦スキーマ
class UserQuizAttemptBase(BaseModel):
    quiz_id: UUID4

class UserQuizAttemptCreate(UserQuizAttemptBase):
    pass

class UserQuizAttemptUpdate(BaseModel):
    end_time: Optional[datetime] = None
    is_completed: Optional[bool] = None
    score: Optional[float] = None
    passed: Optional[bool] = None

class UserQuizAttempt(UserQuizAttemptBase):
    id: UUID4
    user_id: UUID4
    start_time: datetime
    end_time: Optional[datetime] = None
    is_completed: bool
    score: float
    passed: bool
    created_at: datetime
    updated_at: datetime
    answers: List[UserQuizAnswer] = []

    class Config:
        orm_mode = True

# クイズリスト取得用レスポンススキーマ
class QuizListResponse(BaseModel):
    items: List[Quiz]
    total: int
    page: int
    size: int
    
    class Config:
        orm_mode = True 