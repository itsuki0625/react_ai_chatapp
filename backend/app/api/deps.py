import uuid
from typing import Generator, Set, Callable, Awaitable
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import SessionLocal, get_async_db
from app.models.user import User, UserRole, Role, RolePermission, Permission
from app.crud import user as crud_user
import logging

logger = logging.getLogger(__name__)

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_async_db)
) -> User:
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated (user_id not found in request state)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
         logger.error(f"Invalid user_id format in request state: {user_id}")
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier",
            headers={"WWW-Authenticate": "Bearer"},
         )

    db_user = await crud_user.get_user(db, user_id=user_uuid)

    if db_user is None:
        logger.error(f"request.state に存在するユーザーUUID ({user_uuid}) がDBに見つかりません。")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user context (user not found)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return db_user

def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    # --- 権限チェック --- 
    has_admin_permission = False
    if hasattr(current_user, 'user_roles') and current_user.user_roles:
        for user_role in current_user.user_roles:
            if hasattr(user_role, 'role') and user_role.role and \
               hasattr(user_role.role, 'role_permissions') and user_role.role.role_permissions:
                for rp in user_role.role.role_permissions:
                    if hasattr(rp, 'permission') and rp.permission and \
                       hasattr(rp.permission, 'name') and \
                       rp.permission.name.lower() == "admin_access":
                        has_admin_permission = True
                        break
            if has_admin_permission:
                break

    if not has_admin_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for superuser access",
        )
    # --- ここまで --- 
    return current_user

def require_permission(*required_permissions: str) -> Callable[[User], Awaitable[User]]:
    """
    ユーザーが必要な権限を持っていることを要求する依存関係関数を返すファクトリ。

    Args:
        *required_permissions: 要求される権限名の可変長引数。

    Returns:
        FastAPIの依存関係として使用できる非同期関数。
        この関数は、必要な権限を持つ認証済みユーザーオブジェクトを返すか、
        HTTPExceptionを発生させる。
    """

    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        """実際の依存関係チェックを行う内部関数"""
        # --- ★ 管理者ロールチェックを追加 ---
        is_admin = False
        if current_user.user_roles:
            for user_role_assoc in current_user.user_roles:
                # lazy='selectin' を想定
                role: Role = user_role_assoc.role
                if role and role.name == '管理者': # ロール名で判定
                    is_admin = True
                    break

        if is_admin:
            logger.debug(f"User {current_user.email} is an administrator. Skipping specific permission check for: {required_permissions}")
            return current_user # 管理者は権限チェックをスキップ
        # --- ★ ここまで ---

        # ユーザーに紐づく権限を取得 (リレーションシップ経由)
        user_permissions: Set[str] = set()
        if current_user.user_roles:
            for user_role_assoc in current_user.user_roles:
                # lazy='selectin' を想定
                role: Role = user_role_assoc.role
                if role and role.permissions:
                    for perm in role.permissions:
                        if isinstance(perm, Permission) and hasattr(perm, 'name'):
                            user_permissions.add(perm.name)
                        else:
                            logger.warning(f"Unexpected item in role.permissions: {perm}")

        logger.debug(f"User {current_user.email} permissions: {user_permissions}")

        # 必要な権限がすべてユーザーの権限に含まれているかチェック
        missing_permissions = set(required_permissions) - user_permissions
        if missing_permissions:
            logger.warning(f"User {current_user.email} lacks required permissions: {missing_permissions}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {', '.join(missing_permissions)}"
            )

        logger.debug(f"User {current_user.email} has required permissions: {required_permissions}")
        return current_user # 権限チェックが通ったらユーザーオブジェクトを返す

    return dependency # 内部関数を返す
 