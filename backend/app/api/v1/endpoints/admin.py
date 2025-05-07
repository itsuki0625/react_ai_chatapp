from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional, Set
import stripe # エラーハンドリング用に追加
import logging # ロギング用に追加
from uuid import UUID
from pydantic import BaseModel, Field # ★ BaseModel と Field をインポート

from app.core.config import settings
from app.api.deps import get_current_user, require_permission
from app.services.stripe_service import StripeService # StripeServiceをインポート
# Pydanticスキーマのインポート (後で追加する可能性あり)
# from app.schemas.stripe import ProductCreate, ProductUpdate, PriceCreate, PriceUpdate # 例

from app.schemas.subscription import (
    CampaignCodeCreate, 
    CampaignCodeResponse,
    CampaignCodeUpdate,
    StripeCouponCreate, StripeCouponUpdate, StripeCouponResponse
)
from app.crud.subscription import (
    create_campaign_code,
    get_campaign_code,
    get_all_campaign_codes,
    update_campaign_code,
    delete_campaign_code,
    create_db_coupon,
    get_db_coupon,
    get_all_db_coupons,
    update_db_coupon,
    delete_db_coupon,
    get_db_coupon_by_stripe_id
)
from app.crud.user import get_multi_users, remove_user, create_user, get_user, update_user, get_user_by_email
from app.schemas.user import (
    UserListResponse,
    UserResponse,
    UserCreate,
    UserUpdate,
    UserStatus as SchemaUserStatus,
    RoleResponse # もし UserResponse 内でネストされたロール情報として使われていなければ、
                  # RoleRead を直接使う方が明確
)
from app.schemas.role import RoleRead # ★ RoleRead をインポート

# 作成したStripeスキーマをインポート
from app.schemas.stripe import (
    StripeProductCreate, StripeProductUpdate, StripeProductResponse, StripeProductWithPricesResponse,
    StripePriceCreate, StripePriceUpdate, StripePriceResponse,
    StripeCouponListFilter, StripeApiCouponResponse
)

# --- Userモデルのインポートを追加 ---
from app.models.user import User, Role, Permission # UserModel の代わりに User を直接使う

# --- crud_role をインポート ---
from app.crud import crud_role, crud_user # crud_user も使うので明示的にインポート
# ----------------------------

# --- get_async_db をインポート ---
from app.database.database import get_async_db # get_async_db を直接インポート
# ----------------------------------

logger = logging.getLogger(__name__)

router = APIRouter()

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
    current_user: User = Depends(require_permission('admin_access', 'user_read')),
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
    current_user: User = Depends(require_permission('admin_access', 'user_write')),
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
    current_user: User = Depends(require_permission('admin_access', 'user_read')),
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
async def admin_update_user(
    user_id: str,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('admin_access', 'user_write')),
):
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無効なユーザーID形式です")

    db_user = await crud_user.get_user(db, user_id=user_uuid)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ユーザーが見つかりません")

    # --- ★ ロール存在チェックを追加 ---
    if user_in.role is not None:
        target_role = await crud_role.get_role_by_name(db, name=user_in.role)
        if not target_role:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"指定されたロール '{user_in.role}' は存在しません。",
            )
    # --- チェックここまで ---

    # メールアドレス変更時の重複チェック (既存のロジック)
    if user_in.email and user_in.email != db_user.email:
        existing_user = await crud_user.get_user_by_email(db, email=user_in.email)
        if existing_user and existing_user.id != user_uuid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="このメールアドレスは既に使用されています。",
            )

    # ユーザー更新処理
    updated_user = await crud_user.update_user(db, db_user=db_user, user_in=user_in)
    return updated_user

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('admin_access', 'user_write')),
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
    current_user: User = Depends(require_permission('admin_access', 'stripe_product_read')),
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
    current_user: User = Depends(require_permission('admin_access', 'stripe_product_write')),
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
    current_user: User = Depends(require_permission('admin_access', 'stripe_product_write')),
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
    current_user: User = Depends(require_permission('admin_access', 'stripe_product_write')),
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
    current_user: User = Depends(require_permission('admin_access', 'stripe_price_read')),
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
    current_user: User = Depends(require_permission('admin_access', 'stripe_price_write')),
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
    current_user: User = Depends(require_permission('admin_access', 'stripe_price_write')),
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
    current_user: User = Depends(require_permission('admin_access', 'stripe_price_write')),
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

# @router.get("/campaign-codes", response_model=List[CampaignCodeResponse]) # ★ 重複定義のためコメントアウトまたは削除
# async def admin_get_campaign_codes(
#     skip: int = 0,
#     limit: int = 100,
#     db: AsyncSession = Depends(get_async_db),
#     current_user: User = Depends(require_permission('admin_access', 'campaign_code_read')),
# ):
#     """
#     キャンペーンコード一覧を取得します。(Coupon情報を含む)
#     管理者専用エンドポイント。
#     """
#     campaign_codes = await get_all_campaign_codes(db=db, skip=skip, limit=limit)
#     return campaign_codes

@router.post(
    "/campaign-codes",
    response_model=CampaignCodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Campaign Code",
    dependencies=[Depends(require_permission('admin_access', 'campaign_code_write'))]
)
async def admin_create_campaign_code(
    campaign_code_in: CampaignCodeCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('admin_access', 'campaign_code_write')), # 依存関係を重複させない
):
    """
    新しいキャンペーンコードを作成します。

    **必要な権限:** `admin_access`, `campaign_code_write`
    """
    try:
        # 割引タイプが存在するか確認 (任意)
        # if campaign_code_in.discount_type_id:
        #     discount_type = await get_discount_type(db, campaign_code_in.discount_type_id)
        #     if not discount_type:
        #         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discount type not found")

        # Stripe Coupon ID が指定されている場合、DBに存在するか確認 (任意)
        if campaign_code_in.stripe_coupon_id:
            db_coupon = await get_db_coupon_by_stripe_id(db, stripe_coupon_id=campaign_code_in.stripe_coupon_id)
            if not db_coupon:
                # ここでエラーにするか、Stripeから取得してDBに保存するかは要件次第
                logger.warning(f"Stripe Coupon ID {campaign_code_in.stripe_coupon_id} provided but not found in DB.")
                # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Stripe Coupon ID {campaign_code_in.stripe_coupon_id} not found in database.")

        created_code = await create_campaign_code(db=db, campaign_code=campaign_code_in, creator=current_user)
        return created_code
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"キャンペーンコード作成中に予期せぬエラー: {e}", exc_info=True)
        if db.in_transaction(): await db.rollback() # ロールバック試行
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during campaign code creation")

# ★ こちらの admin_get_campaign_codes を残す (is_active フィルタ付き)
@router.get(
    "/campaign-codes",
    response_model=List[CampaignCodeResponse],
    summary="List Campaign Codes",
    # dependencies=[Depends(require_permission('admin_access', 'campaign_code_read'))] # ★ デコレータ内の重複した依存関係を削除
)
async def admin_get_campaign_codes(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('admin_access', 'campaign_code_read')), # ここで権限チェック
):
    """
    キャンペーンコードの一覧を取得します。

    **必要な権限:** `admin_access`, `campaign_code_read`
    """
    codes = await get_all_campaign_codes(db=db, skip=skip, limit=limit, is_active=is_active)
    return codes

@router.get(
    "/campaign-codes/{code_id}",
    response_model=CampaignCodeResponse,
    summary="Get Campaign Code by ID",
    # dependencies=[Depends(require_permission('admin_access', 'campaign_code_read'))] # ★ デコレータ内の重複した依存関係を削除
)
async def admin_get_campaign_code(
    code_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('admin_access', 'campaign_code_read')), # ここで権限チェック
):
    """
    指定されたIDのキャンペーンコードを取得します。

    **必要な権限:** `admin_access`, `campaign_code_read`
    """
    code = await get_campaign_code(db=db, code_id=code_id)
    if not code:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign code not found")
    return code

@router.put(
    "/campaign-codes/{code_id}",
    response_model=CampaignCodeResponse,
    summary="Update Campaign Code",
    # dependencies=[Depends(require_permission('admin_access', 'campaign_code_write'))] # ★ デコレータ内の重複した依存関係を削除
)
async def admin_update_campaign_code(
    code_id: UUID,
    campaign_code_in: CampaignCodeUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('admin_access', 'campaign_code_write')), # ★ 権限チェック用の引数を追加
):
    """
    指定されたIDのキャンペーンコードを更新します。

    **必要な権限:** `admin_access`, `campaign_code_write`
    """
    try:
        updated_code = await update_campaign_code(db=db, code_id=code_id, campaign_code_update=campaign_code_in)
        if not updated_code:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign code not found")
        return updated_code
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"キャンペーンコード更新中に予期せぬエラー (ID: {code_id}): {e}", exc_info=True)
        if db.in_transaction(): await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during campaign code update")

@router.delete(
    "/campaign-codes/{code_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Campaign Code",
    # dependencies=[Depends(require_permission('admin_access', 'campaign_code_write'))] # ★ デコレータ内の重複した依存関係を削除
)
async def admin_delete_campaign_code(
    code_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('admin_access', 'campaign_code_write')), # ★ 権限チェック用の引数を追加
):
    """
    指定されたIDのキャンペーンコードを削除します。

    **必要な権限:** `admin_access`, `campaign_code_write`
    """
    deleted = await delete_campaign_code(db=db, code_id=code_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign code not found")
    return None

# --- DB Coupon CRUD エンドポイント (Stripe連携あり) ---

# GET /stripe-coupons (DBリスト取得)
@router.get(
    "/stripe-coupons",
    response_model=List[StripeCouponResponse],
    summary="List DB Coupons",
    dependencies=[Depends(require_permission('admin_access', 'stripe_coupon_read'))]
)
async def list_db_coupons(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    # current_user: User = Depends(require_permission('admin_access', 'stripe_coupon_read')),
):
    """データベースに登録されている Stripe Coupon のリストを取得します。"""
    logger.info(f"Fetching DB Coupons: skip={skip}, limit={limit}")
    db_coupons = await get_all_db_coupons(db, skip=skip, limit=limit)
    logger.info(f"Found {len(db_coupons)} DB Coupons.")
    return db_coupons

# POST /stripe-coupons (作成 Stripe+DB)
@router.post(
    "/stripe-coupons",
    response_model=StripeCouponResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Stripe Coupon and Import to DB",
    dependencies=[Depends(require_permission('admin_access', 'stripe_coupon_write'))]
)
async def create_stripe_coupon_and_import(
    coupon_data: StripeCouponCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('admin_access', 'stripe_coupon_write'))
):
    logger.info(f"Attempting to create Stripe coupon with data: {coupon_data.model_dump_json(indent=2)}")

    try:
        # Stripe API呼び出しのためのパラメータ準備
        stripe_coupon_params = {
            "name": coupon_data.name,
            "duration": coupon_data.duration,
        }
        if coupon_data.percent_off is not None:
            stripe_coupon_params["percent_off"] = coupon_data.percent_off
        elif coupon_data.amount_off is not None:
            stripe_coupon_params["amount_off"] = coupon_data.amount_off
            if coupon_data.currency:
                stripe_coupon_params["currency"] = coupon_data.currency
            else:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="amount_off を指定する場合は currency も必須です。"
                )
        else: # percent_off も amount_off もない場合
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="percent_off または amount_off のどちらかは必須です。"
            )

        if coupon_data.duration == "repeating":
            if coupon_data.duration_in_months is not None:
                stripe_coupon_params["duration_in_months"] = coupon_data.duration_in_months
            else:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="duration が repeating の場合は duration_in_months も必須です。"
                )

        if coupon_data.max_redemptions is not None:
            stripe_coupon_params["max_redemptions"] = coupon_data.max_redemptions
        if coupon_data.redeem_by is not None: # Unix timestamp
            stripe_coupon_params["redeem_by"] = coupon_data.redeem_by
        if coupon_data.metadata: # metadata はそのまま渡せる想定
            stripe_coupon_params["metadata"] = coupon_data.metadata
        
        # applies_to はStripe APIの形式に合わせる必要がある
        # StripeCouponCreate に applies_to がある場合:
        if hasattr(coupon_data, 'applies_to') and coupon_data.applies_to:
             stripe_coupon_params["applies_to"] = coupon_data.applies_to.model_dump(exclude_unset=True)


        # Stripe APIキー設定 (通常はグローバルかStripeService内で設定)
        # stripe.api_key = settings.STRIPE_SECRET_KEY # main.py等での設定を期待

        logger.debug(f"Calling Stripe API to create coupon with params: {stripe_coupon_params}")
        created_stripe_coupon = stripe.Coupon.create(**stripe_coupon_params)
        logger.info(f"Successfully created Stripe coupon ID: {created_stripe_coupon.id}")

        # DB登録用のデータを作成
        # create_db_coupon が StripeCouponCreate 互換のデータを期待すると仮定し、
        # Stripe APIレスポンスから情報を追加・整形する。
        # StripeCouponCreate スキーマに不足しているフィールドは、この後の手順で追加する。
        db_coupon_data_for_create_dict = coupon_data.model_dump(exclude_unset=True)
        db_coupon_data_for_create_dict['stripe_coupon_id'] = created_stripe_coupon.id
        
        # Stripe APIのレスポンスから取得できる可能性のある情報を追加（スキーマに存在すれば）
        if hasattr(created_stripe_coupon, 'valid'):
            db_coupon_data_for_create_dict['valid'] = created_stripe_coupon.valid
        if hasattr(created_stripe_coupon, 'created'): # Unix timestamp
             db_coupon_data_for_create_dict['created'] = created_stripe_coupon.created
        if hasattr(created_stripe_coupon, 'currency') and created_stripe_coupon.currency:
            db_coupon_data_for_create_dict['currency'] = created_stripe_coupon.currency
        if hasattr(created_stripe_coupon, 'metadata') and created_stripe_coupon.metadata:
             db_coupon_data_for_create_dict['metadata'] = dict(created_stripe_coupon.metadata)
        
        # times_redeemed は新規作成時は 0 なので、DBモデルのデフォルト値に任せるか、明示的に設定
        # db_coupon_data_for_create_dict['times_redeemed'] = 0 

        # 再度 StripeCouponCreate で Pydantic モデルとしてインスタンス化 (バリデーションのため)
        # ただし、このためには StripeCouponCreate スキーマがこれらのフィールドを許容する必要がある。
        # 一旦、辞書のまま create_db_coupon に渡すことを試みるか、
        # create_db_coupon の引数型を Dict[str, Any] のようにするか検討。
        # ここでは、create_db_coupon が Dict を受け取れるか、
        # または必要なフィールドのみを持つ Pydantic モデルを内部で使うと仮定して進める。

        # DB保存 (create_db_coupon が StripeCouponモデルインスタンスを返すと期待)
        # create_db_coupon の引数 coupon_in が StripeCouponCreate 型であると仮定。
        # このためには、StripeCouponCreate スキーマに stripe_coupon_id 等の追加フィールドが必要。
        # ここでは、一時的に必要な情報を元に再構築する。
        # (より良いのは、Stripe APIレスポンスを直接マッピングできるDB登録用スキーマを用意すること)
        
        # `create_db_coupon` が期待するスキーマに合わせて整形
        # `StripeCouponCreate` をそのまま使う場合、`stripe_coupon_id` 等のフィールドが追加されている前提
        final_db_coupon_data = StripeCouponCreate(
            stripe_coupon_id=created_stripe_coupon.id, 
            name=created_stripe_coupon.name if created_stripe_coupon.name else coupon_data.name, 
            duration=created_stripe_coupon.duration,
            percent_off=created_stripe_coupon.percent_off,
            amount_off=created_stripe_coupon.amount_off,
            currency=created_stripe_coupon.currency,
            duration_in_months=created_stripe_coupon.duration_in_months,
            max_redemptions=getattr(created_stripe_coupon, 'max_redemptions', coupon_data.max_redemptions), # Stripeレスポンスになければユーザー入力をフォールバック
            redeem_by=getattr(created_stripe_coupon, 'redeem_by', coupon_data.redeem_by), # 同上
            metadata=dict(created_stripe_coupon.metadata) if hasattr(created_stripe_coupon, 'metadata') and created_stripe_coupon.metadata else coupon_data.metadata,
            valid=getattr(created_stripe_coupon, 'valid', True),
            created=getattr(created_stripe_coupon, 'created', None),
            livemode=getattr(created_stripe_coupon, 'livemode', False),
            times_redeemed=getattr(created_stripe_coupon, 'times_redeemed', 0),
        )


        logger.debug(f"Attempting to save coupon to DB with data for create_db_coupon: {final_db_coupon_data.model_dump_json(indent=2)}")
        db_coupon_from_crud = await create_db_coupon(db, coupon_in=final_db_coupon_data) # coupon_in の型に注意
        logger.info(f"Successfully saved coupon to DB with ID: {db_coupon_from_crud.id}, Stripe ID: {db_coupon_from_crud.stripe_coupon_id}")

        # クライアントに返す (StripeCouponResponse スキーマで)
        response_data = StripeCouponResponse(
            id=str(db_coupon_from_crud.id),
            stripe_coupon_id=db_coupon_from_crud.stripe_coupon_id,
            name=db_coupon_from_crud.name,
            duration=db_coupon_from_crud.duration,
            valid=db_coupon_from_crud.valid,
            times_redeemed=db_coupon_from_crud.times_redeemed,
            created=db_coupon_from_crud.stripe_created_timestamp,
            amount_off=db_coupon_from_crud.amount_off,
            percent_off=db_coupon_from_crud.percent_off,
            currency=db_coupon_from_crud.currency,
            duration_in_months=db_coupon_from_crud.duration_in_months,
            max_redemptions=db_coupon_from_crud.max_redemptions,
            redeem_by=db_coupon_from_crud.redeem_by_timestamp,
            livemode=db_coupon_from_crud.livemode,
            db_created_at=db_coupon_from_crud.created_at,
            db_updated_at=db_coupon_from_crud.updated_at,
            metadata=db_coupon_from_crud.metadata_
        )
        return response_data

    except stripe.error.StripeError as e:
        logger.error(f"Stripe API error during coupon creation: {str(e)}", exc_info=True)
        detail = f"Stripe APIエラー: {e.user_message}" if hasattr(e, 'user_message') and e.user_message else f"Stripe APIエラー: {str(e)}"
        raise HTTPException(
            status_code=e.http_status if hasattr(e, 'http_status') else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )
    except HTTPException: # 内部で発生した HTTPException はそのまま raise
        raise
    except Exception as e:
        logger.error(f"Unexpected error during coupon creation and import: {str(e)}", exc_info=True)
        # トランザクション中であればロールバック試行 (get_async_db でのจัดการを期待)
        # if db.in_transaction(): # in_transaction は同期セッションのメソッド。非同期では異なる。
        #     try:
        #         await db.rollback()
        #         logger.info("Transaction rolled back due to unexpected error.")
        #     except Exception as rb_exc:
        #         logger.error(f"Failed to rollback transaction: {rb_exc}", exc_info=True)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"クーポンの作成とインポート中に予期せぬエラーが発生しました。" # エラー詳細はログで確認
        )

# GET /stripe-coupons/{coupon_db_id} (DB 個別取得)
@router.get(
    "/stripe-coupons/{coupon_db_id}",
    response_model=StripeCouponResponse,
    summary="Get DB Coupon by DB ID",
    dependencies=[Depends(require_permission('admin_access', 'stripe_coupon_read'))]
)
async def read_db_coupon(
    coupon_db_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    # current_user: User = Depends(require_permission('admin_access', 'stripe_coupon_read')),
):
    """指定されたDB IDを持つStripe Couponをデータベースから取得します。"""
    logger.info(f"Fetching DB Coupon with DB ID: {coupon_db_id}")
    db_coupon = await get_db_coupon(db, coupon_id=coupon_db_id)
    if db_coupon is None:
        logger.warning(f"DB Coupon with DB ID {coupon_db_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DB Coupon not found")
    logger.info(f"Found DB Coupon {coupon_db_id} (Stripe ID: {db_coupon.stripe_coupon_id})")
    return db_coupon

# PUT /stripe-coupons/{coupon_db_id} (更新 Stripe+DB)
@router.put(
    "/stripe-coupons/{coupon_db_id}",
    response_model=StripeCouponResponse,
    summary="Update Stripe Coupon and DB",
    dependencies=[Depends(require_permission('admin_access', 'stripe_coupon_write'))]
)
async def update_stripe_coupon_and_db(
    coupon_db_id: UUID,
    coupon_update: StripeCouponUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('admin_access', 'stripe_coupon_write'))
):
    """
    指定されたDB IDのCouponについて、Stripe APIとDBの両方を更新します。
    (中略) ... エンドポイントの実装 ...
    """
    # ... (前回までの実装) ...
    pass # Placeholder for actual implementation

# DELETE /stripe-coupons/{coupon_db_id} (削除 Stripe+DB)
@router.delete(
    "/stripe-coupons/{coupon_db_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Stripe Coupon and DB Record",
    dependencies=[Depends(require_permission('admin_access', 'stripe_coupon_write'))]
)
async def delete_stripe_coupon_and_db(
    coupon_db_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission('admin_access', 'stripe_coupon_write'))
):
    """
    指定されたDB IDのCouponについて、Stripe APIとDBの両方から削除します。
    (中略) ... エンドポイントの実装 ...
    """
    # --- DBからのクーポン削除 ---
    try:
        # delete_db_coupon は bool を返すので、変数名を適切にし、条件分岐を修正
        was_deleted = await delete_db_coupon(db, coupon_id=coupon_db_id)
        if not was_deleted: # False の場合 (見つからなかった、または削除に失敗してFalseを返した場合など)
            # delete_db_coupon が False を返すのは「見つからない」場合のみなので、このメッセージは適切
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DBクーポンの削除対象が見つかりませんでした。")
        logger.info(f"Successfully deleted DB coupon ID: {coupon_db_id}")
        # HTTP_204_NO_CONTENT の場合、レスポンスボディは返さないのが一般的
        # FastAPI は status_code=204 の場合、ルートハンドラが何も返さないか None を返すと適切に処理する
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DB coupon deletion failed for {coupon_db_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="DBクーポンの削除処理中に予期せぬエラーが発生しました")
    
    return None # HTTP 204 No Content の場合は None を返すのが明示的で良い

# ---------- ロール関連のエンドポイント ---------- #
@router.get(
    "/roles",
    response_model=List[RoleRead], # ★ RoleRead に変更
    summary="List All Roles",
    dependencies=[Depends(require_permission('admin_access', 'role_read'))]
)
async def admin_get_all_roles(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
):
    """
    システムに登録されている全てのロールの一覧を取得します。
    フロントエンドの商品設定画面で「割り当てるロール」の選択肢として使用することを想定しています。

    **必要な権限:** `admin_access`, `role_read`
    """
    roles = await crud_role.get_roles(db=db, skip=skip, limit=limit)
    return roles

# ... (既存のユーザー関連、商品関連などのエンドポイント) ... 