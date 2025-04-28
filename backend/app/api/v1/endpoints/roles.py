import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.role import RoleCreate, RoleRead, RoleUpdate
from app.schemas.permission import PermissionRead # ネストされたレスポンス用
from app.crud import crud_role, crud_permission

# !!! 注意: 依存関係とモデルのインポートパスは実際のプロジェクト構造に合わせてください !!!
# from app.dependencies import get_db, get_current_active_superuser
# from app.models.user import User as UserModel

# 修正: インポート元を変更
from app.database.database import get_async_db
from app.models.user import User # Userモデルのインポートパスは要確認
from app.api.deps import require_permission

router = APIRouter(
    tags=["Roles"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role_endpoint(
    role_in: RoleCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('role_create')),
):
    """
    新しいロールを作成します (管理者専用).

    - **name**: ロール名 (一意)
    - **description**: 説明 (任意)
    - **is_active**: アクティブ状態 (デフォルト: true)
    """
    existing_role = await crud_role.get_role_by_name(db, name=role_in.name)
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Role with this name already exists",
        )
    return await crud_role.create_role(db=db, role=role_in)

@router.get("/", response_model=List[RoleRead])
async def read_roles_endpoint(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('role_read')),
):
    """
    ロールの一覧を取得します (管理者専用).
    各ロールに関連付けられた権限も含まれます。
    """
    roles = await crud_role.get_roles(db, skip=skip, limit=limit)
    return roles

@router.get("/{role_id}", response_model=RoleRead)
async def read_role_endpoint(
    role_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('role_read')),
):
    """
    指定されたIDのロールを取得します (管理者専用).
    関連付けられた権限も含まれます。
    """
    db_role = await crud_role.get_role(db, role_id=role_id)
    if db_role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return db_role

@router.put("/{role_id}", response_model=RoleRead)
async def update_role_endpoint(
    role_id: uuid.UUID,
    role_in: RoleUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('role_update')),
):
    """
    指定されたIDのロールの基本情報 (名前, 説明, アクティブ状態) を更新します (管理者専用).
    権限の変更はこのエンドポイントでは行いません。
    `/roles/{role_id}/permissions` を使用してください。
    """
    db_role = await crud_role.get_role(db, role_id=role_id)
    if db_role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    # Pydantic v1/v2 対応
    if hasattr(role_in, 'model_dump'):
        update_data = role_in.model_dump(exclude_unset=True)
    else:
        update_data = role_in.dict(exclude_unset=True)

    # 更新しようとしている名前が既に他のロールで使われていないかチェック
    if "name" in update_data and update_data["name"] != db_role.name:
        existing_role = await crud_role.get_role_by_name(db, name=update_data["name"])
        if existing_role and existing_role.id != role_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Role with this name already exists",
            )

    updated_role = await crud_role.update_role(db=db, role_id=role_id, role_in=role_in)
    if updated_role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found during update process") # update_role内で見つからないケース
    return updated_role

@router.delete("/{role_id}", response_model=RoleRead)
async def delete_role_endpoint(
    role_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('role_delete')),
):
    """
    指定されたIDのロールを削除します (管理者専用).
    関連する権限割り当て (`RolePermission`) も削除されます (DB or ORMのカスケード設定による).
    削除されたロールの情報（削除前の権限含む）を返します。
    """
    deleted_role = await crud_role.delete_role(db=db, role_id=role_id)
    if deleted_role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return deleted_role

# --- Role Permission Management --- #

@router.post("/{role_id}/permissions/{permission_id}", response_model=RoleRead, status_code=status.HTTP_200_OK)
async def add_permission_to_role_endpoint(
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('role_permission_assign')),
):
    """
    指定されたロールに権限を追加します (管理者専用).
    既に割り当て済みの場合は、変更せずに現在のロール情報を返します。
    ロールまたは権限が見つからない場合は404エラー。
    """
    # crud_role.add_permission_to_role内で存在チェックは行われるが、
    # エラーレスポンスを明確にするため、ここでもチェックする
    role = await crud_role.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    permission = await crud_permission.get_permission(db, permission_id)
    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")

    updated_role = await crud_role.add_permission_to_role(db=db, role_id=role_id, permission_id=permission_id)
    # add_permission_to_role は role/permission が見つかれば必ず Role オブジェクトを返すはず
    return updated_role

@router.delete("/{role_id}/permissions/{permission_id}", response_model=RoleRead, status_code=status.HTTP_200_OK)
async def remove_permission_from_role_endpoint(
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('role_permission_assign')),
):
    """
    指定されたロールから権限を削除します (管理者専用).
    成功した場合、更新されたロール情報（権限リスト含む）を返します。
    ロールまたは権限が見つからない場合、あるいは権限が割り当てられていない場合は404エラー。
    """
    role = await crud_role.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    permission = await crud_permission.get_permission(db, permission_id)
    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")

    updated_role = await crud_role.remove_permission_from_role(db=db, role_id=role_id, permission_id=permission_id)
    if updated_role is None:
        # remove_permission_from_role が None を返すのは、割り当てが見つからなかった場合
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission assignment not found for this role")
    return updated_role


@router.put("/{role_id}/permissions", response_model=RoleRead)
async def set_role_permissions_endpoint(
    role_id: uuid.UUID,
    # リクエストボディの形式を明確化: {"permission_ids": ["uuid1", "uuid2", ...]}
    payload: dict = Body(..., example={"permission_ids": ["f47ac10b-58cc-4372-a567-0e02b2c3d479"]}),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('role_permission_assign')),
):
    """
    ロールに割り当てる権限をリストで一括設定します (管理者専用).
    リクエストボディ (`{"permission_ids": [...]}`) で指定された権限 ID のリストで、ロールの権限を**上書き**します。
    既存の権限割り当てはすべて削除されます。
    空のリスト `[]` を指定すると、すべての権限が削除されます。
    存在しない権限 ID が含まれていた場合、その ID は無視されます（警告ログが出る可能性あり）。
    """
    permission_ids_str = payload.get("permission_ids")
    if permission_ids_str is None or not isinstance(permission_ids_str, list):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Request body must contain 'permission_ids' list."
        )

    try:
        # 文字列のリストを UUID のリストに変換
        permission_ids = [uuid.UUID(pid_str) for pid_str in permission_ids_str]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format in permission_ids: {e}"
        )

    role = await crud_role.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    updated_role = await crud_role.set_role_permissions(db=db, role_id=role_id, permission_ids=permission_ids)
    # set_role_permissions は role が見つかれば必ず Role オブジェクトを返すはず
    return updated_role 