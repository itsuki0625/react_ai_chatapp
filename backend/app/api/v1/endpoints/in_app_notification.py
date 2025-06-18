from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.api.deps import get_async_db, get_current_user
from app.models.user import User
from app.models.in_app_notification import InAppNotification
from app.schemas.in_app_notification import (
    InAppNotificationCreate,
    InAppNotificationUpdate,
    InAppNotificationInDB
)

router = APIRouter()

@router.get("/", response_model=List[InAppNotificationInDB])
async def get_in_app_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    stmt = select(InAppNotification).filter(
        InAppNotification.user_id == current_user.id
    ).order_by(InAppNotification.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/", response_model=InAppNotificationInDB)
async def create_in_app_notification(
    notification: InAppNotificationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    db_notification = InAppNotification(
        user_id=str(current_user.id),
        **notification.model_dump()
    )
    db.add(db_notification)
    await db.commit()
    await db.refresh(db_notification)
    return db_notification

@router.patch("/{notification_id}", response_model=InAppNotificationInDB)
async def mark_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    stmt = select(InAppNotification).filter(
        InAppNotification.id == notification_id,
        InAppNotification.user_id == current_user.id
    )
    result = await db.execute(stmt)
    notification = result.scalars().first()
    if not notification:
        raise HTTPException(status_code=404, detail="通知が見つかりません")
    notification.is_read = True
    await db.commit()
    await db.refresh(notification)
    return notification 