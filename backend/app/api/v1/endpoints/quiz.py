from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from app.api.deps import get_current_user, get_async_db, require_permission
from app.models.user import User
from app.models.quiz import Quiz, QuizQuestion, QuizAnswer, UserQuizAttempt, UserQuizAnswer
from app.schemas.quiz import (
    Quiz as QuizSchema,
    QuizCreate,
    QuizUpdate,
    QuizListResponse,
    UserQuizAttempt as UserQuizAttemptSchema,
    UserQuizAttemptCreate,
    UserQuizAttemptUpdate,
    QuizQuestion as QuizQuestionSchema,
    QuizQuestionCreate,
    QuizQuestionUpdate,
    QuizAnswer as QuizAnswerSchema,
    QuizAnswerCreate,
    QuizAnswerUpdate
)
from app.crud import quiz as crud_quiz

logger = logging.getLogger(__name__)
router = APIRouter()

# ===== クイズの基本操作 =====

@router.post("/", response_model=QuizSchema, status_code=status.HTTP_201_CREATED)
async def create_new_quiz(
    quiz_in: QuizCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('quiz_create'))
):
    """
    新しいクイズを作成します。
    """
    try:
        new_quiz = await crud_quiz.create_quiz(db=db, quiz_in=quiz_in, user_id=current_user.id)
        return new_quiz
    except Exception as e:
        logger.error(f"Error creating quiz: {e}", exc_info=True)
        if db.in_transaction(): await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="クイズ作成エラー")


@router.get("/", response_model=QuizListResponse)
async def read_quizzes(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('quiz_read')),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    difficulty: Optional[str] = None,
    active_only: bool = True
):
    """
    クイズ一覧を取得します。フィルタリングとページネーション機能付き。
    """
    try:
        quizzes, total = await crud_quiz.get_quizzes(
            db=db,
            skip=skip,
            limit=limit,
            search=search,
            difficulty=difficulty,
            active_only=active_only
        )
        return {
            "items": quizzes,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit
        }
    except Exception as e:
        logger.error(f"Error reading quizzes: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="クイズ一覧取得エラー")


@router.get("/{quiz_id}", response_model=QuizSchema)
async def read_quiz(
    quiz_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('quiz_read'))
):
    """
    特定のクイズの詳細を取得します。
    """
    try:
        quiz = await crud_quiz.get_quiz(db=db, quiz_id=quiz_id)
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found"
            )
        return quiz
    except Exception as e:
        logger.error(f"Error reading quiz {quiz_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="クイズ取得エラー")


@router.put("/{quiz_id}", response_model=QuizSchema)
async def update_existing_quiz(
    quiz_id: UUID,
    quiz_in: QuizUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('quiz_update'))
):
    """
    クイズを更新します。作成者のみ更新可能。
    """
    try:
        quiz = await crud_quiz.get_quiz(db=db, quiz_id=quiz_id)
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found"
            )
        
        updated_quiz = await crud_quiz.update_quiz(db=db, quiz=quiz, quiz_in=quiz_in)
        return updated_quiz
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating quiz {quiz_id}: {e}", exc_info=True)
        if db.in_transaction(): await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="クイズ更新エラー")


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_quiz(
    quiz_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('quiz_delete'))
):
    """
    クイズを削除します。作成者または管理者のみ削除可能。
    """
    try:
        quiz = await crud_quiz.get_quiz(db=db, quiz_id=quiz_id)
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found"
            )
        
        await crud_quiz.delete_quiz(db=db, quiz_id=quiz_id)
        return None
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error deleting quiz {quiz_id}: {e}", exc_info=True)
        if db.in_transaction(): await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="クイズ削除エラー")


# ===== クイズの問題操作 =====

@router.post("/{quiz_id}/questions", response_model=QuizQuestionSchema)
async def add_question_to_quiz(
    quiz_id: UUID,
    question_in: QuizQuestionCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('quiz_update'))
):
    """
    クイズに問題を追加します。
    """
    try:
        quiz = await crud_quiz.get_quiz(db=db, quiz_id=quiz_id)
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found"
            )
        
        new_question = await crud_quiz.create_quiz_question(db=db, quiz_id=quiz_id, question=question_in)
        return new_question
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error adding question to quiz {quiz_id}: {e}", exc_info=True)
        if db.in_transaction(): await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="問題追加エラー")


@router.get("/{quiz_id}/questions", response_model=List[QuizQuestionSchema])
async def get_questions_for_quiz(
    quiz_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('quiz_read'))
):
    """
    クイズの問題一覧を取得します。
    """
    try:
        quiz = await crud_quiz.get_quiz(db=db, quiz_id=quiz_id)
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found"
            )
        
        questions = await crud_quiz.get_quiz_questions(db=db, quiz_id=quiz_id)
        return questions
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error getting questions for quiz {quiz_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="問題一覧取得エラー")


@router.put("/{quiz_id}/questions/{question_id}", response_model=QuizQuestionSchema)
async def update_question_in_quiz(
    quiz_id: UUID,
    question_id: UUID,
    question_data: QuizQuestionUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('quiz_update'))
):
    """
    クイズの問題を更新します。
    """
    try:
        quiz = await crud_quiz.get_quiz(db=db, quiz_id=quiz_id)
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found"
            )
        
        question = await crud_quiz.get_quiz_question(db=db, question_id=question_id)
        if not question or question.quiz_id != quiz_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found in this quiz"
            )
        
        updated_question = await crud_quiz.update_quiz_question(db=db, question_id=question_id, question_data=question_data)
        return updated_question
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating question {question_id} in quiz {quiz_id}: {e}", exc_info=True)
        if db.in_transaction(): await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="問題更新エラー")


@router.delete("/{quiz_id}/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question_from_quiz(
    quiz_id: UUID,
    question_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('quiz_update'))
):
    """
    クイズの問題を削除します。
    """
    try:
        quiz = await crud_quiz.get_quiz(db=db, quiz_id=quiz_id)
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found"
            )
        
        deleted = await crud_quiz.delete_quiz_question(db=db, question_id=question_id, quiz_id=quiz_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found in this quiz or could not be deleted")
        return None
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error deleting question {question_id} from quiz {quiz_id}: {e}", exc_info=True)
        if db.in_transaction(): await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="問題削除エラー")


# ===== クイズの受験関連 =====

@router.post("/{quiz_id}/attempt", response_model=UserQuizAttemptSchema, status_code=status.HTTP_201_CREATED)
async def start_quiz_attempt_by_id(
    quiz_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('quiz_attempt'))
):
    """
    クイズを受験開始します。
    """
    try:
        quiz = await crud_quiz.get_quiz(db=db, quiz_id=quiz_id)
        if not quiz or not quiz.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active quiz not found")

        attempt = await crud_quiz.start_quiz_attempt(db=db, quiz_id=quiz_id, user_id=current_user.id)
        return attempt
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error starting quiz attempt for quiz {quiz_id} by user {current_user.id}: {e}", exc_info=True)
        if db.in_transaction(): await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="クイズ開始エラー")


@router.post("/{quiz_id}/submit", response_model=UserQuizAttemptSchema)
async def submit_quiz_answers(
    quiz_id: UUID,
    answers: List[Dict[str, Any]] = Body(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('quiz_submit'))
):
    """
    クイズの回答を提出します。
    """
    try:
        submitted_attempt = await crud_quiz.submit_quiz_attempt(
            db=db,
            user_id=current_user.id,
            quiz_id=quiz_id,
            answers=answers
        )
        if not submitted_attempt:
            raise HTTPException(status_code=400, detail="Failed to submit quiz attempt")
        return submitted_attempt
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error submitting quiz answers for quiz {quiz_id} by user {current_user.id}: {e}", exc_info=True)
        if db.in_transaction(): await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="クイズ提出エラー")


@router.get("/{quiz_id}/results", response_model=List[UserQuizAttemptSchema])
async def get_quiz_results_by_id(
    quiz_id: UUID,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('quiz_read'))
):
    """
    クイズの結果を取得します。
    """
    try:
        results = await crud_quiz.get_quiz_results(db=db, quiz_id=quiz_id, limit=limit)
        return results
    except Exception as e:
        logger.error(f"Error getting results for quiz {quiz_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="クイズ結果取得エラー")


# ===== その他のユーティリティ =====

@router.get("/recommended", response_model=List[QuizSchema])
async def get_recommended_quizzes_for_user(
    limit: int = 5,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('quiz_read'))
):
    """
    推奨クイズ一覧を取得します。
    """
    try:
        recommended = await crud_quiz.get_recommended_quizzes(db=db, user_id=current_user.id, limit=limit)
        return recommended
    except Exception as e:
        logger.error(f"Error getting recommended quizzes for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="おすすめクイズ取得エラー")


@router.get("/history", response_model=List[UserQuizAttemptSchema])
async def get_user_quiz_history(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('quiz_read'))
):
    """
    ユーザーのクイズ受験履歴を取得します。
    """
    try:
        history = await crud_quiz.get_user_quiz_attempts(db=db, user_id=current_user.id)
        return history
    except Exception as e:
        logger.error(f"Error getting quiz history for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="クイズ履歴取得エラー")


@router.get("/analysis", response_model=Dict[str, Any])
async def get_quiz_analysis(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('quiz_read'))
):
    """
    ユーザーのクイズ結果分析を取得します。
    """
    try:
        analysis = await crud_quiz.get_user_quiz_analysis(db=db, user_id=current_user.id)
        return analysis
    except Exception as e:
        logger.error(f"Error getting quiz analysis for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="クイズ分析取得エラー") 