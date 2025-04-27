from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from app.models.quiz import Quiz, QuizQuestion, QuizAnswer, UserQuizAttempt, UserQuizAnswer
from app.schemas.quiz import (
    QuizCreate, QuizUpdate, QuizQuestionCreate, QuizQuestionUpdate,
    QuizAnswerCreate, QuizAnswerUpdate, QuizAnswerSubmit,
    UserQuizAttemptCreate, UserQuizAttemptUpdate
)
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import uuid
from datetime import datetime
from sqlalchemy import desc
import random

# クイズのCRUD操作
def create_quiz(db: Session, quiz_in: QuizCreate, user_id: UUID) -> Quiz:
    """新しいクイズを作成します"""
    
    # クイズオブジェクトの作成
    db_quiz = Quiz(
        title=quiz_in.title,
        description=quiz_in.description,
        time_limit=quiz_in.time_limit,
        difficulty=quiz_in.difficulty,
        is_active=quiz_in.is_active,
        pass_percentage=quiz_in.pass_percentage,
        max_attempts=quiz_in.max_attempts,
        created_by=user_id
    )
    db.add(db_quiz)
    db.flush()  # IDを生成するためにフラッシュする
    
    # 質問の作成
    for question_data in quiz_in.questions:
        db_question = QuizQuestion(
            quiz_id=db_quiz.id,
            text=question_data.text,
            question_type=question_data.question_type,
            points=question_data.points,
            order=question_data.order,
            image_url=question_data.image_url
        )
        db.add(db_question)
        db.flush()  # IDを生成するためにフラッシュする
        
        # 回答の作成
        for answer_data in question_data.answers:
            db_answer = QuizAnswer(
                question_id=db_question.id,
                text=answer_data.text,
                is_correct=answer_data.is_correct,
                explanation=answer_data.explanation
            )
            db.add(db_answer)
    
    db.commit()
    db.refresh(db_quiz)
    return db_quiz

def get_quiz(db: Session, quiz_id: UUID) -> Optional[Quiz]:
    """指定されたIDのクイズを取得します"""
    return db.query(Quiz).filter(Quiz.id == quiz_id).first()

def get_quizzes(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None,
    difficulty: Optional[str] = None,
    active_only: bool = True
) -> Tuple[List[Quiz], int]:
    """クイズのリストと総数を取得します"""
    query = db.query(Quiz)
    
    # 検索フィルター
    if search:
        search_term = f"%{search}%"
        query = query.filter(or_(
            Quiz.title.ilike(search_term),
            Quiz.description.ilike(search_term)
        ))
    
    # 難易度フィルター
    if difficulty:
        query = query.filter(Quiz.difficulty == difficulty)
    
    # アクティブのみ表示
    if active_only:
        query = query.filter(Quiz.is_active == True)
    
    # 総数を取得
    total = query.count()
    
    # ページネーション
    quizzes = query.order_by(Quiz.created_at.desc()).offset(skip).limit(limit).all()
    
    return quizzes, total

def update_quiz(db: Session, quiz: Quiz, quiz_in: QuizUpdate) -> Quiz:
    """クイズを更新します"""
    # 基本情報の更新
    for field in quiz_in.__fields_set__:
        if field == "questions":
            continue  # 質問は別途処理
        setattr(quiz, field, getattr(quiz_in, field))
    
    # 質問と回答を更新（既存の質問・回答を削除し、新しいものを作成する方法）
    if quiz_in.questions is not None:
        # クイズに関連する質問と回答をすべて削除
        for question in quiz.questions:
            for answer in question.answers:
                db.delete(answer)
            db.delete(question)
        
        # 新しい質問と回答を作成
        for question_data in quiz_in.questions:
            db_question = QuizQuestion(
                quiz_id=quiz.id,
                text=question_data.text,
                question_type=question_data.question_type,
                points=question_data.points,
                order=question_data.order,
                image_url=question_data.image_url
            )
            db.add(db_question)
            db.flush()
            
            for answer_data in question_data.answers:
                db_answer = QuizAnswer(
                    question_id=db_question.id,
                    text=answer_data.text,
                    is_correct=answer_data.is_correct,
                    explanation=answer_data.explanation
                )
                db.add(db_answer)
    
    db.commit()
    db.refresh(quiz)
    return quiz

def delete_quiz(db: Session, quiz_id: UUID) -> None:
    """クイズを削除します"""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if quiz:
        db.delete(quiz)  # カスケード削除により関連する質問と回答も削除されます
        db.commit()

# クイズ問題のCRUD操作
def create_quiz_question(db: Session, quiz_id: UUID, question: QuizQuestionCreate) -> QuizQuestion:
    """クイズに問題を追加する"""
    # シーケンス番号が指定されていない場合、最後に追加する
    if question.sequence_number is None:
        max_seq = db.query(func.max(QuizQuestion.sequence_number)).filter(
            QuizQuestion.quiz_id == quiz_id
        ).scalar() or 0
        question.sequence_number = max_seq + 1
    
    db_question = QuizQuestion(
        id=uuid.uuid4(),
        quiz_id=quiz_id,
        question_text=question.question_text,
        question_type=question.question_type,
        explanation=question.explanation,
        points=question.points or 1,
        sequence_number=question.sequence_number,
        media_url=question.media_url
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

def get_quiz_questions(db: Session, quiz_id: UUID) -> List[QuizQuestion]:
    """クイズの問題一覧を取得する"""
    return db.query(QuizQuestion).filter(
        QuizQuestion.quiz_id == quiz_id
    ).order_by(
        QuizQuestion.sequence_number
    ).all()

def get_quiz_question(db: Session, question_id: UUID) -> Optional[QuizQuestion]:
    """特定のクイズ問題を取得する"""
    return db.query(QuizQuestion).filter(
        QuizQuestion.id == question_id
    ).options(
        joinedload(QuizQuestion.answers)
    ).first()

def update_quiz_question(db: Session, question_id: UUID, question_data: QuizQuestionUpdate) -> Optional[QuizQuestion]:
    """クイズ問題を更新する"""
    db_question = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if not db_question:
        return None
    
    # 更新可能なフィールドを設定
    if question_data.question_text is not None:
        db_question.question_text = question_data.question_text
    if question_data.question_type is not None:
        db_question.question_type = question_data.question_type
    if question_data.explanation is not None:
        db_question.explanation = question_data.explanation
    if question_data.points is not None:
        db_question.points = question_data.points
    if question_data.sequence_number is not None:
        db_question.sequence_number = question_data.sequence_number
    if question_data.media_url is not None:
        db_question.media_url = question_data.media_url
    
    db.commit()
    db.refresh(db_question)
    return db_question

def delete_quiz_question(db: Session, question_id: UUID) -> bool:
    """クイズ問題を削除する"""
    db_question = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if not db_question:
        return False
    
    # 関連する回答も削除される（カスケード削除）
    db.delete(db_question)
    db.commit()
    return True

# クイズ回答選択肢のCRUD操作
def create_quiz_answer(db: Session, question_id: UUID, answer: QuizAnswerCreate) -> QuizAnswer:
    """クイズ問題に回答選択肢を追加する"""
    # シーケンス番号が指定されていない場合、最後に追加する
    if answer.sequence_number is None:
        max_seq = db.query(func.max(QuizAnswer.sequence_number)).filter(
            QuizAnswer.question_id == question_id
        ).scalar() or 0
        answer.sequence_number = max_seq + 1
    
    db_answer = QuizAnswer(
        id=uuid.uuid4(),
        question_id=question_id,
        answer_text=answer.answer_text,
        is_correct=answer.is_correct,
        explanation=answer.explanation,
        sequence_number=answer.sequence_number
    )
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)
    return db_answer

def get_quiz_answers(db: Session, question_id: UUID) -> List[QuizAnswer]:
    """クイズ問題の回答選択肢一覧を取得する"""
    return db.query(QuizAnswer).filter(
        QuizAnswer.question_id == question_id
    ).order_by(
        QuizAnswer.sequence_number
    ).all()

def update_quiz_answer(db: Session, answer_id: UUID, answer_data: QuizAnswerUpdate) -> Optional[QuizAnswer]:
    """クイズ回答選択肢を更新する"""
    db_answer = db.query(QuizAnswer).filter(QuizAnswer.id == answer_id).first()
    if not db_answer:
        return None
    
    # 更新可能なフィールドを設定
    if answer_data.answer_text is not None:
        db_answer.answer_text = answer_data.answer_text
    if answer_data.is_correct is not None:
        db_answer.is_correct = answer_data.is_correct
    if answer_data.explanation is not None:
        db_answer.explanation = answer_data.explanation
    if answer_data.sequence_number is not None:
        db_answer.sequence_number = answer_data.sequence_number
    
    db.commit()
    db.refresh(db_answer)
    return db_answer

def delete_quiz_answer(db: Session, answer_id: UUID) -> bool:
    """クイズ回答選択肢を削除する"""
    db_answer = db.query(QuizAnswer).filter(QuizAnswer.id == answer_id).first()
    if not db_answer:
        return False
    
    db.delete(db_answer)
    db.commit()
    return True

# ユーザークイズ挑戦のCRUD操作
def start_quiz_attempt(db: Session, quiz_id: UUID, user_id: UUID) -> Tuple[UserQuizAttempt, List[QuizQuestion]]:
    """クイズの挑戦を開始する"""
    # クイズを取得
    quiz = get_quiz(db, quiz_id)
    if not quiz:
        raise ValueError(f"クイズID {quiz_id} が見つかりません")
    
    # 挑戦回数をチェック
    if quiz.max_attempts:
        attempt_count = db.query(func.count(UserQuizAttempt.id)).filter(
            UserQuizAttempt.user_id == user_id,
            UserQuizAttempt.quiz_id == quiz_id
        ).scalar()
        
        if attempt_count >= quiz.max_attempts:
            raise ValueError(f"クイズの最大挑戦回数 ({quiz.max_attempts}) に達しています")
    
    # 挑戦回数を計算
    attempt_number = db.query(func.count(UserQuizAttempt.id)).filter(
        UserQuizAttempt.user_id == user_id,
        UserQuizAttempt.quiz_id == quiz_id
    ).scalar() + 1
    
    # 新しい挑戦を作成
    db_attempt = UserQuizAttempt(
        id=uuid.uuid4(),
        user_id=user_id,
        quiz_id=quiz_id,
        start_time=datetime.utcnow(),
        attempt_number=attempt_number
    )
    db.add(db_attempt)
    db.commit()
    db.refresh(db_attempt)
    
    # 問題を取得
    questions = get_quiz_questions(db, quiz_id)
    
    # 問題をランダム化する場合
    if quiz.is_randomized:
        random.shuffle(questions)
    
    return db_attempt, questions

def submit_quiz_attempt(
    db: Session, attempt_id: UUID, user_answers: List[QuizAnswerSubmit]
) -> UserQuizAttempt:
    """クイズの回答を提出する"""
    # 挑戦を取得
    db_attempt = db.query(UserQuizAttempt).filter(
        UserQuizAttempt.id == attempt_id
    ).options(
        joinedload(UserQuizAttempt.quiz)
    ).first()
    
    if not db_attempt:
        raise ValueError(f"挑戦ID {attempt_id} が見つかりません")
    
    # 既に終了している場合はエラー
    if db_attempt.end_time:
        raise ValueError("この挑戦は既に終了しています")
    
    # 終了時間を設定
    db_attempt.end_time = datetime.utcnow()
    
    # クイズの全問題を取得
    quiz_questions = get_quiz_questions(db, db_attempt.quiz_id)
    total_points = sum(q.points for q in quiz_questions)
    
    # ユーザーの回答を処理
    earned_points = 0
    
    for answer_submit in user_answers:
        # 問題を取得
        question = get_quiz_question(db, answer_submit.question_id)
        if not question:
            continue
        
        # 回答の正解判定
        is_correct = False
        
        if question.question_type in ["MULTIPLE_CHOICE", "SINGLE_CHOICE", "TRUE_FALSE"]:
            # 選択式の場合
            if answer_submit.answer_id:
                # 選択された回答を取得
                selected_answer = db.query(QuizAnswer).filter(
                    QuizAnswer.id == answer_submit.answer_id
                ).first()
                
                if selected_answer:
                    is_correct = selected_answer.is_correct
        else:
            # 記述式の場合（シンプルな文字列比較 - より高度な判定も可能）
            correct_answer = db.query(QuizAnswer).filter(
                QuizAnswer.question_id == question.id,
                QuizAnswer.is_correct == True
            ).first()
            
            if correct_answer and answer_submit.user_text_answer:
                # 大文字小文字を無視して比較
                is_correct = (
                    answer_submit.user_text_answer.strip().lower() == 
                    correct_answer.answer_text.strip().lower()
                )
        
        # ポイントを加算
        points_earned = question.points if is_correct else 0
        earned_points += points_earned
        
        # ユーザー回答を記録
        db_user_answer = UserQuizAnswer(
            id=uuid.uuid4(),
            attempt_id=db_attempt.id,
            question_id=question.id,
            answer_id=answer_submit.answer_id,
            user_text_answer=answer_submit.user_text_answer,
            is_correct=is_correct,
            points_earned=points_earned,
            time_spent_seconds=answer_submit.time_spent_seconds
        )
        db.add(db_user_answer)
    
    # スコアと正答率を計算
    db_attempt.score = earned_points
    
    if total_points > 0:
        db_attempt.percentage = round((earned_points / total_points) * 100, 2)
    else:
        db_attempt.percentage = 0
    
    # 合格判定
    db_attempt.passed = db_attempt.percentage >= db_attempt.quiz.passing_percentage
    
    db.commit()
    db.refresh(db_attempt)
    return db_attempt

def get_quiz_attempt(db: Session, attempt_id: UUID) -> Optional[UserQuizAttempt]:
    """特定のクイズ挑戦を取得する"""
    return db.query(UserQuizAttempt).filter(
        UserQuizAttempt.id == attempt_id
    ).options(
        joinedload(UserQuizAttempt.quiz),
        joinedload(UserQuizAttempt.user_answers).joinedload(UserQuizAnswer.question),
        joinedload(UserQuizAttempt.user_answers).joinedload(UserQuizAnswer.answer)
    ).first()

def get_user_quiz_attempts(db: Session, user_id: UUID, quiz_id: Optional[UUID] = None) -> List[UserQuizAttempt]:
    """ユーザーのクイズ挑戦一覧を取得する"""
    query = db.query(UserQuizAttempt).filter(UserQuizAttempt.user_id == user_id)
    
    if quiz_id:
        query = query.filter(UserQuizAttempt.quiz_id == quiz_id)
    
    return query.order_by(desc(UserQuizAttempt.start_time)).all()

def get_quiz_results(db: Session, quiz_id: UUID, limit: int = 100) -> List[UserQuizAttempt]:
    """クイズの結果一覧を取得する"""
    return db.query(UserQuizAttempt).filter(
        UserQuizAttempt.quiz_id == quiz_id,
        UserQuizAttempt.end_time != None  # 完了した挑戦のみ
    ).order_by(
        desc(UserQuizAttempt.percentage),
        desc(UserQuizAttempt.end_time)
    ).limit(limit).all()

def get_user_quiz_analysis(db: Session, user_id: UUID) -> Dict[str, Any]:
    """ユーザーのクイズ結果分析を取得する"""
    # 完了した挑戦を取得
    completed_attempts = db.query(UserQuizAttempt).filter(
        UserQuizAttempt.user_id == user_id,
        UserQuizAttempt.end_time != None
    ).all()
    
    # 基本統計情報
    total_attempts = len(completed_attempts)
    if total_attempts == 0:
        return {
            "total_attempts": 0,
            "average_score": 0,
            "passed_quizzes": 0,
            "top_score": 0,
            "total_quizzes_taken": 0,
            "by_difficulty": {},
            "recent_attempts": []
        }
    
    # クイズごとの最高スコア
    quiz_highest_scores = {}
    for attempt in completed_attempts:
        quiz_id = str(attempt.quiz_id)
        current_score = attempt.percentage or 0
        
        if quiz_id not in quiz_highest_scores or current_score > quiz_highest_scores[quiz_id]:
            quiz_highest_scores[quiz_id] = current_score
    
    # 難易度別の統計
    difficulty_stats = {}
    for attempt in completed_attempts:
        difficulty = str(attempt.quiz.difficulty_level) if attempt.quiz else "UNKNOWN"
        
        if difficulty not in difficulty_stats:
            difficulty_stats[difficulty] = {
                "attempts": 0,
                "passed": 0,
                "average_score": 0,
                "total_score": 0
            }
        
        difficulty_stats[difficulty]["attempts"] += 1
        if attempt.passed:
            difficulty_stats[difficulty]["passed"] += 1
        
        difficulty_stats[difficulty]["total_score"] += attempt.percentage or 0
    
    # 難易度別の平均スコアを計算
    for difficulty, stats in difficulty_stats.items():
        if stats["attempts"] > 0:
            stats["average_score"] = round(stats["total_score"] / stats["attempts"], 2)
    
    # 全体の統計情報を計算
    total_score = sum(attempt.percentage or 0 for attempt in completed_attempts)
    average_score = round(total_score / total_attempts, 2)
    passed_quizzes = sum(1 for quiz_id, score in quiz_highest_scores.items() if score >= 70)  # 70%を合格とする
    top_score = max((attempt.percentage or 0) for attempt in completed_attempts)
    
    # 最近の挑戦（最新5件）
    recent_attempts = sorted(
        completed_attempts, 
        key=lambda x: x.end_time or datetime.min, 
        reverse=True
    )[:5]
    
    recent_attempts_data = []
    for attempt in recent_attempts:
        quiz_title = attempt.quiz.title if attempt.quiz else "Unknown Quiz"
        recent_attempts_data.append({
            "id": str(attempt.id),
            "quiz_id": str(attempt.quiz_id),
            "quiz_title": quiz_title,
            "score": attempt.percentage,
            "passed": attempt.passed,
            "date": attempt.end_time.isoformat() if attempt.end_time else None
        })
    
    return {
        "total_attempts": total_attempts,
        "average_score": average_score,
        "passed_quizzes": passed_quizzes,
        "top_score": top_score,
        "total_quizzes_taken": len(quiz_highest_scores),
        "by_difficulty": difficulty_stats,
        "recent_attempts": recent_attempts_data
    }

def get_recommended_quizzes(db: Session, user_id: UUID, limit: int = 5) -> List[Quiz]:
    """ユーザーにおすすめのクイズ一覧を取得する"""
    # ユーザーが挑戦したクイズのIDを取得
    attempted_quiz_ids = db.query(UserQuizAttempt.quiz_id).filter(
        UserQuizAttempt.user_id == user_id
    ).distinct().all()
    
    attempted_quiz_ids = [str(quiz_id[0]) for quiz_id in attempted_quiz_ids]
    
    # まだ挑戦していないクイズを取得
    new_quizzes = db.query(Quiz).filter(
        Quiz.is_active == True,
        ~Quiz.id.in_(attempted_quiz_ids) if attempted_quiz_ids else True
    ).order_by(
        func.random()
    ).limit(limit).all()
    
    # 新しいクイズが足りない場合は、挑戦済みの中から追加
    if len(new_quizzes) < limit and attempted_quiz_ids:
        # 合格していないクイズを優先
        failed_quizzes = db.query(Quiz).join(
            UserQuizAttempt, UserQuizAttempt.quiz_id == Quiz.id
        ).filter(
            Quiz.is_active == True,
            Quiz.id.in_(attempted_quiz_ids),
            UserQuizAttempt.user_id == user_id,
            UserQuizAttempt.passed == False
        ).order_by(
            func.random()
        ).limit(limit - len(new_quizzes)).all()
        
        new_quizzes.extend(failed_quizzes)
    
    # それでも足りない場合はランダムに追加
    if len(new_quizzes) < limit:
        additional_quizzes = db.query(Quiz).filter(
            Quiz.is_active == True,
            ~Quiz.id.in_([str(quiz.id) for quiz in new_quizzes])
        ).order_by(
            func.random()
        ).limit(limit - len(new_quizzes)).all()
        
        new_quizzes.extend(additional_quizzes)
    
    return new_quizzes

def create_user_quiz_attempt(db: Session, attempt_in: UserQuizAttemptCreate, user_id: UUID) -> UserQuizAttempt:
    """ユーザーのクイズ挑戦を作成します"""
    now = datetime.datetime.utcnow()
    
    db_attempt = UserQuizAttempt(
        user_id=user_id,
        quiz_id=attempt_in.quiz_id,
        start_time=now,
        is_completed=False,
        score=0,  # 初期スコア
        passed=False  # 初期状態では不合格
    )
    
    db.add(db_attempt)
    db.commit()
    db.refresh(db_attempt)
    return db_attempt

def get_user_quiz_attempt(db: Session, attempt_id: UUID) -> Optional[UserQuizAttempt]:
    """指定されたIDのクイズ挑戦を取得します"""
    return db.query(UserQuizAttempt).filter(UserQuizAttempt.id == attempt_id).first()

def get_user_quiz_attempts(
    db: Session, 
    user_id: UUID,
    quiz_id: Optional[UUID] = None
) -> List[UserQuizAttempt]:
    """ユーザーのクイズ挑戦リストを取得します"""
    query = db.query(UserQuizAttempt).filter(UserQuizAttempt.user_id == user_id)
    
    if quiz_id:
        query = query.filter(UserQuizAttempt.quiz_id == quiz_id)
    
    return query.order_by(UserQuizAttempt.start_time.desc()).all()

def update_user_quiz_attempt(db: Session, attempt: UserQuizAttempt, attempt_update: UserQuizAttemptUpdate) -> UserQuizAttempt:
    """ユーザーのクイズ挑戦を更新します（完了、スコア計算など）"""
    # 回答の保存
    if attempt_update.answers:
        # 既存の回答を削除（再提出の場合）
        for answer in attempt.answers:
            db.delete(answer)
        
        # 新しい回答を追加
        for answer_data in attempt_update.answers:
            db_answer = UserQuizAnswer(
                attempt_id=attempt.id,
                question_id=answer_data.question_id,
                selected_answer_id=answer_data.selected_answer_id
            )
            db.add(db_answer)
        
        db.flush()
    
    # 挑戦の完了
    if attempt_update.is_completed:
        attempt.is_completed = True
        attempt.end_time = datetime.datetime.utcnow()
        
        # スコア計算
        total_points = 0
        earned_points = 0
        
        quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
        
        # クイズの全質問を取得し、合計点数を計算
        questions = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == attempt.quiz_id).all()
        for question in questions:
            total_points += question.points
            
            # ユーザーの回答を検索
            user_answer = db.query(UserQuizAnswer).filter(
                UserQuizAnswer.attempt_id == attempt.id,
                UserQuizAnswer.question_id == question.id
            ).first()
            
            if user_answer:
                # 正解の場合、ポイントを追加
                correct_answer = db.query(QuizAnswer).filter(
                    QuizAnswer.question_id == question.id,
                    QuizAnswer.id == user_answer.selected_answer_id,
                    QuizAnswer.is_correct == True
                ).first()
                
                if correct_answer:
                    earned_points += question.points
        
        # 最終スコアを計算（パーセント）
        if total_points > 0:
            attempt.score = (earned_points / total_points) * 100
        else:
            attempt.score = 0
        
        # 合格判定
        attempt.passed = attempt.score >= quiz.pass_percentage if quiz.pass_percentage else True
    
    db.commit()
    db.refresh(attempt)
    return attempt 