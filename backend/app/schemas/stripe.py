from pydantic import BaseModel, Field, UUID4, model_validator, computed_field, AliasChoices
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# --- Product Schemas ---

class StripeProductBaseModel(BaseModel):
    name: str = Field(..., description="商品名")
    description: Optional[str] = Field(None, description="商品の説明")
    active: bool = Field(True, description="有効フラグ")
    metadata: Optional[Dict[str, str]] = Field(None, description="メタデータ (キーも値も文字列)")

class StripeProductCreate(StripeProductBaseModel):
    pass

class StripeProductUpdate(BaseModel):
    name: Optional[str] = Field(None, description="商品名")
    description: Optional[str] = Field(None, description="商品の説明")
    active: Optional[bool] = Field(None, description="有効フラグ")
    metadata: Optional[Dict[str, str]] = Field(None, description="メタデータ (キーも値も文字列)")

# Stripe APIからのレスポンス用
class StripeProductResponse(StripeProductBaseModel):
    id: str = Field(..., description="Stripe Product ID")
    created: int # Unix timestamp
    updated: int # Unix timestamp
    assigned_role_name: Optional[str] = Field(None, description="購入後に割り当てるロール名")

    @model_validator(mode='before')
    @classmethod
    def extract_assigned_role(cls, data: Any) -> Any:
        logger.debug(f"StripeProductResponse validator: incoming data for product ID {data.get('id', 'N/A')}: {data}")
        if isinstance(data, dict):
            metadata = data.get('metadata')
            if isinstance(metadata, dict):
                assigned_role = metadata.get('assigned_role')
                data['assigned_role_name'] = assigned_role
                logger.debug(f"StripeProductResponse validator: product ID {data.get('id', 'N/A')}, assigned_role_name set to: {assigned_role}")
            else:
                logger.debug(f"StripeProductResponse validator: product ID {data.get('id', 'N/A')}, metadata is not a dict or is None: {metadata}")
        else:
            logger.debug(f"StripeProductResponse validator: incoming data is not a dict: {type(data)}")
        return data

    class Config:
        from_attributes = True

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
    metadata: Optional[Dict[str, str]] = Field(None, description="メタデータ")
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
    metadata: Optional[Dict[str, str]] = Field(None, description="メタデータ")
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

# --- Stripe DB Product Schemas (For DB interaction) ---
class StripeDbProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    active: bool = True
    # metadata_: Optional[Dict[str, Any]] = Field(None, alias="metadata") # Baseから削除

    class Config:
        populate_by_name = True

    # @model_validator(mode='before') # 前回のバリデータは削除またはコメントアウト
    # @classmethod
    # def ensure_metadata_is_dict(cls, data: Any) -> Any:
    #     ...

class StripeDbProductCreate(StripeDbProductBase):
    stripe_product_id: str
    metadata: Optional[Dict[str, Any]] = Field(None, validation_alias=AliasChoices('metadata', 'metadata_'))

class StripeDbProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = Field(None, validation_alias=AliasChoices('metadata', 'metadata_'))

    class Config:
        populate_by_name = True

class StripeDbProductResponse(StripeDbProductBase):
    id: UUID4
    stripe_product_id: str
    created_at: datetime
    updated_at: datetime

    @computed_field # type: ignore[misc]
    @property
    def metadata(self) -> Optional[Dict[str, Any]]:
        # SQLAlchemyモデルインスタンス(self)のmetadata_属性を取得することを想定
        actual_metadata_obj = getattr(self, 'metadata_', None)
        if actual_metadata_obj is not None:
            if isinstance(actual_metadata_obj, dict):
                return actual_metadata_obj
            try:
                return dict(actual_metadata_obj)
            except (TypeError, ValueError):
                # 変換に失敗した場合、エラー情報を含む辞書を返すか、Noneを返すか、
                # あるいは例外を発生させることを検討。
                # ここでは、問題の特定のためにエラー情報を含む辞書を返す。
                return {"serialization_error": "metadata could not be converted to dict"}
        return None

    class Config:
        from_attributes = True
        populate_by_name = True

# Potentially update SubscriptionPlan schemas if needed
# For example, if SubscriptionPlanCreate now needs stripe_db_product_id
# from .subscription import SubscriptionPlanBase # Assuming SubscriptionPlanBase is in subscription.py

# class SubscriptionPlanCreateDB(SubscriptionPlanBase): # Example, adjust as needed
#     stripe_db_product_id: UUID4

# class SubscriptionPlanResponseDB(SubscriptionPlanBase):
#     id: UUID4
#     stripe_db_product_id: UUID4
#     created_at: datetime
#     updated_at: datetime
#     class Config:
#         from_attributes = True

# +++ ここまで +++ 