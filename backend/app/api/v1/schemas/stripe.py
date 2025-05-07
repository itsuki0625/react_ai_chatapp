from pydantic import BaseModel
from typing import Optional, Dict, Any

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