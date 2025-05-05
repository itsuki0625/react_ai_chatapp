from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
import stripe # エラーハンドリング用に追加
import logging # ロギング用に追加
from uuid import UUID
from pydantic import BaseModel, Field # ★ BaseModel と Field をインポート

from app.core.config import settings
from app.api.deps import get_db
from app.api.deps import require_permission
from app.services.stripe_service import StripeService # StripeServiceをインポート
# Pydanticスキーマのインポート (後で追加する可能性あり)
# from app.schemas.stripe import ProductCreate, ProductUpdate, PriceCreate, PriceUpdate # 例

from app.schemas.subscription import (
    CampaignCodeCreate, 
    CampaignCodeResponse,
    DiscountTypeCreate, DiscountTypeResponse, DiscountTypeUpdate,
    StripeCouponCreate, StripeCouponUpdate, StripeCouponResponse
)
from app.crud.subscription import (
    create_campaign_code,
    get_campaign_code,
    get_all_campaign_codes,
    update_campaign_code,
    delete_campaign_code,
    create_discount_type, get_all_discount_types, get_discount_type,
    update_discount_type, delete_discount_type, get_discount_type_by_name,
    create_db_coupon,
    get_db_coupon,
    get_all_db_coupons,
    update_db_coupon,
    get_db_coupon_by_stripe_id
)
from app.crud.user import get_multi_users, remove_user, create_user, get_user, update_user, get_user_by_email
from app.schemas.user import (
    UserListResponse,
    UserResponse,
    UserCreate,
    UserUpdate,
    UserStatus as SchemaUserStatus
)

# 作成したStripeスキーマをインポート
from app.schemas.stripe import (
    StripeProductCreate, StripeProductUpdate, StripeProductResponse, StripeProductWithPricesResponse,
    StripePriceCreate, StripePriceUpdate, StripePriceResponse
)

# --- Userモデルのインポートを追加 ---
from app.models.user import User as UserModel

# --- crud_role をインポート ---
from app.crud import crud_role, crud_user # crud_user も使うので明示的にインポート
# ----------------------------

# --- get_async_db をインポート --- 
# from app.api.deps import get_db
from app.database.database import get_async_db # get_async_db を直接インポート
# ----------------------------------

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])

# Stripeインスタンスの初期化はStripeService内で行われるため不要
# stripe.api_key = settings.STRIPE_SECRET_KEY

# ---------- ユーザー関連のエンドポイント ---------- #
@router.get("/users",
            response_model=UserListResponse,
            response_model_exclude={'users': {'__all__': {'full_name', 'is_verified', 'user_roles', 'login_info'}}}
            )
async def admin_get_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[SchemaUserStatus] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(require_permission('admin_access', 'user_read')),
):
    users, total = await crud_user.get_multi_users(db, skip=skip, limit=limit, search=search, role=role, status=status)
    return UserListResponse(
        total=total,
        users=users,
        page=(skip // limit) + 1,
        size=len(users),
    )

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(require_permission('admin_access', 'user_write')),
):
    existing_user = await crud_user.get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このメールアドレスは既に使用されています。",
        )
    new_user = await crud_user.create_user(db, user_in=user_in)
    return new_user

@router.get("/users/{user_id}",
           response_model=UserResponse,
           response_model_exclude={'user_roles', 'login_info'} # Exclude raw relations
           )
async def admin_get_user(
    user_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(require_permission('admin_access', 'user_read')),
):
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無効なユーザーID形式です")
    db_user = await crud_user.get_user(db, user_id=user_uuid)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ユーザーが見つかりません")
    return db_user

@router.put("/users/{user_id}",
           response_model=UserResponse,
           response_model_exclude={'user_roles', 'login_info'} # Exclude raw relations
           )
async def admin_update_user( # ★ async に変更
    user_id: str,
    user_in: UserUpdate, # スキーマの型は UserUpdate (role は Optional[str])
    db: AsyncSession = Depends(get_async_db), # ★ get_async_db に変更
    current_user: UserModel = Depends(require_permission('admin_access', 'user_write')), # ★ 型を UserModel に変更
):
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無効なユーザーID形式です")

    db_user = await crud_user.get_user(db, user_id=user_uuid) # ★ await を追加
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ユーザーが見つかりません")

    # --- ★ ロール存在チェックを追加 --- 
    if user_in.role is not None: # role が指定されている場合のみチェック
        target_role = await crud_role.get_role_by_name(db, name=user_in.role) # ★ await を追加
        if not target_role:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, # 404 でも良いかもしれない
                detail=f"指定されたロール '{user_in.role}' は存在しません。",
            )
    # --- チェックここまで ---

    # メールアドレス変更時の重複チェック (既存のロジック)
    if user_in.email and user_in.email != db_user.email:
        existing_user = await crud_user.get_user_by_email(db, email=user_in.email) # ★ await を追加
        if existing_user and existing_user.id != user_uuid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="このメールアドレスは既に使用されています。",
            )

    # ユーザー更新処理 (crud_user.update_user は後で修正)
    updated_user = await crud_user.update_user(db, db_user=db_user, user_in=user_in) # ★ await を追加
    return updated_user

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(require_permission('admin_access', 'user_write')),
):
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無効なユーザーID形式です")
    removed = await crud_user.remove_user(db, user_id=user_uuid)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ユーザーが見つかりません")
    return None

# ---------- 商品関連のエンドポイント ---------- #

@router.get("/products", response_model=List[StripeProductWithPricesResponse])
async def get_products(
    active: Optional[bool] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(require_permission('admin_access', 'stripe_product_read')),
):
    """
    Stripe商品一覧（関連価格情報を含む）を取得する
    """
    try:
        products_raw = StripeService.list_products(active=active, limit=limit)
        products_with_prices = []
        for prod_raw in products_raw:
            try:
                # 商品に関連する有効な価格を取得
                prices_raw = StripeService.list_prices(product_id=prod_raw.id, active=True, limit=100)
                formatted_prices = []
                for price_obj in prices_raw: # price_obj は Stripe Price オブジェクト/辞書
                    try:
                        # product フィールドから Product ID (文字列) を抽出
                        product_field_value = price_obj.get('product')
                        product_id_str = None
                        if isinstance(product_field_value, dict): # 展開された Product オブジェクト (辞書として扱われることが多い)
                            product_id_str = product_field_value.get('id')
                        elif isinstance(product_field_value, str): # 既にID文字列の場合
                            product_id_str = product_field_value
                        # stripe.Product オブジェクトの場合 (Stripeライブラリのバージョンによる)
                        elif hasattr(product_field_value, 'id'): 
                            product_id_str = product_field_value.id 

                        if product_id_str:
                            # 元のデータをコピーし、productフィールドをID文字列に置き換える
                            price_data_dict = dict(price_obj)
                            price_data_dict['product'] = product_id_str
                            # Pydanticモデルでバリデーション/変換
                            formatted_prices.append(StripePriceResponse.model_validate(price_data_dict))
                        else:
                             logger.warning(f"Price {price_obj.get('id')} is missing product ID.")
                    except Exception as price_val_e:
                        logger.error(f"Pydantic validation failed for price {price_obj.get('id')}: {price_val_e}")
                        # エラーがあっても処理を続けるか、ここでエラーを発生させるか選択
                        # continue

                # Productレスポンスモデルでバリデーション/変換
                product_resp_data = dict(prod_raw)
                product_resp = StripeProductWithPricesResponse.model_validate({
                    **product_resp_data,
                    'prices': formatted_prices
                })
                products_with_prices.append(product_resp)
            except Exception as prod_val_e:
                logger.error(f"Pydantic validation failed for product {prod_raw.get('id')}: {prod_val_e}")
                # エラーがあっても処理を続けるか、ここでエラーを発生させるか選択
                # continue

        return products_with_prices
    except Exception as e:
        logger.error(f"Stripe商品の取得に失敗しました: {str(e)}", exc_info=True) # エラー詳細をログに出力
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe商品の取得に失敗しました: {str(e)}"
        )

@router.post("/products", response_model=StripeProductResponse, status_code=status.HTTP_201_CREATED)
async def create_stripe_product(
    product_data: StripeProductCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(require_permission('admin_access', 'stripe_product_write')),
):
    """
    Stripeに新しい商品を作成します (StripeServiceを使用)
    """
    try:
        product = StripeService.create_product(
            name=product_data.name,
            description=product_data.description,
            active=product_data.active,
            metadata=product_data.metadata
        )
        return product
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe商品の作成に失敗しました: {str(e)}"
        )

@router.put("/products/{product_id}", response_model=StripeProductResponse)
async def update_stripe_product(
    product_id: str,
    product_data: StripeProductUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(require_permission('admin_access', 'stripe_product_write')),
):
    """
    Stripe商品を更新します (StripeServiceを使用)
    """
    try:
        # 更新データがない場合はエラーにしても良い
        if not product_data.model_dump(exclude_unset=True):
             raise HTTPException(
                 status_code=status.HTTP_400_BAD_REQUEST,
                 detail="更新するデータがありません。"
             )

        product = StripeService.update_product(
            product_id=product_id,
            name=product_data.name,
            description=product_data.description,
            active=product_data.active,
            metadata=product_data.metadata
        )
        return product
    except stripe.error.InvalidRequestError as e:
         if "No such product" in str(e):
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="指定された商品が見つかりません")
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Stripe APIエラー: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe商品の更新に失敗しました: {str(e)}"
        )

@router.delete("/products/{product_id}", response_model=StripeProductResponse)
async def archive_stripe_product(
    product_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(require_permission('admin_access', 'stripe_product_write')),
):
    """
    Stripe商品をアーカイブ（非アクティブ化）します
    """
    try:
        product = StripeService.archive_product(product_id=product_id)
        return product
    except stripe.error.InvalidRequestError as e:
         if "No such product" in str(e):
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="指定された商品が見つかりません")
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Stripe APIエラー: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe商品のアーカイブに失敗しました: {str(e)}"
        )

# ---------- 価格関連のエンドポイント ---------- #

@router.get("/prices", response_model=List[StripePriceResponse])
async def get_prices(
    product_id: Optional[str] = None,
    active: Optional[bool] = None,
    limit: int = 100,
    current_user: UserModel = Depends(require_permission('admin_access', 'stripe_price_read')),
):
    """
    Stripe価格一覧を取得します (StripeServiceを使用)
    """
    try:
        prices_raw = StripeService.list_prices(product_id=product_id, active=active, limit=limit)
        formatted_prices = []
        for price_obj in prices_raw:
            try:
                # product フィールドから Product ID (文字列) を抽出
                product_field_value = price_obj.get('product')
                product_id_str = None
                if isinstance(product_field_value, dict):
                    product_id_str = product_field_value.get('id')
                elif isinstance(product_field_value, str):
                    product_id_str = product_field_value
                elif hasattr(product_field_value, 'id'):
                    product_id_str = product_field_value.id

                if product_id_str:
                    price_data_dict = dict(price_obj)
                    price_data_dict['product'] = product_id_str
                    formatted_prices.append(StripePriceResponse.model_validate(price_data_dict))
                else:
                    logger.warning(f"Price {price_obj.get('id')} is missing product ID.")
            except Exception as price_val_e:
                logger.error(f"Pydantic validation failed for price {price_obj.get('id')}: {price_val_e}")
                # continue

        return formatted_prices # 整形・検証済みのリストを返す
    except Exception as e:
        logger.error(f"Stripe価格の取得に失敗しました: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe価格の取得に失敗しました: {str(e)}"
        )

@router.post("/prices", response_model=StripePriceResponse, status_code=status.HTTP_201_CREATED)
async def create_stripe_price(
    price_data: StripePriceCreate,
    current_user: UserModel = Depends(require_permission('admin_access', 'stripe_price_write')),
):
    """
    Stripeに新しい価格を作成します (StripeServiceを使用)
    """
    try:
        # recurring を Dict に変換する必要があるか確認 (Pydanticが自動変換するはず)
        recurring_dict = price_data.recurring.model_dump()

        price = StripeService.create_price(
            product_id=price_data.product_id,
            unit_amount=price_data.unit_amount,
            currency=price_data.currency,
            recurring=recurring_dict,
            active=price_data.active,
            metadata=price_data.metadata,
            lookup_key=price_data.lookup_key
        )
        return price
    except stripe.error.InvalidRequestError as e:
        # 商品が存在しない場合などのエラーハンドリング
        if "No such product" in str(e):
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="指定された商品が見つかりません")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Stripe APIエラー: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe価格の作成に失敗しました: {str(e)}"
        )

@router.put("/prices/{price_id}", response_model=StripePriceResponse)
async def update_stripe_price(
    price_id: str,
    price_data: StripePriceUpdate,
    current_user: UserModel = Depends(require_permission('admin_access', 'stripe_price_write')),
):
    """
    Stripe価格を更新します (StripeServiceを使用)
    """
    try:
        if not price_data.model_dump(exclude_unset=True):
             raise HTTPException(
                 status_code=status.HTTP_400_BAD_REQUEST,
                 detail="更新するデータがありません。"
             )

        price = StripeService.update_price(
            price_id=price_id,
            active=price_data.active,
            metadata=price_data.metadata,
            lookup_key=price_data.lookup_key
        )
        return price
    except stripe.error.InvalidRequestError as e:
         if "No such price" in str(e):
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="指定された価格が見つかりません")
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Stripe APIエラー: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe価格の更新に失敗しました: {str(e)}"
        )

# DELETEは価格の非アクティブ化に対応
@router.delete("/prices/{price_id}", response_model=StripePriceResponse)
async def archive_stripe_price(
    price_id: str,
    current_user: UserModel = Depends(require_permission('admin_access', 'stripe_price_write')),
):
    """
    Stripe価格をアーカイブ（非アクティブ化）します (StripeServiceを使用)
    """
    try:
        # update_price を使って active=False にする
        price = StripeService.update_price(price_id=price_id, active=False)
        return price
    except stripe.error.InvalidRequestError as e:
         if "No such price" in str(e):
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="指定された価格が見つかりません")
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Stripe APIエラー: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe価格のアーカイブに失敗しました: {str(e)}"
        )

# ---------- キャンペーンコード関連のエンドポイント (修正) ---------- #

@router.get("/campaign-codes", response_model=List[CampaignCodeResponse])
async def admin_get_campaign_codes(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(require_permission('admin_access', 'campaign_code_read')),
):
    """
    キャンペーンコード一覧を取得します。(Coupon情報を含む)
    管理者専用エンドポイント。
    """
    campaign_codes = await get_all_campaign_codes(db=db, skip=skip, limit=limit)
    return campaign_codes

@router.post("/campaign-codes", response_model=CampaignCodeResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_campaign_code(
    campaign_code: CampaignCodeCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(require_permission('admin_access', 'campaign_code_write')),
):
    """
    新しいキャンペーンコードを作成します。(指定されたDB Couponに紐づくStripe Promotion Codeも作成)
    管理者専用エンドポイント。
    """
    try:
        return await create_campaign_code(db=db, campaign_code=campaign_code, creator=current_user)
    except HTTPException as e: # CRUD関数内で発生したHTTPExceptionをそのまま返す
        raise e
    except Exception as e: # その他の予期せぬエラー
        logger.error(f"キャンペーンコード作成APIエラー: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="キャンペーンコードの作成に失敗しました。")

@router.delete("/campaign-codes/{campaign_code_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_campaign_code(
    campaign_code_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(require_permission('admin_access', 'campaign_code_write')),
):
    """
    キャンペーンコードをDBから削除します。(紐づくStripe Promotion Codeも無効化)
    管理者専用エンドポイント。
    """
    try:
        uuid_campaign_code_id = UUID(campaign_code_id)
    except ValueError:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無効なcampaign_code_id形式です"
        )

    deleted = await delete_campaign_code(db, uuid_campaign_code_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定されたキャンペーンコードが見つかりません"
        )
    return None

# ---------- ★ DB Stripe Coupon 関連のエンドポイント (追加) ---------- #

@router.get("/stripe-coupons", response_model=List[StripeCouponResponse])
async def admin_get_db_stripe_coupons(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(require_permission('admin_access', 'stripe_coupon_read')),
):
    """DBに保存されているStripe Couponの情報一覧を取得します。"""
    db_coupons = await get_all_db_coupons(db=db, skip=skip, limit=limit)
    return db_coupons

@router.get("/stripe-coupons/{coupon_db_id}", response_model=StripeCouponResponse)
async def admin_get_db_stripe_coupon(
    coupon_db_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(require_permission('admin_access', 'stripe_coupon_read')),
):
    """DBに保存されている特定のStripe Coupon情報を取得します。"""
    db_coupon = await get_db_coupon(db, coupon_db_id=coupon_db_id)
    if not db_coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定されたDB Couponが見つかりません。"
        )
    return db_coupon

@router.put("/stripe-coupons/{coupon_db_id}", response_model=StripeCouponResponse)
async def admin_update_db_stripe_coupon(
    coupon_db_id: UUID,
    coupon_in: StripeCouponUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(require_permission('admin_access', 'stripe_coupon_write')),
):
    """DBに保存されているStripe Coupon情報を更新します (主に is_active, metadata)。"""
    updated_coupon = await update_db_coupon(db, coupon_db_id=coupon_db_id, coupon_in=coupon_in)
    if not updated_coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定されたDB Couponが見つかりません。"
        )
    return updated_coupon

# POST /stripe-coupons (DBへの登録) は、Stripe Coupon自体をどう作成するかによるため、一旦保留。
# Stripe側でCouponを作成 -> そのIDをDBに登録するフローが一般的かもしれない。
# その場合、このAdmin APIでStripe Couponを直接作成する機能は不要かもしれない。

# ---------- 割引タイプ関連のエンドポイント (コメントアウト) ---------- #
# DiscountType は StripeCoupon/PromotionCode で代替されるため、不要になる可能性が高い
# 必要であれば残すが、一旦コメントアウトまたは削除を検討

# @router.get("/discount-types", response_model=List[DiscountTypeResponse])
# async def admin_get_discount_types(
#     skip: int = 0,
#     limit: int = 100,
#     db: AsyncSession = Depends(get_async_db),
#     current_user: UserModel = Depends(require_permission('admin_access', 'discount_type_read')),
# ):
#     """割引タイプ一覧を取得します。"""
#     discount_types = await get_all_discount_types(db, skip=skip, limit=limit)
#     return discount_types

# @router.post("/discount-types", response_model=DiscountTypeResponse, status_code=status.HTTP_201_CREATED)
# async def admin_create_discount_type(
#     discount_type_in: DiscountTypeCreate,
#     db: AsyncSession = Depends(get_async_db),
#     current_user: UserModel = Depends(require_permission('admin_access', 'discount_type_write')),
# ):
#     """新しい割引タイプを作成します。"""
#     try:
#         return await create_discount_type(db=db, discount_type=discount_type_in)
#     except HTTPException as e: # 重複エラーなどをキャッチ
#         raise e
#     except Exception as e:
#         logger.error(f"割引タイプの作成中に予期せぬエラー: {e}")
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# @router.put("/discount-types/{discount_type_id}", response_model=DiscountTypeResponse)
# async def admin_update_discount_type(
#     discount_type_id: UUID,
#     discount_type_in: DiscountTypeUpdate,
#     db: AsyncSession = Depends(get_async_db),
#     current_user: UserModel = Depends(require_permission('admin_access', 'discount_type_write')),
# ):
#     """割引タイプを更新します。"""
#     try:
#         updated_discount_type = await update_discount_type(db, discount_type_id, discount_type_in)
#         if not updated_discount_type:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discount type not found")
#         return updated_discount_type
#     except HTTPException as e: # 重複エラーなどをキャッチ
#         raise e
#     except Exception as e:
#         logger.error(f"割引タイプの更新中に予期せぬエラー: {e}")
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# @router.delete("/discount-types/{discount_type_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def admin_delete_discount_type(
#     discount_type_id: UUID,
#     db: AsyncSession = Depends(get_async_db),
#     current_user: UserModel = Depends(require_permission('admin_access', 'discount_type_write')),
# ):
#     """割引タイプを削除します。"""
#     deleted = await delete_discount_type(db, discount_type_id)
#     if not deleted:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discount type not found")
#     return None 

# --- Stripe Coupon Management Schemas ---

class StripeCouponCreate(BaseModel):
    """Stripe Coupon 作成リクエストスキーマ"""
    name: Optional[str] = None
    percent_off: Optional[float] = Field(None, gt=0, le=100)
    amount_off: Optional[int] = Field(None, gt=0) # 整数値 (セント単位)
    currency: Optional[str] = Field(None, min_length=3, max_length=3) # amount_off の場合に必須
    duration: str = Field(..., pattern="^(forever|once|repeating)$") # forever, once, repeating
    duration_in_months: Optional[int] = Field(None, gt=0) # duration=repeating の場合に必須
    max_redemptions: Optional[int] = Field(None, gt=0)
    redeem_by: Optional[int] = None # Unix timestamp
    metadata: Optional[Dict[str, str]] = None
    applies_to: Optional[Dict[str, List[str]]] = None # 例: {"products": ["prod_123", "prod_456"]}

    # amount_off と percent_off のどちらか一方のみ指定可能にするバリデーション (例)
    # @validator('*', pre=True, always=True)
    # def check_discount_type(cls, values):
    #     if values.get('amount_off') is not None and values.get('percent_off') is not None:
    #         raise ValueError('amount_off と percent_off は同時に指定できません。')
    #     if values.get('amount_off') is None and values.get('percent_off') is None:
    #         raise ValueError('amount_off または percent_off のどちらか一方を指定してください。')
    #     if values.get('amount_off') is not None and values.get('currency') is None:
    #         raise ValueError('amount_off を指定する場合は currency も指定してください。')
    #     if values.get('duration') == 'repeating' and values.get('duration_in_months') is None:
    #         raise ValueError('duration が repeating の場合は duration_in_months を指定してください。')
    #     return values

class StripeCouponResponse(BaseModel):
    """Stripe Coupon レスポンススキーマ"""
    id: str
    object: str
    amount_off: Optional[int]
    created: int
    currency: Optional[str]
    duration: str
    duration_in_months: Optional[int]
    livemode: bool
    max_redemptions: Optional[int]
    metadata: Dict[str, str]
    name: Optional[str]
    percent_off: Optional[float]
    redeem_by: Optional[int]
    times_redeemed: int
    valid: bool
    applies_to: Optional[Dict[str, List[str]]] = None

    class Config:
        orm_mode = True # orm_mode の代わりに from_attributes = True を使用 (Pydantic v2)
        # from_attributes = True # Pydantic v2 の場合

class StripeCouponUpdate(BaseModel):
    """Stripe Coupon 更新リクエストスキーマ"""
    name: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


# --- Stripe Coupon Management Endpoints ---

@router.post(
    "/stripe/coupons",
    response_model=StripeCouponResponse,
    summary="Create Stripe Coupon",
    dependencies=[Depends(require_permission('admin_access'))] # 管理者権限が必要
)
async def create_stripe_coupon(
    coupon_data: StripeCouponCreate,
    current_user: UserModel = Depends(require_permission('admin_access')) # require_permission を使用
):
    """
    新しい Stripe Coupon を作成します。

    **必要な権限:** `admin_access`
    """
    try:
        # Pydantic モデルから辞書に変換
        coupon_params = coupon_data.dict(exclude_unset=True)
        logger.info(f"Stripe Coupon 作成リクエスト: {coupon_params} by user {current_user.email}")

        # amount_off と percent_off のバリデーション（Pydantic側で定義するかここでチェック）
        if coupon_params.get('amount_off') is not None and coupon_params.get('percent_off') is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="amount_off と percent_off は同時に指定できません。")
        if coupon_params.get('amount_off') is None and coupon_params.get('percent_off') is None:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="amount_off または percent_off のどちらか一方を指定してください。")
        if coupon_params.get('amount_off') is not None and coupon_params.get('currency') is None:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="amount_off を指定する場合は currency も指定してください。")
        if coupon_params.get('duration') == 'repeating' and coupon_params.get('duration_in_months') is None:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="duration が repeating の場合は duration_in_months を指定してください。")

        created_coupon = StripeService.create_coupon(**coupon_params)
        logger.info(f"Stripe Coupon 作成成功: {created_coupon.get('id')}")
        # Stripe APIのレスポンスを Pydantic モデルに変換して返す
        # **注意:** Stripe API のレスポンス構造に合わせて StripeCouponResponse を調整する必要があるかもしれません
        return StripeCouponResponse.parse_obj(created_coupon) # parse_obj は Pydantic v1, v2 では model_validate
        # return StripeCouponResponse.model_validate(created_coupon) # Pydantic v2
    except stripe.error.StripeError as e:
        logger.error(f"Stripe Coupon 作成 Stripe API エラー: {e.user_message}")
        raise HTTPException(status_code=e.http_status or status.HTTP_400_BAD_REQUEST, detail=e.user_message or "Stripe API Error")
    except ValueError as e: # Pydantic または手動バリデーションエラー
         logger.error(f"Stripe Coupon 作成 バリデーションエラー: {str(e)}")
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception(f"Stripe Coupon 作成中に予期せぬエラーが発生しました: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during coupon creation")

@router.get(
    "/stripe/coupons",
    response_model=List[StripeCouponResponse],
    summary="List Stripe Coupons",
    dependencies=[Depends(require_permission('admin_access'))]
)
async def list_stripe_coupons(
    limit: int = Query(10, ge=1, le=100),
    starting_after: Optional[str] = Query(None),
    ending_before: Optional[str] = Query(None),
    created_lt: Optional[int] = Query(None, description="Unix timestamp"),
    created_lte: Optional[int] = Query(None, description="Unix timestamp"),
    created_gt: Optional[int] = Query(None, description="Unix timestamp"),
    created_gte: Optional[int] = Query(None, description="Unix timestamp"),
    current_user: UserModel = Depends(require_permission('admin_access'))
):
    """
    Stripe Coupon のリストを取得します。ページネーションと作成日時によるフィルタリングが可能です。

    **必要な権限:** `admin_access`
    """
    try:
        created_filter = {}
        if created_lt: created_filter['lt'] = created_lt
        if created_lte: created_filter['lte'] = created_lte
        if created_gt: created_filter['gt'] = created_gt
        if created_gte: created_filter['gte'] = created_gte

        logger.info(f"Stripe Coupon リスト取得リクエスト by user {current_user.email}. Params: limit={limit}, starting_after={starting_after}, ending_before={ending_before}, created={created_filter or None}")

        coupons_data = StripeService.list_coupons(
            limit=limit,
            created=created_filter or None,
            starting_after=starting_after,
            ending_before=ending_before
        )
        logger.info(f"Stripe Coupon リスト取得成功: {len(coupons_data)} 件")
        # return [StripeCouponResponse.model_validate(c) for c in coupons_data] # Pydantic v2
        return [StripeCouponResponse.parse_obj(c) for c in coupons_data] # Pydantic v1
    except stripe.error.StripeError as e:
        logger.error(f"Stripe Coupon リスト取得 Stripe API エラー: {e.user_message}")
        raise HTTPException(status_code=e.http_status or status.HTTP_400_BAD_REQUEST, detail=e.user_message or "Stripe API Error")
    except Exception as e:
        logger.exception(f"Stripe Coupon リスト取得中に予期せぬエラーが発生しました: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during coupon listing")

@router.get(
    "/stripe/coupons/{coupon_id}",
    response_model=StripeCouponResponse,
    summary="Retrieve Stripe Coupon",
    dependencies=[Depends(require_permission('admin_access'))]
)
async def retrieve_stripe_coupon(
    coupon_id: str,
    current_user: UserModel = Depends(require_permission('admin_access'))
):
    """
    指定された ID の Stripe Coupon 詳細を取得します。

    **必要な権限:** `admin_access`
    """
    try:
        logger.info(f"Stripe Coupon 詳細取得リクエスト: {coupon_id} by user {current_user.email}")
        coupon = StripeService.retrieve_coupon(coupon_id)
        if not coupon: # StripeService が None を返す場合 (通常はエラーを raise するはず)
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found")
        logger.info(f"Stripe Coupon 詳細取得成功: {coupon.get('id')}")
        # return StripeCouponResponse.model_validate(coupon) # Pydantic v2
        return StripeCouponResponse.parse_obj(coupon) # Pydantic v1
    except stripe.error.InvalidRequestError as e:
         if "No such coupon" in str(e):
             logger.warning(f"Stripe Coupon {coupon_id} が見つかりません。")
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found")
         logger.error(f"Stripe Coupon ({coupon_id}) 詳細取得 Stripe API エラー: {e.user_message}")
         raise HTTPException(status_code=e.http_status or status.HTTP_400_BAD_REQUEST, detail=e.user_message or "Stripe API Error")
    except stripe.error.StripeError as e:
        logger.error(f"Stripe Coupon ({coupon_id}) 詳細取得 Stripe API エラー: {e.user_message}")
        raise HTTPException(status_code=e.http_status or status.HTTP_400_BAD_REQUEST, detail=e.user_message or "Stripe API Error")
    except Exception as e:
        logger.exception(f"Stripe Coupon ({coupon_id}) 詳細取得中に予期せぬエラーが発生しました: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during coupon retrieval")

@router.put(
    "/stripe/coupons/{coupon_id}",
    response_model=StripeCouponResponse,
    summary="Update Stripe Coupon",
    dependencies=[Depends(require_permission('admin_access'))]
)
async def update_stripe_coupon(
    coupon_id: str,
    coupon_data: StripeCouponUpdate,
    current_user: UserModel = Depends(require_permission('admin_access'))
):
    """
    指定された ID の Stripe Coupon 情報（名前、メタデータ）を更新します。

    **必要な権限:** `admin_access`
    """
    try:
        update_params = coupon_data.dict(exclude_unset=True)
        logger.info(f"Stripe Coupon 更新リクエスト: {coupon_id}, data: {update_params} by user {current_user.email}")
        if not update_params:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="更新するデータが指定されていません。")

        updated_coupon = StripeService.update_coupon(coupon_id, **update_params)
        logger.info(f"Stripe Coupon 更新成功: {updated_coupon.get('id')}")
        # return StripeCouponResponse.model_validate(updated_coupon) # Pydantic v2
        return StripeCouponResponse.parse_obj(updated_coupon) # Pydantic v1
    except stripe.error.InvalidRequestError as e:
         if "No such coupon" in str(e):
             logger.warning(f"更新しようとしたStripe Coupon {coupon_id} が見つかりません。")
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found")
         logger.error(f"Stripe Coupon ({coupon_id}) 更新 Stripe API エラー: {e.user_message}")
         raise HTTPException(status_code=e.http_status or status.HTTP_400_BAD_REQUEST, detail=e.user_message or "Stripe API Error")
    except stripe.error.StripeError as e:
        logger.error(f"Stripe Coupon ({coupon_id}) 更新 Stripe API エラー: {e.user_message}")
        raise HTTPException(status_code=e.http_status or status.HTTP_400_BAD_REQUEST, detail=e.user_message or "Stripe API Error")
    except Exception as e:
        logger.exception(f"Stripe Coupon ({coupon_id}) 更新中に予期せぬエラーが発生しました: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during coupon update")

@router.delete(
    "/stripe/coupons/{coupon_id}",
    status_code=status.HTTP_204_NO_CONTENT, # 成功時は Body なし
    summary="Delete Stripe Coupon",
    dependencies=[Depends(require_permission('admin_access'))]
)
async def delete_stripe_coupon(
    coupon_id: str,
    current_user: UserModel = Depends(require_permission('admin_access'))
):
    """
    指定された ID の Stripe Coupon を削除します。

    **注意:** 一度使用された Coupon は削除できない場合があります。

    **必要な権限:** `admin_access`
    """
    try:
        logger.info(f"Stripe Coupon 削除リクエスト: {coupon_id} by user {current_user.email}")
        StripeService.delete_coupon(coupon_id)
        logger.info(f"Stripe Coupon 削除成功: {coupon_id}")
        return # 204 No Content
    except HTTPException as e: # delete_coupon 内で raise された HTTPException をそのまま返す
        raise e
    except stripe.error.StripeError as e:
        logger.error(f"Stripe Coupon ({coupon_id}) 削除 Stripe API エラー: {e.user_message}")
        raise HTTPException(status_code=e.http_status or status.HTTP_400_BAD_REQUEST, detail=e.user_message or "Stripe API Error")
    except Exception as e:
        logger.exception(f"Stripe Coupon ({coupon_id}) 削除中に予期せぬエラーが発生しました: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during coupon deletion") 