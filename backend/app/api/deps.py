from typing import Generator
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.models.user import User
from app.crud.user import get_user

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(
    request: Request
) -> User:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# 管理者権限チェック用の関数を追加
def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    has_admin_permission = False
    if hasattr(current_user, 'user_roles') and current_user.user_roles:
        for user_role in current_user.user_roles:
            # user_role.role がロードされていることを確認 (selectinload のおかげでロードされているはず)
            if hasattr(user_role, 'role') and user_role.role and \
               hasattr(user_role.role, 'role_permissions') and user_role.role.role_permissions:
                # 各 RolePermission オブジェクトから permission の名前を取得してチェック
                for rp in user_role.role.role_permissions:
                    if hasattr(rp, 'permission') and rp.permission and \
                       hasattr(rp.permission, 'name') and \
                       rp.permission.name.lower() == "admin_access":
                        has_admin_permission = True
                        break # admin権限が見つかったら内側のループを抜ける
            if has_admin_permission:
                break # admin権限が見つかったら外側のループも抜ける

    if not has_admin_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions", # エラーメッセージを維持
        )
    return current_user 