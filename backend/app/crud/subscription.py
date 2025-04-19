from sqlalchemy.orm import Session
from app.models.subscription import Subscription, SubscriptionPlan, PaymentHistory, CampaignCode
from app.schemas.subscription import SubscriptionCreate, SubscriptionPlanCreate, PaymentHistoryCreate, CampaignCodeCreate, CampaignCodeUpdate
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

# サブスクリプションプランのCRUD操作
def create_subscription_plan(db: Session, plan: SubscriptionPlanCreate):
    db_plan = SubscriptionPlan(**plan.dict())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

def get_subscription_plan(db: Session, plan_id: UUID):
    return db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()

def get_subscription_plan_by_price_id(db: Session, price_id: str):
    return db.query(SubscriptionPlan).filter(SubscriptionPlan.price_id == price_id).first()

def get_all_subscription_plans(db: Session, skip: int = 0, limit: int = 100):
    return db.query(SubscriptionPlan).offset(skip).limit(limit).all()

def get_active_subscription_plans(db: Session):
    return db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True).all()

def update_subscription_plan(db: Session, plan_id: UUID, plan_data: dict):
    db_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if db_plan:
        for key, value in plan_data.items():
            setattr(db_plan, key, value)
        db.commit()
        db.refresh(db_plan)
    return db_plan

# サブスクリプションのCRUD操作
def create_subscription(db: Session, subscription: SubscriptionCreate):
    db_subscription = Subscription(**subscription.dict())
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    return db_subscription

def get_subscription(db: Session, subscription_id: UUID):
    return db.query(Subscription).filter(Subscription.id == subscription_id).first()

def get_user_subscriptions(db: Session, user_id: UUID):
    return db.query(Subscription).filter(Subscription.user_id == user_id).all()

def get_active_user_subscription(db: Session, user_id: UUID):
    return db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.is_active == True,
        Subscription.status.in_(["active", "trialing"])
    ).first()

def get_subscription_by_stripe_id(db: Session, stripe_subscription_id: str):
    return db.query(Subscription).filter(Subscription.stripe_subscription_id == stripe_subscription_id).first()

def update_subscription(db: Session, subscription_id: UUID, subscription_data: dict):
    db_subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if db_subscription:
        for key, value in subscription_data.items():
            setattr(db_subscription, key, value)
        db.commit()
        db.refresh(db_subscription)
    return db_subscription

def cancel_subscription(db: Session, subscription_id: UUID, canceled_at: datetime = None):
    db_subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if db_subscription:
        db_subscription.status = "canceled"
        db_subscription.canceled_at = canceled_at or datetime.utcnow()
        db_subscription.is_active = False
        db.commit()
        db.refresh(db_subscription)
    return db_subscription

# 支払い履歴のCRUD操作
def create_payment_history(db: Session, payment: PaymentHistoryCreate):
    db_payment = PaymentHistory(**payment.dict())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

def get_payment_history(db: Session, payment_id: UUID):
    return db.query(PaymentHistory).filter(PaymentHistory.id == payment_id).first()

def get_user_payment_history(db: Session, user_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(PaymentHistory).filter(
        PaymentHistory.user_id == user_id
    ).order_by(PaymentHistory.payment_date.desc()).offset(skip).limit(limit).all()

def get_payment_by_stripe_id(db: Session, stripe_payment_intent_id: str):
    return db.query(PaymentHistory).filter(
        PaymentHistory.stripe_payment_intent_id == stripe_payment_intent_id
    ).first()

def update_payment_history(db: Session, payment_id: UUID, payment_data: dict):
    db_payment = db.query(PaymentHistory).filter(PaymentHistory.id == payment_id).first()
    if db_payment:
        for key, value in payment_data.items():
            setattr(db_payment, key, value)
        db.commit()
        db.refresh(db_payment)
    return db_payment

# キャンペーンコードのCRUD操作
def create_campaign_code(db: Session, campaign_code: CampaignCodeCreate):
    db_campaign_code = CampaignCode(**campaign_code.dict())
    db.add(db_campaign_code)
    db.commit()
    db.refresh(db_campaign_code)
    return db_campaign_code

def get_campaign_code(db: Session, campaign_code_id: UUID):
    return db.query(CampaignCode).filter(CampaignCode.id == campaign_code_id).first()

def get_campaign_code_by_code(db: Session, code: str):
    return db.query(CampaignCode).filter(CampaignCode.code == code).first()

def get_all_campaign_codes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(CampaignCode).order_by(CampaignCode.created_at.desc()).offset(skip).limit(limit).all()

def get_user_campaign_codes(db: Session, owner_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(CampaignCode).filter(
        CampaignCode.owner_id == owner_id
    ).order_by(CampaignCode.created_at.desc()).offset(skip).limit(limit).all()

def update_campaign_code(db: Session, campaign_code_id: UUID, campaign_code_data: CampaignCodeUpdate):
    db_campaign_code = db.query(CampaignCode).filter(CampaignCode.id == campaign_code_id).first()
    if db_campaign_code:
        update_data = campaign_code_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_campaign_code, key, value)
        db.commit()
        db.refresh(db_campaign_code)
    return db_campaign_code

def increment_campaign_code_usage(db: Session, campaign_code_id: UUID):
    db_campaign_code = db.query(CampaignCode).filter(CampaignCode.id == campaign_code_id).first()
    if db_campaign_code:
        db_campaign_code.used_count += 1
        db.commit()
        db.refresh(db_campaign_code)
    return db_campaign_code

def delete_campaign_code(db: Session, campaign_code_id: UUID):
    db_campaign_code = db.query(CampaignCode).filter(CampaignCode.id == campaign_code_id).first()
    if db_campaign_code:
        db.delete(db_campaign_code)
        db.commit()
        return True
    return False

# キャンペーンコードの検証
def verify_campaign_code(db: Session, code: str, plan_id: UUID) -> Dict[str, Any]:
    db_campaign_code = get_campaign_code_by_code(db, code)
    
    # コードが存在しない場合
    if not db_campaign_code:
        return {
            "valid": False,
            "message": "指定されたキャンペーンコードは存在しません",
            "campaign_code_id": None
        }
    
    # コードが有効かどうかチェック
    if not db_campaign_code.is_valid:
        if not db_campaign_code.is_active:
            return {
                "valid": False,
                "message": "このキャンペーンコードは無効化されています",
                "campaign_code_id": db_campaign_code.id
            }
        
        now = datetime.utcnow()
        if db_campaign_code.valid_from and db_campaign_code.valid_from > now:
            return {
                "valid": False,
                "message": f"このキャンペーンコードは {db_campaign_code.valid_from.strftime('%Y-%m-%d')} から有効になります",
                "campaign_code_id": db_campaign_code.id
            }
            
        if db_campaign_code.valid_until and db_campaign_code.valid_until < now:
            return {
                "valid": False,
                "message": "このキャンペーンコードは期限切れです",
                "campaign_code_id": db_campaign_code.id
            }
            
        if db_campaign_code.max_uses and db_campaign_code.used_count >= db_campaign_code.max_uses:
            return {
                "valid": False,
                "message": "このキャンペーンコードは使用可能回数を超えています",
                "campaign_code_id": db_campaign_code.id
            }
    
    # プランの存在確認
    db_plan = get_subscription_plan(db, plan_id)
    if not db_plan:
        return {
            "valid": False,
            "message": "指定されたプランが見つかりません",
            "campaign_code_id": db_campaign_code.id
        }
    
    # 割引額の計算
    original_amount = db_plan.amount
    discounted_amount = original_amount
    
    if db_campaign_code.discount_type == "percentage":
        discount = original_amount * (db_campaign_code.discount_value / 100)
        discounted_amount = original_amount - int(discount)
    elif db_campaign_code.discount_type == "fixed":
        discounted_amount = original_amount - int(db_campaign_code.discount_value)
        # 割引後の価格が0以下にならないよう調整
        if discounted_amount < 0:
            discounted_amount = 0
    
    return {
        "valid": True,
        "message": "有効なキャンペーンコードです",
        "discount_type": db_campaign_code.discount_type,
        "discount_value": db_campaign_code.discount_value,
        "original_amount": original_amount,
        "discounted_amount": discounted_amount,
        "campaign_code_id": db_campaign_code.id
    } 