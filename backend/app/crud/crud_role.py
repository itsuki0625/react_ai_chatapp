# backend/app/crud/crud_role.py
import uuid
from typing import List
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.future import select
from sqlalchemy import update as sql_update, delete as sql_delete, insert as sql_insert
from sqlalchemy.ext.asyncio import AsyncSession # AsyncSessionを使用

# !!! 注意: モデルのインポートパスは実際のプロジェクト構造に合わせてください !!!
# 修正: 実際のモデルをインポート (role_permission_association は不要)
from app.models.user import Role, Permission # RolePermission クラスも直接使わないなら不要
# from app.models.base import Base, TimestampMixin # 必要に応じて Base, TimestampMixin もインポート

# 削除: 仮のモデル定義を削除またはコメントアウト
# from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Table
# from sqlalchemy.dialects.postgresql import UUID
# from sqlalchemy.orm import relationship
# # from app.models.base import Base, TimestampMixin # 上でインポート済み
# import datetime
#
# # RolePermission 中間テーブルの定義 (SQLAlchemy Core Table)
# # Base.metadata に関連付ける
# # 既存の Base オブジェクトを取得する必要がある
# try:
#     # Baseオブジェクトが app.models.base にあると仮定
#     from app.models.base import Base as ExistingBase
# except ImportError:
#     # テストや仮実装用にダミーのBaseを作成
#     from sqlalchemy.orm import declarative_base
#     ExistingBase = declarative_base()
#     print("Warning: Using dummy Base for role_permission_association")
#
# role_permission_association = Table(
#     'role_permissions', ExistingBase.metadata, # 既存のMetaDataを使用
#     Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
#     Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
#     Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False),
#     # Column('is_granted', Boolean, default=True), # DB_model.md に合わせてコメントアウト
#     Column('created_at', DateTime, default=datetime.datetime.utcnow),
#     Column('updated_at', DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow),
#     # UNIQUE constraint (role_id, permission_id) が必要なら追加
# )
#
# # Permission モデル (crud_permission.py からインポートするのが望ましい)
# # ここでは仮定義
# class Permission(ExistingBase, TimestampMixin):
#     __tablename__ = "permissions"
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     name = Column(String, unique=True, index=True, nullable=False)
#     description = Column(String, nullable=True)
#     # roles リレーションは下で定義
#
# # Role モデル
# class Role(ExistingBase, TimestampMixin):
#     __tablename__ = "roles"
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     name = Column(String, unique=True, index=True, nullable=False)
#     description = Column(String, nullable=True)
#     is_active = Column(Boolean, default=True)
#
#     permissions = relationship(
#         "Permission",
#         secondary=role_permission_association,
#         backref="roles",
#         lazy="selectin"
#     )
# # !!! ここまで仮のモデル定義 !!!


from app.schemas.role import RoleCreate, RoleUpdate
from app.crud.crud_permission import get_permission # 権限取得関数をインポート

async def get_role(db: AsyncSession, role_id: uuid.UUID) -> Role | None:
    """IDでロールを取得 (関連する権限も含む)"""
    result = await db.execute(
        select(Role)
        .options(selectinload(Role.permissions))
        .filter(Role.id == role_id)
    )
    return result.scalars().first()

async def get_role_by_name(db: AsyncSession, name: str) -> Role | None:
    """名前でロールを取得"""
    result = await db.execute(select(Role).filter(Role.name == name))
    return result.scalars().first()

async def get_roles(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Role]:
    """ロール一覧を取得 (関連する権限も含む)"""
    result = await db.execute(
        select(Role)
        .options(selectinload(Role.permissions))
        .order_by(Role.name) # 名前順でソート
        .offset(skip)
        .limit(limit)
    )
    # unique() は selectinload と組み合わせる場合に必要
    return result.scalars().unique().all()

async def create_role(db: AsyncSession, role: RoleCreate) -> Role:
    """ロールを作成"""
    # Pydantic v1/v2 対応
    if hasattr(role, 'model_dump'):
        role_data = role.model_dump()
    else:
        role_data = role.dict()

    db_role = Role(**role_data)
    db.add(db_role)
    await db.commit()
    await db.refresh(db_role)
    # permissions はリレーションシップで管理されるため、ここでは空リストを返すのが適切
    # db_role を返せば、RoleRead スキーマが自動的に permissions を解決するはず
    # ただし、refresh後すぐには反映されない可能性があるので、空を設定しておく
    db_role.permissions = []
    return db_role

async def update_role(db: AsyncSession, role_id: uuid.UUID, role_in: RoleUpdate) -> Role | None:
    """ロールを更新 (基本情報のみ)"""
     # Pydantic v1/v2 対応
    if hasattr(role_in, 'model_dump'):
        update_data = role_in.model_dump(exclude_unset=True)
    else:
        update_data = role_in.dict(exclude_unset=True)

    if not update_data:
        return await get_role(db, role_id)

    # DBから現在のロール情報を取得 (権限情報も含む)
    db_role = await get_role(db, role_id)
    if not db_role:
        return None

    # 値を更新
    for key, value in update_data.items():
        setattr(db_role, key, value)

    db.add(db_role) # セッションに追加して変更を追跡
    await db.commit()
    await db.refresh(db_role)
    # refresh後、リレーションシップ(permissions)も最新の状態になるはず
    return db_role


async def delete_role(db: AsyncSession, role_id: uuid.UUID) -> Role | None:
    """ロールを削除"""
    # 削除前にロール情報を取得 (権限情報含む) して返すため
    role_to_delete = await get_role(db, role_id)
    if not role_to_delete:
        return None

    # 削除実行
    await db.delete(role_to_delete)
    await db.commit()

    return role_to_delete # 削除されたオブジェクトを返す

async def add_permission_to_role(db: AsyncSession, role_id: uuid.UUID, permission_id: uuid.UUID) -> Role | None:
    """ロールに権限を追加"""
    role = await get_role(db, role_id)
    permission = await get_permission(db, permission_id)

    if not role or not permission:
        return None

    # 既に権限が割り当てられているかチェック (リレーションシップ経由)
    if permission in role.permissions:
        return role # 既に存在する場合はそのままロールを返す

    # リレーションシップに追加
    role.permissions.append(permission)
    db.add(role)
    await db.commit()
    await db.refresh(role) # relationship の変更を反映

    return role

async def remove_permission_from_role(db: AsyncSession, role_id: uuid.UUID, permission_id: uuid.UUID) -> Role | None:
    """ロールから権限を削除"""
    role = await get_role(db, role_id)
    permission = await get_permission(db, permission_id)

    if not role or not permission:
        return None

    # 権限が割り当てられているかチェック
    if permission not in role.permissions:
        return None # 削除対象が見つからない場合は None を返す

    # リレーションシップから削除
    role.permissions.remove(permission)
    db.add(role)
    await db.commit()
    await db.refresh(role) # relationship の変更を反映

    return role

async def set_role_permissions(db: AsyncSession, role_id: uuid.UUID, permission_ids: List[uuid.UUID]) -> Role | None:
    """ロールの権限をリストで一括設定（既存はクリアされる）"""
    role = await get_role(db, role_id)
    if not role:
        return None

    # 新しい権限リストに対応するPermissionオブジェクトを取得
    if not permission_ids:
        new_permissions = []
    else:
        stmt = select(Permission).where(Permission.id.in_(permission_ids))
        result = await db.execute(stmt)
        new_permissions = result.scalars().all()

        # 指定されたIDの権限がすべて見つかったかチェック (任意)
        if len(new_permissions) != len(set(permission_ids)):
            print(f"Warning: Some permission IDs not found: {set(permission_ids) - {p.id for p in new_permissions}}")
            # エラーにする場合はここで raise HTTPException

    # ロールの権限を新しいリストで上書き
    role.permissions = new_permissions
    db.add(role)
    await db.commit()
    await db.refresh(role)

    return role 