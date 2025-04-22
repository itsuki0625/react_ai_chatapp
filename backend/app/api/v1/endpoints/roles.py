from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.deps import get_current_user, get_db, get_current_superuser
from app.models.user import User
from app.schemas.role import RoleCreate, RoleResponse, RoleUpdate, RoleAssign
from app.crud.role import (
    get_all_roles, 
    get_role_by_id, 
    create_role, 
    update_role, 
    delete_role_by_id,
    assign_role_to_user
)

router = APIRouter()

@router.get("/", response_model=List[RoleResponse])
async def get_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    利用可能なロール一覧を取得
    """
    # 一般ユーザーは自分のロールのみを見れる制限も可能
    roles = get_all_roles(db)
    return roles

@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    特定のロールの詳細と権限を取得
    """
    role = get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定されたロールが見つかりません"
        )
    return role

@router.post("/", response_model=RoleResponse)
async def create_new_role(
    role_data: RoleCreate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    新しいロールを作成（管理者のみ）
    """
    # ロール作成
    new_role = create_role(db, role_data)
    return new_role

@router.put("/{role_id}", response_model=RoleResponse)
async def update_existing_role(
    role_id: str,
    role_data: RoleUpdate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    ロール情報を更新（管理者のみ）
    """
    # 既存のロールを確認
    existing_role = get_role_by_id(db, role_id)
    if not existing_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定されたロールが見つかりません"
        )
    
    # ロール更新
    updated_role = update_role(db, role_id, role_data)
    return updated_role

@router.delete("/{role_id}")
async def delete_role(
    role_id: str,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    ロールを削除（管理者のみ）
    """
    # 既存のロールを確認
    existing_role = get_role_by_id(db, role_id)
    if not existing_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定されたロールが見つかりません"
        )
    
    # ロール削除
    delete_role_by_id(db, role_id)
    return {"message": "ロールが正常に削除されました"}

@router.post("/assign")
async def assign_role(
    role_assignment: RoleAssign,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    ユーザーにロールを割り当て（管理者のみ）
    """
    # ロール割り当て
    try:
        assign_role_to_user(db, role_assignment.user_id, role_assignment.role_id)
        return {"message": "ロールが正常に割り当てられました"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ロールの割り当て中にエラーが発生しました: {str(e)}"
        ) 