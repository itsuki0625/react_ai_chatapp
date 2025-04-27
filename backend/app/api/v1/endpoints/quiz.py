from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.api.deps import get_current_user, get_db
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
from app.crud.quiz import (
    create_quiz,
    get_quiz,
    get_quizzes,
    update_quiz,
    delete_quiz,
    create_quiz_question,
    get_quiz_questions,
    get_quiz_question,
    update_quiz_question,
    delete_quiz_question,
    create_quiz_answer,
    get_quiz_answers,
    update_quiz_answer,
    delete_quiz_answer,
    start_quiz_attempt,
    submit_quiz_attempt,
    get_quiz_attempt,
    get_user_quiz_attempts,
    get_quiz_results,
    get_user_quiz_analysis,
    get_recommended_quizzes
)

router = APIRouter()

# ===== クイズの基本操作 =====

@router.post("/", response_model=QuizSchema, status_code=status.HTTP_201_CREATED)
def create_new_quiz(
    quiz_in: QuizCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    新しいクイズを作成します。
    """
    return create_quiz(db=db, quiz_in=quiz_in, user_id=current_user.id)


@router.get("/", response_model=QuizListResponse)
def read_quizzes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    difficulty: Optional[str] = None,
    active_only: bool = True
):
    """
    クイズ一覧を取得します。フィルタリングとページネーション機能付き。
    """
    quizzes, total = get_quizzes(
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


@router.get("/{quiz_id}", response_model=QuizSchema)
def read_quiz(
    quiz_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    特定のクイズの詳細を取得します。
    """
    quiz = get_quiz(db=db, quiz_id=quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    return quiz


@router.put("/{quiz_id}", response_model=QuizSchema)
def update_existing_quiz(
    quiz_id: UUID,
    quiz_in: QuizUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    クイズを更新します。作成者のみ更新可能。
    """
    quiz = get_quiz(db=db, quiz_id=quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # クイズの作成者かどうか確認（管理者は常に更新可能）
    if str(quiz.created_by) != str(current_user.id) and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this quiz"
        )
    
    return update_quiz(db=db, quiz=quiz, quiz_in=quiz_in)


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_quiz(
    quiz_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    クイズを削除します。作成者または管理者のみ削除可能。
    """
    quiz = get_quiz(db=db, quiz_id=quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # クイズの作成者かどうか確認（管理者は常に削除可能）
    if str(quiz.created_by) != str(current_user.id) and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this quiz"
        )
    
    delete_quiz(db=db, quiz_id=quiz_id)
    return None


# ===== クイズの問題操作 =====

@router.post("/{quiz_id}/questions", response_model=QuizQuestionSchema)
def add_question_to_quiz(
    quiz_id: UUID,
    question_in: QuizQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    クイズに問題を追加します。
    """
    quiz = get_quiz(db=db, quiz_id=quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # クイズの作成者かどうか確認（管理者は常に追加可能）
    if str(quiz.created_by) != str(current_user.id) and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to add questions to this quiz"
        )
    
    return create_quiz_question(db=db, quiz_id=quiz_id, question=question_in)


@router.get("/{quiz_id}/questions", response_model=List[QuizQuestionSchema])
def get_questions_for_quiz(
    quiz_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    クイズの問題一覧を取得します。
    """
    quiz = get_quiz(db=db, quiz_id=quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    return get_quiz_questions(db=db, quiz_id=quiz_id)


@router.put("/{quiz_id}/questions/{question_id}", response_model=QuizQuestionSchema)
def update_question_in_quiz(
    quiz_id: UUID,
    question_id: UUID,
    question_data: QuizQuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    クイズの問題を更新します。
    """
    # クイズの存在確認
    quiz = get_quiz(db=db, quiz_id=quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # 権限確認
    if str(quiz.created_by) != str(current_user.id) and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this quiz"
        )
    
    # 問題の存在確認
    question = get_quiz_question(db=db, question_id=question_id)
    if not question or question.quiz_id != quiz_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found in this quiz"
        )
    
    return update_quiz_question(db=db, question_id=question_id, question_data=question_data)


@router.delete("/{quiz_id}/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question_from_quiz(
    quiz_id: UUID,
    question_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    クイズの問題を削除します。
    """
    # クイズの存在確認
    quiz = get_quiz(db=db, quiz_id=quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # 権限確認
    if str(quiz.created_by) != str(current_user.id) and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this quiz"
        )
    
    # 問題の存在確認
    question = get_quiz_question(db=db, question_id=question_id)
    if not question or question.quiz_id != quiz_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found in this quiz"
        )
    
    result = delete_quiz_question(db=db, question_id=question_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete question"
        )
    
    return None


# ===== クイズの受験関連 =====

@router.post("/{quiz_id}/attempt", response_model=UserQuizAttemptSchema, status_code=status.HTTP_201_CREATED)
def start_quiz_attempt_by_id(
    quiz_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    クイズを受験開始します。
    """
    # クイズが存在するか確認
    quiz = get_quiz(db=db, quiz_id=quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # クイズがアクティブか確認
    if not quiz.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This quiz is not active"
        )
    
    # 最大挑戦回数チェック（設定されている場合）
    if quiz.max_attempts:
        attempts_count = len(get_user_quiz_attempts(db=db, user_id=current_user.id, quiz_id=quiz_id))
        if attempts_count >= quiz.max_attempts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum attempts ({quiz.max_attempts}) reached for this quiz"
            )
    
    attempt, questions = start_quiz_attempt(db=db, quiz_id=quiz_id, user_id=current_user.id)
    return attempt


@router.post("/{quiz_id}/submit", response_model=UserQuizAttemptSchema)
def submit_quiz_answers(
    quiz_id: UUID,
    answers: List[Dict[str, Any]] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    クイズの回答を提出します。
    """
    # 最新の未完了の挑戦を取得
    attempts = get_user_quiz_attempts(db=db, user_id=current_user.id, quiz_id=quiz_id)
    active_attempts = [a for a in attempts if not a.is_completed]
    
    if not active_attempts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active quiz attempt found"
        )
    
    # 最新の挑戦を取得
    current_attempt = active_attempts[0]
    for a in active_attempts:
        if a.start_time > current_attempt.start_time:
            current_attempt = a
    
    # 回答を提出
    return submit_quiz_attempt(db=db, attempt_id=current_attempt.id, user_answers=answers)


@router.get("/{quiz_id}/results", response_model=List[UserQuizAttemptSchema])
def get_quiz_results_by_id(
    quiz_id: UUID,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    クイズの結果を取得します。
    """
    # クイズの存在確認
    quiz = get_quiz(db=db, quiz_id=quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # 権限確認（作成者または管理者のみ全結果を参照可能）
    if str(quiz.created_by) == str(current_user.id) or current_user.is_admin:
        return get_quiz_results(db=db, quiz_id=quiz_id, limit=limit)
    else:
        # 一般ユーザーは自分の結果のみ参照可能
        return get_user_quiz_attempts(db=db, user_id=current_user.id, quiz_id=quiz_id)


# ===== その他のユーティリティ =====

@router.get("/recommended", response_model=List[QuizSchema])
def get_recommended_quizzes_for_user(
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    推奨クイズ一覧を取得します。
    """
    return get_recommended_quizzes(db=db, user_id=current_user.id, limit=limit)


@router.get("/history", response_model=List[UserQuizAttemptSchema])
def get_user_quiz_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ユーザーのクイズ受験履歴を取得します。
    """
    return get_user_quiz_attempts(db=db, user_id=current_user.id)


@router.get("/analysis", response_model=Dict[str, Any])
def get_quiz_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ユーザーのクイズ結果分析を取得します。
    """
    return get_user_quiz_analysis(db=db, user_id=current_user.id) 