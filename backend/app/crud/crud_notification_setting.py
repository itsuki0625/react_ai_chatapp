from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func # func をインポート
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload # ユーザー情報を eager load するために追加

from app.models.notification_setting import NotificationSetting as NotificationSettingModel
from app.models.user import User as UserModel # Userモデルをインポート
from app.schemas.notification_setting import NotificationSettingUpdate
from app.models.enums import NotificationType


async def get_notification_setting(
    db: AsyncSession, *, user_id: UUID, notification_type: NotificationType
) -> Optional[NotificationSettingModel]:
    """
    特定のユーザーの特定の通知タイプの通知設定を取得する
    """
    stmt = select(NotificationSettingModel).filter(
        NotificationSettingModel.user_id == user_id,
        NotificationSettingModel.notification_type == notification_type
    )
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_notification_setting_by_id(
    db: AsyncSession, *, setting_id: UUID
) -> Optional[NotificationSettingModel]:
    """
    IDで特定の通知設定を取得する
    """
    stmt = select(NotificationSettingModel).filter(NotificationSettingModel.id == setting_id).options(selectinload(NotificationSettingModel.user)) # ユーザー情報もロード
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_notification_settings_by_user(
    db: AsyncSession, *, user_id: UUID, skip: int = 0, limit: int = 100
) -> List[NotificationSettingModel]:
    """
    特定のユーザーの通知設定一覧を取得する (ページネーション対応)
    """
    stmt = (
        select(NotificationSettingModel)
        .filter(NotificationSettingModel.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .options(selectinload(NotificationSettingModel.user)) # ユーザー情報もロード
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_all_notification_settings(
    db: AsyncSession, *, skip: int = 0, limit: int = 100, user_id: Optional[UUID] = None
) -> List[NotificationSettingModel]:
    """
    全ての通知設定を取得する (ページネーションと任意でユーザーIDによるフィルタリング対応)
    Admin用
    """
    stmt = select(NotificationSettingModel).order_by(NotificationSettingModel.user_id, NotificationSettingModel.notification_type).options(selectinload(NotificationSettingModel.user)) # ユーザー情報もロード

    if user_id:
        stmt = stmt.filter(NotificationSettingModel.user_id == user_id)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_all_notification_settings_count(
    db: AsyncSession, *, user_id: Optional[UUID] = None
) -> int:
    """
    全ての通知設定の総数を取得する (任意でユーザーIDによるフィルタリング対応)
    Admin用 (ページネーションのtotalを計算するため)
    """
    # SQLAlchemy 2.0 スタイルでの count
    count_stmt = select(func.count(NotificationSettingModel.id))
    if user_id:
        count_stmt = count_stmt.filter(NotificationSettingModel.user_id == user_id)
    
    result = await db.execute(count_stmt)
    return result.scalar_one()


async def create_notification_setting(
    db: AsyncSession, *, user_id: UUID, notification_type: NotificationType, email_enabled: bool = True, push_enabled: bool = False, in_app_enabled: bool = True
) -> NotificationSettingModel:
    """
    新しい通知設定を作成する (ユーザー登録時などに使用されることを想定)
    """
    db_obj = NotificationSettingModel(
        user_id=user_id,
        notification_type=notification_type,
        email_enabled=email_enabled,
        push_enabled=push_enabled,
        in_app_enabled=in_app_enabled,
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def update_notification_setting(
    db: AsyncSession, *, db_obj: NotificationSettingModel, obj_in: NotificationSettingUpdate
) -> NotificationSettingModel:
    """
    通知設定を更新する
    """
    update_data = obj_in.model_dump(exclude_unset=True) # Pydantic V2
    # update_data = obj_in.dict(exclude_unset=True) # Pydantic V1
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    # 更新後オブジェクトにユーザー情報を再度ロード (必要な場合)
    # stmt = select(NotificationSettingModel).filter_by(id=db_obj.id).options(selectinload(NotificationSettingModel.user))
    # result = await db.execute(stmt)
    # return result.scalars().first()
    return db_obj

# `delete_notification_setting` は通常あまり使われないかもしれませんが、必要であれば追加します。 