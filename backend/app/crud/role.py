from sqlalchemy.orm import Session
from app.models.user import Role, Permission, RolePermission, User
from app.schemas.role import RoleCreate, RoleUpdate, PermissionCreate, RolePermissionCreate
from typing import List, Optional, Dict, Any
from uuid import UUID
import uuid
from datetime import datetime

# ロールのCRUD操作
def create_role(db: Session, role_data: RoleCreate) -> Role:
    """新しいロールを作成する"""
    # 既存の同名ロールがないか確認
    existing_role = get_role_by_name(db, role_data.name)
    if existing_role:
        raise ValueError(f"ロール名 '{role_data.name}' は既に使用されています")
    
    # 新しいロールを作成
    db_role = Role(
        name=role_data.name,
        description=role_data.description,
        permissions=role_data.permissions,
        created_at=datetime.now()
    )
    
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    
    return db_role

def get_role(db: Session, role_id: UUID) -> Optional[Role]:
    """特定のロールを取得する"""
    return db.query(Role).filter(Role.id == role_id).first()

def get_role_by_name(db: Session, name: str) -> Optional[Role]:
    """名前でロールを取得する"""
    return db.query(Role).filter(Role.name == name).first()

def get_roles(db: Session, skip: int = 0, limit: int = 100) -> List[Role]:
    """ロール一覧を取得する"""
    return db.query(Role).offset(skip).limit(limit).all()

def update_role(db: Session, role_id: str, role_data: RoleUpdate) -> Role:
    """既存のロールを更新する"""
    db_role = get_role_by_id(db, role_id)
    if not db_role:
        raise ValueError(f"ロールID '{role_id}' が見つかりません")
    
    # 名前の変更が要求された場合、重複チェック
    if role_data.name is not None and role_data.name != db_role.name:
        existing_role = get_role_by_name(db, role_data.name)
        if existing_role:
            raise ValueError(f"ロール名 '{role_data.name}' は既に使用されています")
        db_role.name = role_data.name
    
    # その他のフィールドを更新
    if role_data.description is not None:
        db_role.description = role_data.description
    
    if role_data.permissions is not None:
        db_role.permissions = role_data.permissions
    
    db_role.updated_at = datetime.now()
    
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    
    return db_role

def delete_role(db: Session, role_id: UUID) -> bool:
    """ロールを削除する"""
    db_role = db.query(Role).filter(Role.id == role_id).first()
    if db_role:
        db.delete(db_role)
        db.commit()
        return True
    return False

# 権限のCRUD操作
def create_permission(db: Session, permission: PermissionCreate) -> Permission:
    """新しい権限を作成する"""
    db_permission = Permission(
        id=uuid.uuid4(),
        name=permission.name,
        description=permission.description
    )
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission

def get_permission(db: Session, permission_id: UUID) -> Optional[Permission]:
    """特定の権限を取得する"""
    return db.query(Permission).filter(Permission.id == permission_id).first()

def get_permission_by_name(db: Session, name: str) -> Optional[Permission]:
    """名前で権限を取得する"""
    return db.query(Permission).filter(Permission.name == name).first()

def get_permissions(db: Session, skip: int = 0, limit: int = 100) -> List[Permission]:
    """権限一覧を取得する"""
    return db.query(Permission).offset(skip).limit(limit).all()

def delete_permission(db: Session, permission_id: UUID) -> bool:
    """権限を削除する"""
    db_permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if db_permission:
        db.delete(db_permission)
        db.commit()
        return True
    return False

# ロール権限のCRUD操作
def assign_permission_to_role(db: Session, role_permission: RolePermissionCreate) -> RolePermission:
    """ロールに権限を割り当てる"""
    db_role_permission = RolePermission(
        id=uuid.uuid4(),
        role_id=role_permission.role_id,
        permission_id=role_permission.permission_id,
        is_granted=role_permission.is_granted
    )
    db.add(db_role_permission)
    db.commit()
    db.refresh(db_role_permission)
    return db_role_permission

def get_role_permissions(db: Session, role_id: UUID) -> List[RolePermission]:
    """ロールの権限一覧を取得する"""
    return db.query(RolePermission).filter(RolePermission.role_id == role_id).all()

def remove_permission_from_role(db: Session, role_id: UUID, permission_id: UUID) -> bool:
    """ロールから権限を削除する"""
    db_role_permission = db.query(RolePermission).filter(
        RolePermission.role_id == role_id,
        RolePermission.permission_id == permission_id
    ).first()
    if db_role_permission:
        db.delete(db_role_permission)
        db.commit()
        return True
    return False

def get_user_roles(db: Session, user_id: UUID) -> List[Role]:
    """ユーザーのロール一覧を取得する"""
    from app.models.user import UserRole
    return (
        db.query(Role)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user_id)
        .all()
    )

def assign_role_to_user(db: Session, user_id: str, role_id: str) -> None:
    """ユーザーにロールを割り当てる"""
    # ユーザーの存在確認
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"ユーザーID '{user_id}' が見つかりません")
    
    # ロールの存在確認
    role = get_role_by_id(db, role_id)
    if not role:
        raise ValueError(f"ロールID '{role_id}' が見つかりません")
    
    # ロールを割り当て
    user.role_id = role.id
    db.add(user)
    db.commit()
    db.refresh(user)

def get_all_roles(db: Session) -> List[Role]:
    """全てのロールを取得する"""
    return db.query(Role).all()

def get_role_by_id(db: Session, role_id: str) -> Optional[Role]:
    """IDでロールを取得する"""
    return db.query(Role).filter(Role.id == role_id).first()

def delete_role_by_id(db: Session, role_id: str) -> bool:
    """ロールを削除する"""
    db_role = get_role_by_id(db, role_id)
    if not db_role:
        return False
    
    # このロールを持つユーザーの確認
    users_with_role = db.query(User).filter(User.role_id == role_id).all()
    if users_with_role:
        # デフォルトロールを取得
        default_role = get_role_by_name(db, "user")
        if not default_role:
            raise ValueError("デフォルトロールが見つからないため、ロールを削除できません")
        
        # ユーザーにデフォルトロールを割り当て
        for user in users_with_role:
            user.role_id = default_role.id
            db.add(user)
    
    # ロールを削除
    db.delete(db_role)
    db.commit()
    
    return True 