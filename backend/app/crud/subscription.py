from sqlalchemy.orm import Session
from app.models.subscription import Subscription, PaymentHistory, CampaignCode
from app.schemas.subscription import SubscriptionCreate, PaymentHistoryCreate, CampaignCodeCreate, CampaignCodeUpdate
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

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
def verify_campaign_code(db: Session, code: str, price_id: str) -> Dict[str, Any]:
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
    
    # 価格情報の確認は上位層（API）で行われるため、ここでは結果のみを返す
    return {
        "valid": True,
        "message": "有効なキャンペーンコードです",
        "discount_type": db_campaign_code.discount_type,
        "discount_value": db_campaign_code.discount_value,
        "campaign_code_id": db_campaign_code.id
    } 