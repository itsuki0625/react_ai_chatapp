from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
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
from app.crud.statement import (
    create_statement,
    get_statement,
    get_statements,
    update_statement_db,
    delete_statement,
    create_feedback,
    get_feedbacks
)

router = APIRouter()

@router.post("/", response_model=PersonalStatementResponse)
async def create_new_statement(
    statement: PersonalStatementCreate,
    current_user: User = Depends(require_permission('statement_manage_own')),
    db: Session = Depends(get_db)
):
    """新しい志望理由書を作成"""
    return create_statement(db=db, statement=statement, user_id=current_user.id)

@router.get("/", response_model=List[PersonalStatementResponse])
async def get_user_statements(
    current_user: User = Depends(require_permission('statement_manage_own')),
    db: Session = Depends(get_db)
):
    """ユーザーの志望理由書一覧を取得"""
    statements = get_statements(db=db, user_id=current_user.id)
    
    # PersonalStatementResponseのリストとして結果を構築
    result: List[PersonalStatementResponse] = []
    for statement in statements:
        university_name = None
        department_name = None
        
        # 関連データから大学名と学部名を取得
        if statement.desired_department and statement.desired_department.department:
            department_name = statement.desired_department.department.name
            if statement.desired_department.department.university:
                university_name = statement.desired_department.department.university.name
        
        # PersonalStatementResponseスキーマに合わせてデータを作成
        response = PersonalStatementResponse(
            id=statement.id,
            content=statement.content,
            status=statement.status,
            created_at=statement.created_at,
            updated_at=statement.updated_at,
            user_id=statement.user_id,
            desired_department_id=statement.desired_department_id,
            university_name=university_name,
            department_name=department_name,
            # feedback_count と latest_feedback_at は必要に応じて別途取得・設定
            # feedback_count=len(statement.feedbacks), # 例: フィードバック数を取得
            # latest_feedback_at=max(f.created_at for f in statement.feedbacks) if statement.feedbacks else None # 例: 最新フィードバック日時
        )
        result.append(response)
    
    return result

@router.get("/{statement_id}", response_model=PersonalStatementResponse)
async def get_single_statement(
    statement_id: str,
    current_user: User = Depends(require_permission('statement_manage_own')),
    db: Session = Depends(get_db)
):
    """特定の志望理由書を取得"""
    statement = get_statement(db=db, statement_id=statement_id)
    if not statement or statement.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="志望理由書が見つかりません")
    return statement

@router.put("/{statement_id}", response_model=PersonalStatementResponse)
async def update_statement(
    statement_id: str,
    statement_update: PersonalStatementUpdate,
    current_user: User = Depends(require_permission('statement_manage_own')),
    db: Session = Depends(get_db)
):
    """志望理由書を更新"""
    # デバッグ用にリクエストデータを出力
    # print(f"Updating statement: {statement_id}")
    # ★ Pydantic V2 の model_dump を使用
    # print(f"Update data: {statement_update.model_dump()}")
    # ★ Pydantic V1 の dict は削除
    # print(f"Update data: {statement_update.dict()}")

    # 既存の志望理由書を取得
    statement = get_statement(db, statement_id)
    if not statement:
        raise HTTPException(status_code=404, detail="志望理由書が見つかりません")
    if statement.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="この志望理由書を編集する権限がありません")

    try:
        # 更新を実行
        updated_statement = update_statement_db(
            db=db,
            statement=statement,
            statement_update=statement_update
        )
        return updated_statement
    except Exception as e:
        print(f"Error updating statement: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"志望理由書の更新中にエラーが発生しました: {str(e)}"
        )

@router.delete("/{statement_id}")
async def delete_existing_statement(
    statement_id: str,
    current_user: User = Depends(require_permission('statement_manage_own')),
    db: Session = Depends(get_db)
):
    """志望理由書を削除"""
    existing_statement = get_statement(db=db, statement_id=statement_id)
    if not existing_statement or existing_statement.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="志望理由書が見つかりません")
    delete_statement(db=db, statement_id=statement_id)
    return {"message": "志望理由書が削除されました"}

@router.post("/{statement_id}/feedback", response_model=FeedbackResponse)
async def create_statement_feedback(
    statement_id: str,
    feedback: FeedbackCreate,
    current_user: User = Depends(require_permission('statement_review_respond')),
    db: Session = Depends(get_db)
):
    """志望理由書にフィードバックを追加"""
    statement = get_statement(db=db, statement_id=statement_id)
    if not statement:
        raise HTTPException(status_code=404, detail="志望理由書が見つかりません")
    return create_feedback(db=db, feedback=feedback, statement_id=statement_id, user_id=current_user.id)

@router.get("/{statement_id}/feedback", response_model=List[FeedbackResponse])
async def get_statement_feedbacks(
    statement_id: str,
    current_user: User = Depends(require_permission('statement_manage_own')),
    db: Session = Depends(get_db)
):
    """志望理由書のフィードバック一覧を取得"""
    statement = get_statement(db=db, statement_id=statement_id)
    if not statement or statement.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="志望理由書が見つかりません")
    return get_feedbacks(db=db, statement_id=statement_id) 