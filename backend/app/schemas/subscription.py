from pydantic import BaseModel, UUID4, Field, validator
from pydantic import computed_field
from typing import Optional, List, Any, Dict
from datetime import datetime
from uuid import UUID
from .base import TimestampMixin

# ベースモデル
class SubscriptionBase(BaseModel):
    user_id: UUID
    plan_name: str
    price_id: Optional[str] = None
    status: str
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    is_active: bool = True

# 作成リクエスト
class SubscriptionCreate(SubscriptionBase):
    pass

# データベースからの応答
class SubscriptionResponse(SubscriptionBase, TimestampMixin):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# サブスクリプションプラン (Stripeから直接取得するためDBモデルなし)
class SubscriptionPlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    price_id: str  # Stripeの価格ID
    amount: int
    currency: str = "jpy"
    interval: str
    is_active: bool = True

class SubscriptionPlanCreate(SubscriptionPlanBase):
    pass

class SubscriptionPlanResponse(SubscriptionPlanBase):
    id: str  # Stripe連携のため、StringとしてIDを保持（価格IDと同じ値）
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = False  # DBモデルと紐づかないため、Falseに変更

# 支払い履歴
class PaymentHistoryBase(BaseModel):
    user_id: UUID
    subscription_id: UUID
    stripe_payment_intent_id: Optional[str] = None
    stripe_invoice_id: Optional[str] = None
    amount: int
    currency: str
    payment_date: datetime
    status: str
    description: Optional[str] = None

class PaymentHistoryCreate(PaymentHistoryBase):
    pass

class PaymentHistoryResponse(PaymentHistoryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- ★ Stripe Coupon Schemas --- 
class StripeCouponBase(BaseModel):
    # stripe_coupon_id: str # DB 登録後に付与されるので Base には含めない
    name: Optional[str] = None
    amount_off: Optional[int] = None
    percent_off: Optional[float] = None
    currency: Optional[str] = None # ★ 追加 (amount_off とセットで必要)
    duration: str # 'forever', 'once', 'repeating'
    duration_in_months: Optional[int] = None # duration='repeating' の場合必須
    redeem_by: Optional[int] = None # Unix timestamp
    metadata: Optional[Dict[str, Any]] = None
    livemode: Optional[bool] = None # Stripe API から取得時に設定

    # --- DB に保存するか検討するフィールド ---
    # max_redemptions: Optional[int] = None
    # valid: Optional[bool] = None # Stripe 側で管理
    # times_redeemed: Optional[int] = None # Stripe 側で管理

class StripeCouponCreate(StripeCouponBase):
    # ★ DB 登録時には stripe_coupon_id は不要だが、
    #    Stripe API 作成 -> DB 登録 の流れでは、API 作成後に ID が決まる。
    #    エンドポイント側で API レスポンスから設定するため、Create スキーマには含めないか、
    #    あるいは Optional にしておく。ここでは含めない方針とする。
    stripe_coupon_id: Optional[str] = Field(None, description="Stripe API で作成後に設定されます。入力不要。")

    # バリデーションを追加しても良い (例: amount_off と currency はセット、percent_off と排他など)

class StripeCouponUpdate(BaseModel):
    # 更新可能なフィールドを定義 (例: metadata, name)
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    # 注意: Stripe Coupon の主要な属性 (割引額、期間など) は一度作成すると変更できないことが多い

class StripeCouponResponse(StripeCouponBase):
    id: UUID # DB の UUID
    stripe_coupon_id: str # Stripe の Coupon ID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # ORM モデルからの変換を有効化

# --- Campaign Code Schemas (修正) --- 
class CampaignCodeBase(BaseModel):
    code: str = Field(..., max_length=255)
    description: Optional[str] = None
    max_uses: Optional[int] = Field(None, ge=1)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool = True

class CampaignCodeCreate(CampaignCodeBase):
    # stripe_coupon_id: str # ← 文字列のStripe IDではなくDBのIDを使う
    # coupon_id: UUID # ★ 紐付ける StripeCoupon テーブルの UUID (必須)
    stripe_coupon_id: str = Field(..., description="紐付けるStripe CouponのID") # ★ 修正: Stripe Coupon ID を直接受け取る

class CampaignCodeUpdate(BaseModel):
    description: Optional[str] = None
    max_uses: Optional[int] = Field(None, ge=1)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None
    # code, coupon_id の更新は許可しない想定

class CampaignCodeResponse(CampaignCodeBase):
    id: UUID
    used_count: int = 0
    stripe_promotion_code_id: Optional[str] = None
    coupon_id: UUID # ★ 紐づく Coupon の DB ID
    # coupon: Optional[StripeCouponResponse] = None # ★ ネストして返す場合 (要 selectinload)
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None

    class Config:
        from_attributes = True

# --- Verify Campaign Code (修正) --- 
class VerifyCampaignCodeRequest(BaseModel):
    code: str
    price_id: str

class VerifyCampaignCodeResponse(BaseModel):
    valid: bool
    message: str
    campaign_code_id: Optional[UUID] = None
    coupon_id: Optional[UUID] = None # ★ Coupon の DB ID を返す
    stripe_coupon_id: Optional[str] = None # ★ Stripe Coupon IDも返すように変更
    # coupon: Optional[StripeCouponResponse] = None # ★ ネストして返す場合

# --- Checkout Session (修正) ---
class CreateCheckoutRequest(BaseModel):
    price_id: str
    plan_id: Optional[str] = None
    success_url: str
    cancel_url: str
    # campaign_code: Optional[str] = None # ← 文字列ではなく Coupon ID を受け取る
    coupon_id: Optional[str] = None # ★ 適用する Stripe Coupon ID を受け取る

class CheckoutSessionResponse(BaseModel):
    session_id: str
    url: str

# サブスクリプション管理リクエスト
class ManageSubscriptionRequest(BaseModel):
    action: str # 'cancel', 'reactivate', 'update'
    subscription_id: Optional[str] = None # update時に必要
    plan_id: Optional[str] = None # update時に必要

# Webhookイベント検証
class WebhookEventValidation(BaseModel):
    signature: str
    payload: str 

# --- Discount Type Schemas (現状維持または削除検討) ---
class DiscountTypeBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    is_percentage: bool

class DiscountTypeCreate(DiscountTypeBase):
    pass

class DiscountTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    is_percentage: Optional[bool] = None

class DiscountTypeResponse(DiscountTypeBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 