# backend/app/crud/crud_permission.py
import uuid
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy import update as sql_update, delete as sql_delete

# !!! 注意: モデルのインポートパスは実際のプロジェクト構造に合わせてください !!!
# 修正: 実際のモデルをインポート
from app.models.user import Permission # Permission モデルをインポート
# from sqlalchemy import Column, String, DateTime, UUID as UUID_SQL # 仮のインポートを削除
# from sqlalchemy.dialects.postgresql import UUID # 仮のインポートを削除
# from app.models.base import Base, TimestampMixin # 仮のインポートを削除
# import datetime # 仮のインポートを削除

# 削除: 仮の Permission クラス定義を削除またはコメントアウト
# class Permission(Base, TimestampMixin):
#     __tablename__ = "permissions"
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     name = Column(String, unique=True, index=True, nullable=False)
#     description = Column(String, nullable=True)
#     # created_at, updated_at は TimestampMixin から継承
#
# # !!! ここまで仮のインポート !!!

from app.schemas.permission import PermissionCreate, PermissionUpdate

async def get_permission(db: Session, permission_id: uuid.UUID) -> Permission | None:
    """IDで権限を取得"""
    result = await db.execute(select(Permission).filter(Permission.id == permission_id))
    return result.scalars().first()

async def get_permission_by_name(db: Session, name: str) -> Permission | None:
    """名前で権限を取得"""
    result = await db.execute(select(Permission).filter(Permission.name == name))
    return result.scalars().first()

async def get_permissions(db: Session, skip: int = 0, limit: int = 100) -> list[Permission]:
    """権限一覧を取得"""
    result = await db.execute(select(Permission).offset(skip).limit(limit))
    return result.scalars().all()

async def create_permission(db: Session, permission: PermissionCreate) -> Permission:
    """権限を作成"""
    # Pydantic v1/v2 対応
    if hasattr(permission, 'model_dump'):
        permission_data = permission.model_dump()
    else:
        permission_data = permission.dict()

    db_permission = Permission(**permission_data)
    db.add(db_permission)
    await db.commit()
    await db.refresh(db_permission)
    return db_permission

async def update_permission(db: Session, permission_id: uuid.UUID, permission_in: PermissionUpdate) -> Permission | None:
    """権限を更新"""
    # Pydantic v1/v2 対応
    if hasattr(permission_in, 'model_dump'):
        update_data = permission_in.model_dump(exclude_unset=True)
    else:
        update_data = permission_in.dict(exclude_unset=True)

    if not update_data:
        return await get_permission(db, permission_id) # 更新データがなければ何もしない

    stmt = (
        sql_update(Permission)
        .where(Permission.id == permission_id)
        .values(**update_data)
        .returning(Permission) # 更新後のオブジェクトを取得 (PostgreSQL用)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalars().first()


async def delete_permission(db: Session, permission_id: uuid.UUID) -> Permission | None:
    """権限を削除"""
    permission = await get_permission(db, permission_id)
    if permission:
        stmt = sql_delete(Permission).where(Permission.id == permission_id)
        await db.execute(stmt)
        await db.commit()
    return permission 