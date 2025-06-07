from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps # 認証・認可のための依存関係 (deps.get_current_active_superuser などがあると仮定)
from app.models.enums import NotificationType # NotificationType をインポート

router = APIRouter()

@router.get(
    "/",
    response_model=schemas.NotificationSettingList, # ページネーション対応のスキーマ
    # dependencies=[Depends(deps.get_current_active_superuser)], # Adminユーザーのみアクセス可能 (コメントアウトして開発中はアクセスしやすくする)
)
async def read_all_notification_settings(
    db: AsyncSession = Depends(deps.get_async_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200), # 1回のリクエストで取得できる最大件数を制限
    user_id: Optional[UUID] = Query(None, description="Filter by User ID"),
) -> Any:
    """
    全ての通知設定を取得します (Admin用)。
    ユーザーIDでフィルタリングも可能です。
    """
    settings = await crud.crud_notification_setting.get_all_notification_settings(
        db, skip=skip, limit=limit, user_id=user_id
    )
    total_count = await crud.crud_notification_setting.get_all_notification_settings_count(
        db, user_id=user_id
    )
    return {"total": total_count, "items": settings}

@router.get(
    "/{setting_id}",
    response_model=schemas.NotificationSettingUser, # ユーザー情報も含むスキーマ
    # dependencies=[Depends(deps.get_current_active_superuser)],
)
async def read_notification_setting_by_id(
    setting_id: UUID,
    db: AsyncSession = Depends(deps.get_async_db),
) -> Any:
    """
    特定の通知設定をIDで取得します (Admin用)。
    """
    setting = await crud.crud_notification_setting.get_notification_setting_by_id(db, setting_id=setting_id)
    if not setting:
        raise HTTPException(status_code=404, detail="Notification setting not found")
    return setting

@router.put(
    "/{setting_id}",
    response_model=schemas.NotificationSettingUser, # 更新後のオブジェクトを返す (ユーザー情報も含む)
    # dependencies=[Depends(deps.get_current_active_superuser)],
)
async def update_notification_setting_by_id(
    setting_id: UUID,
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    setting_in: schemas.NotificationSettingUpdate,
) -> Any:
    """
    特定の通知設定をIDで更新します (Admin用)。
    """
    db_setting = await crud.crud_notification_setting.get_notification_setting_by_id(db, setting_id=setting_id)
    if not db_setting:
        raise HTTPException(
            status_code=404,
            detail="Notification setting not found",
        )
    updated_setting = await crud.crud_notification_setting.update_notification_setting(
        db=db, db_obj=db_setting, obj_in=setting_in
    )
    # 更新後、再度ユーザー情報をロードして返す
    refreshed_setting = await crud.crud_notification_setting.get_notification_setting_by_id(db, setting_id=updated_setting.id)
    if not refreshed_setting: # 念のためチェック
        raise HTTPException(status_code=404, detail="Updated notification setting not found after refresh")
    return refreshed_setting


# --- オプション: 特定ユーザーの通知設定一覧 (Adminがユーザー単位で確認する場合) ---
@router.get(
    "/user/{user_id}",
    response_model=List[schemas.NotificationSetting], # 通常のNotificationSettingのリスト
    # dependencies=[Depends(deps.get_current_active_superuser)],
)
async def read_user_notification_settings(
    user_id: UUID,
    db: AsyncSession = Depends(deps.get_async_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
) -> Any:
    """
    特定のユーザーの通知設定一覧を取得します (Admin用)。
    """
    # crud_user.get_user が存在し、適切に動作すると仮定
    # user = await crud.crud_user.get_user(db, id=user_id) 
    # if not user:
    #     raise HTTPException(status_code=404, detail="User not found")
    
    settings = await crud.crud_notification_setting.get_notification_settings_by_user(
        db, user_id=user_id, skip=skip, limit=limit
    )
    if not settings: # ユーザーは存在するが通知設定がない場合も考慮
        # raise HTTPException(status_code=404, detail="Notification settings not found for this user")
        # 空リストを返すか、404を返すかは要件による
        pass # 空リストを返す
    return settings 