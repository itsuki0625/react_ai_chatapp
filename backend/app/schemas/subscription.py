from pydantic import BaseModel, UUID4, Field, validator, field_validator
from pydantic import computed_field
from typing import Optional, List, Any, Dict
from datetime import datetime
from uuid import UUID
from .base import TimestampMixin

# ベースモデル
class SubscriptionBase(BaseModel):
    user_id: UUID
    plan_id: UUID
    plan_name: Optional[str] = None
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


# --- DB 操作用の SubscriptionPlan スキーマ ---
class SubscriptionPlanDbBase(BaseModel):
    name: str = Field(..., description="プラン名")
    description: Optional[str] = Field(None, description="プランの説明")
    price_id: str = Field(..., description="対応するStripe Price ID")
    stripe_db_product_id: UUID = Field(..., description="紐づくStripeDbProductのDB ID")
    amount: int = Field(..., description="金額 (最小通貨単位)")
    currency: str = Field(default="jpy", description="通貨コード")
    interval: str = Field(..., description="課金間隔 (例: month, year)")
    interval_count: int = Field(default=1, description="課金間隔の数値")
    is_active: bool = Field(default=True, description="有効フラグ")
    features: Optional[List[str]] = Field(None, description="プランのフィーチャーリスト")
    plan_metadata: Optional[Dict[str, Any]] = Field(None, description="プラン固有のメタデータ")
    trial_days: Optional[int] = Field(None, description="トライアル日数")

class SubscriptionPlanCreate(SubscriptionPlanDbBase):
    # SubscriptionPlanDbBaseに必要なフィールドが全て含まれていれば、追加フィールドは不要
    pass

class SubscriptionPlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    features: Optional[List[str]] = None
    plan_metadata: Optional[Dict[str, Any]] = None
    trial_days: Optional[int] = None
    # price_id, stripe_db_product_id, amount, currency, interval, interval_count は通常更新不可とする

class SubscriptionPlanResponse(SubscriptionPlanDbBase):
    id: UUID # DBのUUID
    created_at: datetime
    updated_at: datetime
    # 必要であれば、紐づくStripeDbProductの情報などをネストして含めることも可能

    class Config:
        from_attributes = True

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
    redeem_by: Optional[int] = Field(None, alias='redeem_by_timestamp', description="Unix timestamp for when the coupon expires. Maps to model's redeem_by_timestamp.")
    metadata: Optional[Dict[str, Any]] = Field(None, alias='metadata_', description="Metadata for the coupon. Maps to model's metadata_ attribute.")
    livemode: Optional[bool] = None # Stripe API から取得時に設定

    # --- DB に保存するフィールドを追加 ---
    max_redemptions: Optional[int] = None
    valid: Optional[bool] = None # Stripe APIレスポンスの valid をDBに保存
    times_redeemed: Optional[int] = Field(0, description="Stripe APIレスポンスの times_redeemed をDBに保存 (新規作成時は通常0)")
    created: Optional[int] = Field(None, alias='stripe_created_timestamp', description="Stripe object creation timestamp (Unix). Maps to model's stripe_created_timestamp.")

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
    
    # TimestampMixinからのフィールドを明示的に追加する場合
    db_created_at: datetime = Field(alias="created_at") # DBレコードの作成日時
    db_updated_at: datetime = Field(alias="updated_at") # DBレコードの更新日時

    # metadata が辞書でない場合（例: MetaDataオブジェクト）に辞書に変換するバリデータ
    @field_validator('metadata', mode='before')
    @classmethod
    def convert_metadata_to_dict(cls, v: Any) -> Optional[Dict[str, Any]]:
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        # MetaData() のようなオブジェクトを辞書に変換する試み (もし属性があれば)
        # 実際の MetaData オブジェクトの構造に合わせて調整が必要な場合がある
        if hasattr(v, '__dict__'): # 最も単純な辞書変換
            try:
                # 辞書に変換可能な属性を持つか？
                # もしくは、特定のメソッド（例: .to_dict()）を持つか？
                # ここでは単純に __dict__ を試す
                return dict(v.__dict__)
            except Exception:
                # 変換に失敗した場合は None または空の辞書を返すか、エラーにする
                return {}
        # その他の予期しない型の場合は空の辞書かNoneを返す
        return {}

    class Config:
        from_attributes = True # ORM モデルからの変換を有効化
        populate_by_name = True # alias を有効にするため

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

    # --- フロントエンド表示用の割引情報を追加 ---
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None # 割引率(%) または 割引額(基本通貨単位)
    original_amount: Optional[int] = None  # 割引前の金額 (基本通貨単位)
    discounted_amount: Optional[int] = None # 割引後の金額 (基本通貨単位)

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
