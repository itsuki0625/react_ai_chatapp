from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from fastapi import HTTPException

from app.models.subscription import Subscription, PaymentHistory, CampaignCode, DiscountType
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionCreate,
    PaymentHistoryCreate,
    CampaignCodeCreate,
    CampaignCodeUpdate,
    DiscountTypeCreate,
    DiscountTypeUpdate,
)

# --- サブスクリプションのCRUD操作 ---
async def create_subscription(db: AsyncSession, subscription: SubscriptionCreate) -> Subscription:
    db_subscription = Subscription(**subscription.dict())
    db.add(db_subscription)
    await db.commit()
    await db.refresh(db_subscription)
    return db_subscription

async def get_subscription(db: AsyncSession, subscription_id: UUID) -> Optional[Subscription]:
    result = await db.execute(select(Subscription).filter(Subscription.id == subscription_id))
    return result.scalars().first()

async def get_user_subscriptions(db: AsyncSession, user_id: UUID) -> List[Subscription]:
    result = await db.execute(select(Subscription).filter(Subscription.user_id == user_id))
    return result.scalars().all()

async def get_active_user_subscription(db: AsyncSession, user_id: UUID) -> Optional[Subscription]:
    result = await db.execute(
        select(Subscription)
        .filter(
            Subscription.user_id == user_id,
            Subscription.is_active == True,
            Subscription.status.in_( ["active", "trialing"] ),
        )
    )
    return result.scalars().first()

async def get_subscription_by_stripe_id(db: AsyncSession, stripe_subscription_id: str) -> Optional[Subscription]:
    result = await db.execute(
        select(Subscription).filter(Subscription.stripe_subscription_id == stripe_subscription_id)
    )
    return result.scalars().first()

async def update_subscription(db: AsyncSession, subscription_id: UUID, subscription_data: dict) -> Optional[Subscription]:
    subscription = await get_subscription(db, subscription_id)
    if subscription:
        for key, value in subscription_data.items():
            setattr(subscription, key, value)
        await db.commit()
        await db.refresh(subscription)
    return subscription

async def cancel_subscription(db: AsyncSession, subscription_id: UUID, canceled_at: datetime = None) -> Optional[Subscription]:
    subscription = await get_subscription(db, subscription_id)
    if subscription:
        subscription.status = "canceled"
        subscription.canceled_at = canceled_at or datetime.utcnow()
        subscription.is_active = False
        await db.commit()
        await db.refresh(subscription)
    return subscription

# --- 支払い履歴のCRUD操作 ---
async def create_payment_history(db: AsyncSession, payment: PaymentHistoryCreate) -> PaymentHistory:
    db_payment = PaymentHistory(**payment.dict())
    db.add(db_payment)
    await db.commit()
    await db.refresh(db_payment)
    return db_payment

async def get_payment_history(db: AsyncSession, payment_id: UUID) -> Optional[PaymentHistory]:
    result = await db.execute(
        select(PaymentHistory).filter(PaymentHistory.id == payment_id)
    )
    return result.scalars().first()

async def get_user_payment_history(db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 100) -> List[PaymentHistory]:
    result = await db.execute(
        select(PaymentHistory)
        .filter(PaymentHistory.user_id == user_id)
        .order_by(PaymentHistory.payment_date.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_payment_by_stripe_id(db: AsyncSession, stripe_payment_intent_id: str) -> Optional[PaymentHistory]:
    result = await db.execute(
        select(PaymentHistory).filter(PaymentHistory.stripe_payment_intent_id == stripe_payment_intent_id)
    )
    return result.scalars().first()

async def update_payment_history(db: AsyncSession, payment_id: UUID, payment_data: dict) -> Optional[PaymentHistory]:
    payment = await get_payment_history(db, payment_id)
    if payment:
        for key, value in payment_data.items():
            setattr(payment, key, value)
        await db.commit()
        await db.refresh(payment)
    return payment

# --- キャンペーンコードのCRUD操作 ---
async def create_campaign_code(db: AsyncSession, campaign_code: CampaignCodeCreate, creator: User) -> CampaignCode:
    discount_type_name = campaign_code.discount_type
    result = await db.execute(
        select(DiscountType).filter(DiscountType.name == discount_type_name)
    )
    db_discount_type = result.scalars().first()
    if not db_discount_type:
        raise HTTPException(status_code=400, detail=f"Discount type '{discount_type_name}' not found")
    db_campaign_code = CampaignCode(
        code=campaign_code.code,
        description=campaign_code.description,
        discount_type_id=db_discount_type.id,
        discount_value=campaign_code.discount_value,
        max_uses=campaign_code.max_uses,
        valid_from=campaign_code.valid_from,
        valid_until=campaign_code.valid_until,
        is_active=campaign_code.is_active,
        created_by=creator.id
    )
    db.add(db_campaign_code)
    await db.commit()
    await db.refresh(db_campaign_code)
    return db_campaign_code

async def get_campaign_code(db: AsyncSession, campaign_code_id: UUID) -> Optional[CampaignCode]:
    result = await db.execute(
        select(CampaignCode).filter(CampaignCode.id == campaign_code_id)
    )
    return result.scalars().first()

async def get_campaign_code_by_code(db: AsyncSession, code: str) -> Optional[CampaignCode]:
    result = await db.execute(
        select(CampaignCode).filter(CampaignCode.code == code)
    )
    return result.scalars().first()

async def get_all_campaign_codes(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[CampaignCode]:
    result = await db.execute(
        select(CampaignCode)
        .order_by(CampaignCode.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_user_campaign_codes(db: AsyncSession, owner_id: UUID, skip: int = 0, limit: int = 100) -> List[CampaignCode]:
    result = await db.execute(
        select(CampaignCode)
        .filter(CampaignCode.owner_id == owner_id)
        .order_by(CampaignCode.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def update_campaign_code(db: AsyncSession, campaign_code_id: UUID, campaign_code_data: CampaignCodeUpdate) -> Optional[CampaignCode]:
    campaign_code = await get_campaign_code(db, campaign_code_id)
    if campaign_code:
        update_data = campaign_code_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(campaign_code, key, value)
        await db.commit()
        await db.refresh(campaign_code)
    return campaign_code

async def increment_campaign_code_usage(db: AsyncSession, campaign_code_id: UUID) -> Optional[CampaignCode]:
    campaign_code = await get_campaign_code(db, campaign_code_id)
    if campaign_code:
        campaign_code.used_count += 1
        await db.commit()
        await db.refresh(campaign_code)
    return campaign_code

async def delete_campaign_code(db: AsyncSession, campaign_code_id: UUID) -> bool:
    campaign_code = await get_campaign_code(db, campaign_code_id)
    if campaign_code:
        db.delete(campaign_code)
        await db.commit()
        return True
    return False

async def verify_campaign_code(db: AsyncSession, code: str, price_id: str) -> Dict[str, Any]:
    campaign_code = await get_campaign_code_by_code(db, code)
    if not campaign_code:
        return {"valid": False, "message": "指定されたキャンペーンコードは存在しません", "campaign_code_id": None}
    if not campaign_code.is_valid:
        if not campaign_code.is_active:
            return {"valid": False, "message": "このキャンペーンコードは無効化されています", "campaign_code_id": campaign_code.id}
        now = datetime.utcnow()
        if campaign_code.valid_from and campaign_code.valid_from > now:
            return {"valid": False, "message": f"このキャンペーンコードは {campaign_code.valid_from.strftime('%Y-%m-%d')} から有効になります", "campaign_code_id": campaign_code.id}
        if campaign_code.valid_until and campaign_code.valid_until < now:
            return {"valid": False, "message": "このキャンペーンコードは期限切れです", "campaign_code_id": campaign_code.id}
        if campaign_code.max_uses and campaign_code.used_count >= campaign_code.max_uses:
            return {"valid": False, "message": "このキャンペーンコードは使用可能回数を超えています", "campaign_code_id": campaign_code.id}
    return {"valid": True, "message": "有効なキャンペーンコードです", "discount_type": campaign_code.discount_type, "discount_value": campaign_code.discount_value, "campaign_code_id": campaign_code.id}

# --- DiscountType の CRUD 操作 ---
async def get_discount_type(db: AsyncSession, discount_type_id: UUID) -> Optional[DiscountType]:
    result = await db.execute(
        select(DiscountType).filter(DiscountType.id == discount_type_id)
    )
    return result.scalars().first()

async def get_discount_type_by_name(db: AsyncSession, name: str) -> Optional[DiscountType]:
    result = await db.execute(
        select(DiscountType).filter(DiscountType.name == name)
    )
    return result.scalars().first()

async def get_all_discount_types(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[DiscountType]:
    result = await db.execute(
        select(DiscountType).offset(skip).limit(limit)
    )
    return result.scalars().all()

async def create_discount_type(db: AsyncSession, discount_type: DiscountTypeCreate) -> DiscountType:
    existing = await get_discount_type_by_name(db, discount_type.name)
    if existing:
        raise HTTPException(status_code=400, detail=f"Discount type with name '{discount_type.name}' already exists.")
    db_discount_type = DiscountType(**discount_type.model_dump())
    db.add(db_discount_type)
    await db.commit()
    await db.refresh(db_discount_type)
    return db_discount_type

async def update_discount_type(db: AsyncSession, discount_type_id: UUID, discount_type_data: DiscountTypeUpdate) -> Optional[DiscountType]:
    discount_type = await get_discount_type(db, discount_type_id)
    if not discount_type:
        return None
    update_data = discount_type_data.model_dump(exclude_unset=True)
    if "name" in update_data:
        existing = await get_discount_type_by_name(db, update_data["name"])
        if existing and existing.id != discount_type_id:
            raise HTTPException(status_code=400, detail=f"Discount type with name '{update_data['name']}' already exists.")
    for key, value in update_data.items():
        setattr(discount_type, key, value)
    await db.commit()
    await db.refresh(discount_type)
    return discount_type

async def delete_discount_type(db: AsyncSession, discount_type_id: UUID) -> bool:
    discount_type = await get_discount_type(db, discount_type_id)
    if not discount_type:
        return False
    db.delete(discount_type)
    await db.commit()
    return True

# --- Stripe顧客ID 操作 ---
async def get_stripe_customer_id(db: AsyncSession, user_id: UUID) -> Optional[str]:
    subscription = await get_active_user_subscription(db, user_id)
    if subscription:
        return subscription.stripe_customer_id
    return None

async def update_stripe_customer_id(db: AsyncSession, user_id: UUID, stripe_customer_id: str) -> bool:
    subscription = await get_active_user_subscription(db, user_id)
    if subscription:
        subscription.stripe_customer_id = stripe_customer_id
        await db.commit()
        await db.refresh(subscription)
        return True
    return False