from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.push_subscription import PushSubscription
from app.schemas.push_subscription import (
    PushSubscriptionCreate,
    PushSubscriptionUpdate,
    PushSubscriptionInDB
)

router = APIRouter()

@router.post("/subscriptions", response_model=PushSubscriptionInDB)
async def create_push_subscription(
    subscription: PushSubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    プッシュ通知のサブスクリプションを作成する
    """
    db_subscription = PushSubscription(
        user_id=current_user.id,
        **subscription.model_dump()
    )
    db.add(db_subscription)
    await db.commit()
    await db.refresh(db_subscription)
    return db_subscription

@router.get("/subscriptions", response_model=List[PushSubscriptionInDB])
async def get_push_subscriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    ユーザーのプッシュ通知のサブスクリプション一覧を取得する
    """
    stmt = select(PushSubscription).filter(
        PushSubscription.user_id == current_user.id
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.delete("/subscriptions/{subscription_id}")
async def delete_push_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    プッシュ通知のサブスクリプションを削除する
    """
    stmt = select(PushSubscription).filter(
        PushSubscription.id == subscription_id,
        PushSubscription.user_id == current_user.id
    )
    result = await db.execute(stmt)
    subscription = result.scalars().first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="サブスクリプションが見つかりません")
    
    await db.delete(subscription)
    await db.commit()
    return {"message": "サブスクリプションを削除しました"} 