# backend/app/api/routers/permissions.py
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession # AsyncSessionを使用

from app.schemas.permission import PermissionCreate, PermissionRead, PermissionUpdate
from app.crud import crud_permission

# 修正: インポート元を変更
from app.database.database import get_async_db # AsyncSession を取得する関数と仮定
from app.models.user import User # User モデルのインポートパスは要確認
# 修正: get_current_superuser のインポートを削除し、require_permission をインポート
# from app.api.deps import get_current_superuser
from app.api.deps import require_permission

router = APIRouter(
    tags=["Permissions"], # タグ名を変更
    # 修正: ルーターレベルの依存関係を削除
    # dependencies=[Depends(get_current_superuser)],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=PermissionRead, status_code=status.HTTP_201_CREATED)
async def create_permission_endpoint(
    permission_in: PermissionCreate,
    db: AsyncSession = Depends(get_async_db), # AsyncSession を使用
    # 修正: 権限チェックを追加
    current_user: User = Depends(require_permission('permission_create')),
):
    """
    新しい権限を作成します (管理者専用).

    - **name**: 権限の名前 (一意である必要があります)
    - **description**: 権限の説明 (任意)
    """
    existing_permission = await crud_permission.get_permission_by_name(db, name=permission_in.name)
    if existing_permission:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Permission with this name already exists",
        )
    return await crud_permission.create_permission(db=db, permission=permission_in)

@router.get("/", response_model=List[PermissionRead])
async def read_permissions_endpoint(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db), # AsyncSession を使用
    # 修正: 権限チェックを追加
    current_user: User = Depends(require_permission('permission_read')),
):
    """
    権限の一覧を取得します (管理者専用).
    """
    permissions = await crud_permission.get_permissions(db, skip=skip, limit=limit)
    return permissions

@router.get("/{permission_id}", response_model=PermissionRead)
async def read_permission_endpoint(
    permission_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db), # AsyncSession を使用
    # 修正: 権限チェックを追加
    current_user: User = Depends(require_permission('permission_read')),
):
    """
    指定されたIDの権限を取得します (管理者専用).
    """
    db_permission = await crud_permission.get_permission(db, permission_id=permission_id)
    if db_permission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    return db_permission

@router.put("/{permission_id}", response_model=PermissionRead)
async def update_permission_endpoint(
    permission_id: uuid.UUID,
    permission_in: PermissionUpdate,
    db: AsyncSession = Depends(get_async_db), # AsyncSession を使用
    # 修正: 権限チェックを追加
    current_user: User = Depends(require_permission('permission_update')),
):
    """
    指定されたIDの権限を更新します (管理者専用).
    """
    db_permission = await crud_permission.get_permission(db, permission_id=permission_id)
    if db_permission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")

    # Pydantic v1/v2 対応
    if hasattr(permission_in, 'model_dump'):
        update_data = permission_in.model_dump(exclude_unset=True)
    else:
        update_data = permission_in.dict(exclude_unset=True)

    # 更新しようとしている名前が既に他の権限で使われていないかチェック
    if "name" in update_data and update_data["name"] != db_permission.name:
        existing_permission = await crud_permission.get_permission_by_name(db, name=update_data["name"])
        if existing_permission and existing_permission.id != permission_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Permission with this name already exists",
            )

    updated_permission = await crud_permission.update_permission(db=db, permission_id=permission_id, permission_in=permission_in)
    if updated_permission is None: # 更新が失敗した場合（通常は起こらないはず）
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update permission")
    return updated_permission

@router.delete("/{permission_id}", response_model=PermissionRead)
async def delete_permission_endpoint(
    permission_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db), # AsyncSession を使用
    # 修正: 権限チェックを追加
    current_user: User = Depends(require_permission('permission_delete')),
):
    """
    指定されたIDの権限を削除します (管理者専用).
    """
    deleted_permission = await crud_permission.delete_permission(db=db, permission_id=permission_id)
    if deleted_permission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    # TODO: この権限が割り当てられている RolePermission も削除するか、
    #       あるいは削除を拒否するロジックが必要になる場合があります。
    #       DBのCASCADE制約に依存するか、ここで明示的に処理します。
    #       例: await crud_role_permission.remove_permission_from_all_roles(db, permission_id)
    return deleted_permission 