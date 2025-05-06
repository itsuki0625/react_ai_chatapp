from pydantic import BaseModel, Field, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Product Schemas ---

class StripeProductBase(BaseModel):
    name: str = Field(..., description="商品名")
    description: Optional[str] = Field(None, description="商品の説明")
    active: bool = Field(True, description="有効フラグ")
    metadata: Optional[Dict[str, Any]] = Field(None, description="メタデータ")

class StripeProductCreate(StripeProductBase):
    pass

class StripeProductUpdate(BaseModel):
    name: Optional[str] = Field(None, description="商品名")
    description: Optional[str] = Field(None, description="商品の説明")
    active: Optional[bool] = Field(None, description="有効フラグ")
    metadata: Optional[Dict[str, Any]] = Field(None, description="メタデータ")

# Stripe APIからのレスポンス用
class StripeProductResponse(StripeProductBase):
    id: str = Field(..., description="Stripe Product ID")
    # Stripe APIレスポンスはUnixタイムスタンプなので、datetimeに変換するか、
    # Pydantic側でintとして受け取るか、バリデーションで変換処理を入れる
    created: int # Unix timestamp
    updated: int # Unix timestamp
    # object: str = 'product'
    # livemode: bool
    # package_dimensions: Optional[Dict[str, Any]] = None
    # shippable: Optional[bool] = None
    # statement_descriptor: Optional[str] = None
    # tax_code: Optional[str] = None
    # unit_label: Optional[str] = None
    # url: Optional[str] = None

    class Config:
        from_attributes = True # Stripeオブジェクトからの変換を試みる

# --- Price Schemas ---

class StripeRecurring(BaseModel):
    interval: str = Field(..., description="課金間隔 (day, week, month, year)")
    interval_count: int = Field(1, description="課金間隔の数")
    # usage_type: str = 'licensed' # 必要なら追加
    # aggregate_usage: Optional[str] = None
    # trial_period_days: Optional[int] = None

class StripePriceBase(BaseModel):
    unit_amount: Optional[int] = Field(None, description="金額 (最小通貨単位、例: 円)。従量課金の場合はNoneも可") # 従量課金対応
    currency: str = Field(..., description="通貨コード (例: jpy)")
    recurring: Optional[StripeRecurring] = Field(None, description="定期課金設定。Noneの場合は都度払い") # 都度払い対応
    active: bool = Field(True, description="有効フラグ")
    metadata: Optional[Dict[str, Any]] = Field(None, description="メタデータ")
    lookup_key: Optional[str] = Field(None, description="ルックアップキー")
    # nickname: Optional[str] = None
    # tiers_mode: Optional[str] = None
    # billing_scheme: str = 'per_unit'
    # tax_behavior: str = 'unspecified'
    # transform_quantity: Optional[Dict[str, int]] = None

class StripePriceCreate(StripePriceBase):
    product_id: str = Field(..., description="紐付けるStripe Product ID")
    # unit_amount は Base で Optional にしたので必須チェックを外すか、ここで再度必須にする
    unit_amount: int = Field(..., description="金額 (最小通貨単位、例: 円)") # 作成時は必須とする場合
    recurring: StripeRecurring = Field(..., description="定期課金設定") # 作成時は必須とする場合

class StripePriceUpdate(BaseModel):
    active: Optional[bool] = Field(None, description="有効フラグ")
    metadata: Optional[Dict[str, Any]] = Field(None, description="メタデータ")
    lookup_key: Optional[str] = Field(None, description="ルックアップキー")
    # nickname: Optional[str] = None
    # tax_behavior: Optional[str] = None

# Stripe APIからのレスポンス用
class StripePriceResponse(StripePriceBase):
    id: str = Field(..., description="Stripe Price ID")
    product: str = Field(..., description="紐づくStripe Product ID")
    created: int # Unix timestamp
    livemode: bool
    type: str # 'recurring' or 'one_time'
    # object: str = 'price'

    class Config:
        from_attributes = True

# get_products のレスポンス用（価格情報を含む）
class StripeProductWithPricesResponse(StripeProductResponse):
     prices: List[StripePriceResponse] = [] 

# +++ Stripe Coupon リスト取得用フィルタモデル +++
class StripeCouponListFilter(BaseModel):
    limit: int = Field(10, ge=1, le=100, description="取得する最大件数")
    starting_after: Optional[str] = Field(None, description="このID以降のオブジェクトを取得 (ページネーション用)")
    ending_before: Optional[str] = Field(None, description="このID以前のオブジェクトを取得 (ページネーション用)")
    created_gte: Optional[datetime] = Field(None, description="作成日時 (これ以降)")
    created_lte: Optional[datetime] = Field(None, description="作成日時 (これ以前)")
    # 必要に応じて他のStripe Coupon List APIのパラメータを追加
    # 例: currency: Optional[str] = None

    # ★ Pydantic V2 の model_config を使用
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "limit": 20,
                    "created_gte": "2023-10-26T10:00:00Z",
                    "starting_after": "coupon_xxxxxxxxxxxx"
                }
            ]
        }
    }

# ─────────────────────────────────────────────────────────
# Stripe API から返却される生の Coupon オブジェクト用スキーマ
class StripeApiCouponResponse(BaseModel):
    """
    Stripe API から返却される生の Coupon オブジェクト用スキーマ
    """
    id: str
    object: str
    amount_off: Optional[int] = None
    currency: Optional[str] = None
    percent_off: Optional[float] = None
    name: Optional[str] = None
    duration: str
    duration_in_months: Optional[int] = None
    redeem_by: Optional[int] = None
    times_redeemed: int
    valid: bool
    livemode: bool
    metadata: Dict[str, Any] = {}
    applies_to: Optional[Dict[str, Any]] = None
# ─────────────────────────────────────────────────────────

# +++ ここまで +++ 