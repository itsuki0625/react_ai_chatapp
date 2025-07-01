from sqlalchemy.orm import Session, joinedload
from app.models.personal_statement import PersonalStatement, Feedback
from app.models.desired_school import DesiredDepartment
from app.models.university import Department
from app.schemas.personal_statement import PersonalStatementCreate, PersonalStatementUpdate, FeedbackCreate
from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException, status
from app.models.chat import ChatSession
from app.models.enums import ChatType

def create_statement(
    db: Session,
    statement_in: PersonalStatementCreate,
    user_id: UUID
) -> PersonalStatement:
    """新しい志望理由書を作成"""
    if statement_in.self_analysis_chat_id:
        validate_self_analysis_chat(db, statement_in.self_analysis_chat_id, user_id)

    db_statement = PersonalStatement(
        user_id=user_id,
        content=statement_in.content,
        status=statement_in.status,
        desired_department_id=statement_in.desired_department_id,
        title=statement_in.title,
        keywords=statement_in.keywords,
        self_analysis_chat_id=statement_in.self_analysis_chat_id,
        submission_deadline=statement_in.submission_deadline
    )
    db.add(db_statement)
    db.commit()
    db.refresh(db_statement)
    
    # 関連データを含めて再取得
    return get_statement(db, str(db_statement.id))

def get_statement(
    db: Session,
    statement_id: str
) -> Optional[PersonalStatement]:
    """特定の志望理由書を取得"""
    return db.query(PersonalStatement).filter(
        PersonalStatement.id == statement_id
    ).options(
        joinedload(PersonalStatement.desired_department)
        .joinedload(DesiredDepartment.department)
        .joinedload(Department.university),
        joinedload(PersonalStatement.feedback)
    ).first()

def get_statements(
    db: Session,
    user_id: UUID
) -> List[PersonalStatement]:
    """ユーザーの志望理由書一覧を取得"""
    statements = db.query(PersonalStatement).filter(
        PersonalStatement.user_id == user_id
    ).options(
        joinedload(PersonalStatement.desired_department)
        .joinedload(DesiredDepartment.department)
        .joinedload(Department.university),
        joinedload(PersonalStatement.feedback)
    ).all()
    
    # 明示的にリレーションをロード
    for statement in statements:
        if statement.desired_department:
            db.refresh(statement.desired_department)
            if statement.desired_department.department:
                db.refresh(statement.desired_department.department)
                if statement.desired_department.department.university:
                    db.refresh(statement.desired_department.department.university)
    
    return statements

def update_statement_db(
    db: Session,
    statement: PersonalStatement,
    statement_in: PersonalStatementUpdate,
    user_id: UUID
) -> PersonalStatement:
    """志望理由書を更新"""
    # 更新前の状態を出力
    # print(f"Before update: {statement.__dict__}")
    
    # 更新するフィールドを設定
    update_data = statement_in.model_dump(exclude_unset=True)
    
    if "self_analysis_chat_id" in update_data:
        if update_data["self_analysis_chat_id"] is not None:
            validate_self_analysis_chat(db, update_data["self_analysis_chat_id"], user_id)

    # desired_department_idの存在確認
    if "desired_department_id" in update_data and update_data["desired_department_id"]:
        desired_dept = db.query(DesiredDepartment).filter(
            DesiredDepartment.id == update_data["desired_department_id"]
        ).first()
        if not desired_dept:
            raise ValueError(f"指定された志望学部ID {update_data['desired_department_id']} が見つかりません")

    # 各フィールドを更新
    for key, value in update_data.items():
        setattr(statement, key, value)
    
    try:
        db.commit()
        db.refresh(statement)
        # print(f"After update: {statement.__dict__}")
        
        # 関連データを含めて再取得
        return get_statement(db, str(statement.id))
    except Exception as e:
        db.rollback()
        print(f"Update error: {str(e)}")
        raise

def delete_statement(
    db: Session,
    statement_id: str
) -> None:
    """志望理由書を削除"""
    statement = db.query(PersonalStatement).filter(PersonalStatement.id == statement_id).first()
    if statement:
        db.delete(statement)
        db.commit()

def create_feedback(
    db: Session,
    feedback: FeedbackCreate,
    statement_id: str,
    user_id: UUID
) -> Feedback:
    """フィードバックを作成"""
    db_feedback = Feedback(
        personal_statement_id=statement_id,
        feedback_user_id=user_id,
        content=feedback.content
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback

def get_feedbacks(
    db: Session,
    statement_id: str
) -> List[Feedback]:
    """フィードバック一覧を取得"""
    return db.query(Feedback).filter(Feedback.personal_statement_id == statement_id).all()

def validate_self_analysis_chat(db: Session, chat_id: UUID, user_id: UUID) -> ChatSession:
    """
    指定されたchat_idがユーザーのもので、かつ自己分析タイプか検証する。
    問題なければChatSessionオブジェクトを返す。
    """
    if not chat_id:
        return None

    chat_session = db.query(ChatSession).filter(
        ChatSession.id == chat_id,
        ChatSession.user_id == user_id
    ).first()

    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"指定された自己分析チャット (ID: {chat_id}) が見つかりません。"
        )
    if chat_session.chat_type != ChatType.SELF_ANALYSIS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"指定されたチャット (ID: {chat_id}) は自己分析タイプではありません。"
        )
    return chat_session 