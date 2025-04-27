from typing import Generator
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session, selectinload
from app.database.database import SessionLocal
from app.models.user import User, UserRole, Role, RolePermission, Permission
from app.crud.user import get_user

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(
    request: Request, db: Session = Depends(get_db)
) -> User:
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # DBからユーザー情報を取得 (selectinload を元に戻す)
    db_user = (
        db.query(User)
        .options(  # <- コメントアウト解除
            selectinload(User.user_roles)
            .selectinload(UserRole.role)
            .selectinload(Role.role_permissions)
            .selectinload(RolePermission.permission)
        )          # <- コメントアウト解除
        .filter(User.id == user_id)
        .first()
    )
    
    if db_user is None:
        logger.error(f"request.state に存在するユーザーID ({user_id}) がDBに見つかりません。")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user context",
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
            detail="Insufficient permissions",
        )
    # --- ここまで --- 
    return current_user
 