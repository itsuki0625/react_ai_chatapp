from pydantic import BaseModel, UUID4, Field, validator
from typing import Optional, List
from datetime import datetime

# ベースモデル
class SubscriptionBase(BaseModel):
    plan_name: str
    price_id: str
    status: str = "active"
    campaign_code_id: Optional[UUID4] = None

# 作成リクエスト
class SubscriptionCreate(SubscriptionBase):
    user_id: UUID4

# データベースからの応答
class SubscriptionResponse(SubscriptionBase):
    id: UUID4
    user_id: UUID4
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# サブスクリプションプラン
class SubscriptionPlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    price_id: str
    amount: int
    currency: str = "jpy"
    interval: str
    is_active: bool = True

class SubscriptionPlanCreate(SubscriptionPlanBase):
    pass

class SubscriptionPlanResponse(SubscriptionPlanBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# 支払い履歴
class PaymentHistoryBase(BaseModel):
    user_id: UUID4
    amount: int
    currency: str = "jpy"
    status: str

class PaymentHistoryCreate(PaymentHistoryBase):
    subscription_id: Optional[UUID4] = None
    stripe_payment_intent_id: Optional[str] = None
    stripe_invoice_id: Optional[str] = None
    payment_method: Optional[str] = None
    payment_date: datetime = Field(default_factory=datetime.utcnow)

class PaymentHistoryResponse(PaymentHistoryBase):
    id: UUID4
    subscription_id: Optional[UUID4] = None
    stripe_payment_intent_id: Optional[str] = None
    stripe_invoice_id: Optional[str] = None
    payment_method: Optional[str] = None
    payment_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# キャンペーンコード
class CampaignCodeBase(BaseModel):
    code: str
    description: Optional[str] = None
    discount_type: str  # 'percentage', 'fixed'
    discount_value: float
    max_uses: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool = True

class CampaignCodeCreate(CampaignCodeBase):
    owner_id: Optional[UUID4] = None

    @validator('discount_type')
    def validate_discount_type(cls, v):
        if v not in ['percentage', 'fixed']:
            raise ValueError('discount_typeは "percentage" または "fixed" である必要があります')
        return v
        
    @validator('discount_value')
    def validate_discount_value(cls, v, values):
        if 'discount_type' in values and values['discount_type'] == 'percentage' and (v <= 0 or v > 100):
            raise ValueError('割引率は0より大きく、100以下である必要があります')
        elif v <= 0:
            raise ValueError('割引額は0より大きい必要があります')
        return v

class CampaignCodeResponse(CampaignCodeBase):
    id: UUID4
    owner_id: Optional[UUID4] = None
    used_count: int
    created_at: datetime
    updated_at: datetime
    
    # 有効かどうかの追加フィールド
    is_valid: bool
    
    class Config:
        orm_mode = True

class CampaignCodeUpdate(BaseModel):
    description: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    max_uses: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None
    
    @validator('discount_type')
    def validate_discount_type(cls, v):
        if v and v not in ['percentage', 'fixed']:
            raise ValueError('discount_typeは "percentage" または "fixed" である必要があります')
        return v
        
    @validator('discount_value')
    def validate_discount_value(cls, v, values):
        if v is None:
            return v
            
        discount_type = values.get('discount_type')
        if discount_type == 'percentage' and (v <= 0 or v > 100):
            raise ValueError('割引率は0より大きく、100以下である必要があります')
        elif v <= 0:
            raise ValueError('割引額は0より大きい必要があります')
        return v

# キャンペーンコード検証リクエスト
class VerifyCampaignCodeRequest(BaseModel):
    code: str
    plan_id: UUID4

# キャンペーンコード検証レスポンス
class VerifyCampaignCodeResponse(BaseModel):
    valid: bool
    message: str
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    original_amount: Optional[int] = None
    discounted_amount: Optional[int] = None
    campaign_code_id: Optional[UUID4] = None

# Stripeチェックアウトセッション作成リクエスト（キャンペーンコード対応）
class CreateCheckoutSessionRequest(BaseModel):
    plan_id: UUID4
    success_url: str
    cancel_url: str
    campaign_code: Optional[str] = None

# Stripeチェックアウトセッション応答
class CheckoutSessionResponse(BaseModel):
    session_id: str
    url: str

# サブスクリプション管理リクエスト
class ManageSubscriptionRequest(BaseModel):
    subscription_id: UUID4
    action: str  # "cancel", "reactivate", "update"
    plan_id: Optional[UUID4] = None  # updateの場合に使用

# Webhookイベント検証
class WebhookEventValidation(BaseModel):
    signature: str
    payload: str 