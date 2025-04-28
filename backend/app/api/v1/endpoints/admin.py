from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
import stripe # エラーハンドリング用に追加
import logging # ロギング用に追加
from uuid import UUID

from app.core.config import settings
from app.api.deps import get_db
from app.api.deps import require_permission
from app.services.stripe_service import StripeService # StripeServiceをインポート
# Pydanticスキーマのインポート (後で追加する可能性あり)
# from app.schemas.stripe import ProductCreate, ProductUpdate, PriceCreate, PriceUpdate # 例

from app.schemas.subscription import (
    CampaignCodeCreate, 
    CampaignCodeResponse,
    DiscountTypeCreate, DiscountTypeResponse, DiscountTypeUpdate
)
from app.crud.subscription import (
    create_campaign_code,
    get_campaign_code,
    get_all_campaign_codes,
    update_campaign_code,
    delete_campaign_code,
    create_discount_type, get_all_discount_types, get_discount_type,
    update_discount_type, delete_discount_type, get_discount_type_by_name
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

# ---------- キャンペーンコード関連のエンドポイント ---------- #

@router.get("/campaign-codes", response_model=List[CampaignCodeResponse])
async def admin_get_campaign_codes(
    skip: int = 0,
    limit: int = 100,
    owner_id: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(require_permission('admin_access', 'campaign_code_read')),
):
    """
    キャンペーンコード一覧を取得します。
    管理者専用エンドポイント。
    """
    # owner_idが指定されている場合
    if owner_id:
        try:
            uuid_owner_id = UUID(owner_id)
            return get_user_campaign_codes(db, uuid_owner_id, skip, limit)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無効なowner_id形式です"
            )
    # owner_idが指定されていない場合は全て取得
    else:
        return get_all_campaign_codes(db, skip, limit)

@router.post("/campaign-codes", response_model=CampaignCodeResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_campaign_code(
    campaign_code: CampaignCodeCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(require_permission('admin_access', 'campaign_code_write')),
):
    """
    新しいキャンペーンコードを作成します。
    管理者専用エンドポイント。
    """
    # create_campaign_code に creator=current_user を渡す
    return create_campaign_code(db=db, campaign_code=campaign_code, creator=current_user)

@router.delete("/campaign-codes/{campaign_code_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_campaign_code(
    campaign_code_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(require_permission('admin_access', 'campaign_code_write')),
):
    """
    キャンペーンコードを削除します。
    管理者専用エンドポイント。
    """
    try:
        uuid_campaign_code_id = UUID(campaign_code_id)
        delete_campaign_code(db, uuid_campaign_code_id)
        return None
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無効なcampaign_code_id形式です"
        ) 

# ---------- 割引タイプ関連のエンドポイント ---------- #

@router.get("/discount-types", response_model=List[DiscountTypeResponse])
async def admin_get_discount_types(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(require_permission('admin_access', 'discount_type_read')),
):
    """割引タイプ一覧を取得します。"""
    discount_types = get_all_discount_types(db, skip=skip, limit=limit)
    return discount_types

@router.post("/discount-types", response_model=DiscountTypeResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_discount_type(
    discount_type_in: DiscountTypeCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(require_permission('admin_access', 'discount_type_write')),
):
    """新しい割引タイプを作成します。"""
    try:
        return create_discount_type(db=db, discount_type=discount_type_in)
    except HTTPException as e: # 重複エラーなどをキャッチ
        raise e
    except Exception as e:
        logger.error(f"割引タイプの作成中に予期せぬエラー: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.put("/discount-types/{discount_type_id}", response_model=DiscountTypeResponse)
async def admin_update_discount_type(
    discount_type_id: UUID,
    discount_type_in: DiscountTypeUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(require_permission('admin_access', 'discount_type_write')),
):
    """割引タイプを更新します。"""
    try:
        updated_discount_type = update_discount_type(db, discount_type_id, discount_type_in)
        if not updated_discount_type:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discount type not found")
        return updated_discount_type
    except HTTPException as e: # 重複エラーなどをキャッチ
        raise e
    except Exception as e:
        logger.error(f"割引タイプの更新中に予期せぬエラー: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete("/discount-types/{discount_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_discount_type(
    discount_type_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(require_permission('admin_access', 'discount_type_write')),
):
    """割引タイプを削除します。"""
    deleted = delete_discount_type(db, discount_type_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discount type not found")
    return None 