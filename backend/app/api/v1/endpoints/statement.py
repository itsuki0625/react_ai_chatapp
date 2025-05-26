from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.api.deps import get_current_user, get_db, require_permission
from app.models.user import User
from app.models.personal_statement import PersonalStatement, Feedback
from app.schemas.personal_statement import (
    PersonalStatementCreate,
    PersonalStatementUpdate,
    PersonalStatementResponse,
    FeedbackCreate,
    FeedbackResponse
)
from app.crud import statement as crud_statement

router = APIRouter()

@router.post("/", response_model=PersonalStatementResponse, status_code=status.HTTP_201_CREATED)
async def create_new_statement(
    statement_in: PersonalStatementCreate,
    current_user: User = Depends(require_permission('statement_manage_own')),
    db: Session = Depends(get_db)
):
    """新しい志望理由書を作成"""
    return crud_statement.create_statement(db=db, statement_in=statement_in, user_id=current_user.id)

@router.get("/", response_model=List[PersonalStatementResponse])
async def get_user_statements(
    current_user: User = Depends(require_permission('statement_manage_own')),
    db: Session = Depends(get_db)
):
    """ユーザーの志望理由書一覧を取得"""
    statements = crud_statement.get_statements(db=db, user_id=current_user.id)
    return statements

@router.get("/{statement_id}", response_model=PersonalStatementResponse)
async def get_single_statement(
    statement_id: UUID,
    current_user: User = Depends(require_permission('statement_manage_own')),
    db: Session = Depends(get_db)
):
    """特定の志望理由書を取得"""
    statement = crud_statement.get_statement(db=db, statement_id=str(statement_id))
    if not statement or statement.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="志望理由書が見つかりません")
    return statement

@router.put("/{statement_id}", response_model=PersonalStatementResponse)
async def update_existing_statement(
    statement_id: UUID,
    statement_in: PersonalStatementUpdate,
    current_user: User = Depends(require_permission('statement_manage_own')),
    db: Session = Depends(get_db)
):
    """志望理由書を更新"""
    statement = crud_statement.get_statement(db, statement_id=str(statement_id))
    if not statement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="志望理由書が見つかりません")
    if statement.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="この志望理由書を編集する権限がありません")

    updated_statement = crud_statement.update_statement_db(
        db=db, statement=statement, statement_in=statement_in, user_id=current_user.id
    )
    return updated_statement

@router.delete("/{statement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_statement(
    statement_id: UUID,
    current_user: User = Depends(require_permission('statement_manage_own')),
    db: Session = Depends(get_db)
):
    """志望理由書を削除"""
    statement = crud_statement.get_statement(db=db, statement_id=str(statement_id))
    if not statement or statement.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="志望理由書が見つかりません")
    
    crud_statement.delete_statement(db=db, statement_id=str(statement_id))
    return

@router.post("/{statement_id}/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_statement_feedback(
    statement_id: UUID,
    feedback_in: FeedbackCreate,
    current_user: User = Depends(require_permission('statement_review_respond')),
    db: Session = Depends(get_db)
):
    """志望理由書にフィードバックを追加"""
    statement = crud_statement.get_statement(db=db, statement_id=str(statement_id))
    if not statement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="フィードバック対象の志望理由書が見つかりません")

    return crud_statement.create_feedback(db=db, feedback=feedback_in, statement_id=statement_id, user_id=current_user.id)

@router.get("/{statement_id}/feedback", response_model=List[FeedbackResponse])
async def get_statement_feedbacks(
    statement_id: UUID,
    current_user: User = Depends(require_permission('statement_manage_own')),
    db: Session = Depends(get_db)
):
    """志望理由書のフィードバック一覧を取得"""
    statement = crud_statement.get_statement(db=db, statement_id=str(statement_id))
    if not statement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="志望理由書が見つかりません")
    if statement.user_id != current_user.id and not current_user.has_permission('statement_review_respond'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="この志望理由書のフィードバックを閲覧する権限がありません")

    return crud_statement.get_feedbacks(db=db, statement_id=statement_id) 