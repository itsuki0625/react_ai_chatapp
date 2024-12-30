from sqlalchemy.orm import Session, joinedload
from app.models.personal_statement import PersonalStatement, Feedback
from app.models.desired_school import DesiredDepartment
from app.models.university import Department
from app.schemas.personal_statement import PersonalStatementCreate, PersonalStatementUpdate, FeedbackCreate
from uuid import UUID
from typing import List, Optional

def create_statement(
    db: Session,
    statement: PersonalStatementCreate,
    user_id: UUID
) -> PersonalStatement:
    """新しい志望理由書を作成"""
    db_statement = PersonalStatement(
        user_id=user_id,
        content=statement.content,
        status=statement.status,
        desired_department_id=statement.desired_department_id
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
        .joinedload(Department.university)
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
        .joinedload(Department.university)
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
    statement_update: PersonalStatementUpdate
) -> PersonalStatement:
    """志望理由書を更新"""
    # 更新前の状態を出力
    # print(f"Before update: {statement.__dict__}")
    
    # 更新するフィールドを設定
    update_data = statement_update.dict(exclude_unset=True)
    
    # desired_department_idの存在確認
    if "desired_department_id" in update_data:
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
        return statement
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