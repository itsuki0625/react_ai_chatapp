from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.enums import NotificationType
from app.services.notification_service import NotificationService
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    BulkNotificationCreate
)
from sqlalchemy import select, desc
from app.models.in_app_notification import InAppNotification
from app.schemas.in_app_notification import InAppNotificationResponse

router = APIRouter()

@router.post("/send", response_model=NotificationResponse)
async def send_notification(
    notification: NotificationCreate = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    通知を送信する
    """
    success = await NotificationService.send_notification(
        db=db,
        user_id=notification.user_id,
        notification_type=notification.notification_type,
        title=notification.title,
        message=notification.message,
        metadata=notification.metadata
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="通知の送信に失敗しました")
    
    return NotificationResponse(
        success=True,
        message="通知を送信しました"
    )

@router.post("/send/bulk", response_model=List[NotificationResponse])
async def send_bulk_notification(
    notification: BulkNotificationCreate = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    複数のユーザーに一括で通知を送信する
    """
    results = await NotificationService.send_bulk_notification(
        db=db,
        user_ids=notification.user_ids,
        notification_type=notification.notification_type,
        title=notification.title,
        message=notification.message,
        metadata=notification.metadata
    )
    
    responses = []
    for user_id, success in results.items():
        responses.append(
            NotificationResponse(
                success=success,
                message="通知を送信しました" if success else "通知の送信に失敗しました",
                user_id=user_id
            )
        )
    
    return responses 