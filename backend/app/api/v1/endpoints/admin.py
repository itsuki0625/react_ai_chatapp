from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import stripe

from app.core.config import settings
from app.api.deps import get_db
from app.api.deps import get_current_superuser
from app.schemas.subscription import (
    CampaignCodeCreate, 
    CampaignCodeResponse,
    SubscriptionPlanCreate,
    SubscriptionPlanResponse
)
from app.crud.subscription import (
    create_campaign_code,
    get_campaign_code,
    get_all_campaign_codes,
    update_campaign_code,
    delete_campaign_code,
    create_subscription_plan,
    get_subscription_plan,
    get_all_subscription_plans,
    update_subscription_plan
)

router = APIRouter(tags=["admin"])

# Stripeインスタンスの初期化
stripe.api_key = settings.STRIPE_SECRET_KEY

# ---------- 商品関連のエンドポイント ---------- #

@router.get("/products", response_model=List[dict])
def get_products(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_superuser),
):
    """
    Stripe商品一覧を取得する
    """
    try:
        # Stripe商品一覧を取得
        products = stripe.Product.list(active=True)
        
        # 価格情報も取得して商品情報と結合
        result = []
        for product in products.data:
            prices = stripe.Price.list(product=product.id, active=True)
            product_data = {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "active": product.active,
                "prices": [
                    {
                        "id": price.id,
                        "currency": price.currency,
                        "unit_amount": price.unit_amount,
                        "recurring": price.recurring if hasattr(price, "recurring") else None
                    }
                    for price in prices.data
                ]
            }
            result.append(product_data)
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe商品の取得に失敗しました: {str(e)}"
        )

@router.post("/products", status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_superuser)
):
    """
    Stripeに新しい商品を作成します。
    管理者専用エンドポイント。
    """
    try:
        name = product_data.get("name")
        description = product_data.get("description")
        images = product_data.get("images", [])
        
        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="商品名は必須です"
            )
            
        product = stripe.Product.create(
            name=name,
            description=description,
            images=images
        )
        
        return {"data": product}
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe API エラー: {str(e)}"
        )

@router.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    current_user: Dict = Depends(get_current_superuser)
):
    """
    Stripeから商品を削除します。
    管理者専用エンドポイント。
    """
    try:
        product = stripe.Product.delete(product_id)
        return {"data": product}
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe API エラー: {str(e)}"
        )

# ---------- 価格関連のエンドポイント ---------- #

@router.get("/prices")
async def get_prices(current_user: Dict = Depends(get_current_superuser)):
    """
    Stripeから価格一覧を取得します。
    管理者専用エンドポイント。
    """
    try:
        prices = stripe.Price.list(
            limit=100,
            expand=['data.product']
        )
        
        # 商品名を追加
        prices_with_product_name = []
        for price in prices.data:
            if hasattr(price, 'product') and price.product:
                product_name = price.product.name if hasattr(price.product, 'name') else 'Unknown Product'
            else:
                product_name = 'Unknown Product'
                
            price_dict = dict(price)
            price_dict['product_name'] = product_name
            prices_with_product_name.append(price_dict)
            
        return {"data": prices_with_product_name}
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe API エラー: {str(e)}"
        )

@router.post("/prices", status_code=status.HTTP_201_CREATED)
async def create_price(
    price_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_superuser)
):
    """
    Stripeに新しい価格を作成します。
    管理者専用エンドポイント。
    """
    try:
        product = price_data.get("product")
        unit_amount = price_data.get("unit_amount")
        currency = price_data.get("currency", "jpy")
        recurring = price_data.get("recurring")
        metadata = price_data.get("metadata", {})
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="商品IDは必須です"
            )
            
        if not unit_amount or not isinstance(unit_amount, (int, float)) or unit_amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="有効な価格を指定してください"
            )
            
        price_data = {
            "product": product,
            "unit_amount": int(unit_amount),  # Stripeは整数値を期待
            "currency": currency,
            "metadata": metadata
        }
        
        if recurring:
            price_data["recurring"] = recurring
            
        price = stripe.Price.create(**price_data)
        
        return {"data": price}
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe API エラー: {str(e)}"
        )

@router.delete("/prices/{price_id}")
async def delete_price(
    price_id: str,
    current_user: Dict = Depends(get_current_superuser)
):
    """
    Stripeから価格を削除（非アクティブ化）します。
    管理者専用エンドポイント。
    """
    try:
        # Stripeでは価格の削除はできないため、非アクティブ化する
        price = stripe.Price.modify(
            price_id,
            active=False
        )
        return {"data": price}
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe API エラー: {str(e)}"
        )

# ---------- キャンペーンコード関連のエンドポイント ---------- #

@router.get("/campaign-codes", response_model=List[CampaignCodeResponse])
async def admin_get_campaign_codes(
    skip: int = 0,
    limit: int = 100,
    owner_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_superuser)
):
    """
    キャンペーンコード一覧を取得します。
    管理者専用エンドポイント。
    """
    if owner_id:
        from uuid import UUID
        campaign_codes = get_all_campaign_codes(db, skip=skip, limit=limit, owner_id=UUID(owner_id))
    else:
        campaign_codes = get_all_campaign_codes(db, skip=skip, limit=limit)
    return campaign_codes

@router.post("/campaign-codes", response_model=CampaignCodeResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_campaign_code(
    campaign_code: CampaignCodeCreate,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_superuser)
):
    """
    新しいキャンペーンコードを作成します。
    管理者専用エンドポイント。
    """
    return create_campaign_code(db, campaign_code)

@router.delete("/campaign-codes/{campaign_code_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_campaign_code(
    campaign_code_id: str,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_superuser)
):
    """
    キャンペーンコードを削除します。
    管理者専用エンドポイント。
    """
    from uuid import UUID
    delete_campaign_code(db, UUID(campaign_code_id))
    return None 