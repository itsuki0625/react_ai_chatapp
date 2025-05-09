from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
import uuid
import logging

from app.models.subscription import Subscription, PaymentHistory, CampaignCode, StripeCoupon, SubscriptionPlan, StripeDbProduct
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionCreate,
    PaymentHistoryCreate,
    CampaignCodeCreate,
    CampaignCodeUpdate,
    StripeCouponCreate,
    StripeCouponUpdate,
    StripeCouponResponse,
    SubscriptionPlanCreate,
    SubscriptionPlanUpdate
)
from app.schemas.stripe import StripeDbProductCreate, StripeDbProductUpdate, StripeDbProductResponse
from app.services.stripe_service import StripeService
import stripe

logger = logging.getLogger(__name__)

# --- サブスクリプションのCRUD操作 ---
async def create_subscription(db: AsyncSession, subscription: SubscriptionCreate) -> Subscription:
    db_plan = None
    # price_id が渡されているか確認 (SubscriptionCreateにprice_idはOptionalなので)
    # ただし、webhookからの new_sub_data には price_id を設定しているはず
    effective_price_id = subscription.price_id 
    if not effective_price_id and subscription.plan_id:
         # plan_idからplanを取得してprice_idを逆引きすることも可能だが、
         # webhookのロジックでprice_idは設定されているはずなので、ここではエラーや警告を出すことを検討
         logger.warning(f"SubscriptionCreate に price_id がありません。plan_id: {subscription.plan_id} から特定を試みます（非推奨）")
         # temp_plan = await get_plan_by_id(db, subscription.plan_id) # get_plan_by_id が必要
         # if temp_plan: effective_price_id = temp_plan.price_id
         # else: raise HTTPException(...)

    if effective_price_id:
        db_plan = await get_plan_by_price_id(db, stripe_price_id=effective_price_id)
        if not db_plan:
            logger.error(f"DBに Price ID '{effective_price_id}' に対応するプランが見つかりません。")
            raise HTTPException(status_code=404, detail=f"Plan not found for price_id: {effective_price_id}")
        # スキーマのplan_idとDBから引いたプランのIDが一致するか確認（念のため）
        if subscription.plan_id != db_plan.id:
            logger.warning(f"SubscriptionCreate の plan_id ({subscription.plan_id}) と Price ID ({effective_price_id}) から引いた Plan ID ({db_plan.id}) が一致しません。DB Plan ID を優先します。")
            subscription.plan_id = db_plan.id # DBから引いたもので上書き

    elif not subscription.plan_id: # price_id も plan_id もない場合 (通常Webhookからはありえないはず)
        logger.error("SubscriptionCreate に price_id も plan_id も提供されていません。")
        raise HTTPException(status_code=400, detail="Either price_id or plan_id must be provided.")
    
    # SQLAlchemyモデルに渡すデータを作成
    # SubscriptionCreateからprice_idとplan_nameを除外 (plan_nameはモデルにない、price_idもスキーマにはあるがモデルには直接ない)
    subscription_model_data = subscription.model_dump(exclude={"price_id", "plan_name"}) 

    # Subscription SQLAlchemyモデルのインスタンスを作成
    try:
        db_subscription = Subscription(**subscription_model_data)
    except TypeError as e:
        logger.error(f"Subscriptionモデルの初期化に失敗しました。渡されたデータ: {subscription_model_data}, エラー: {e}", exc_info=True)
        # エラーメッセージから問題のフィールドを特定し、より詳細なエラーを返すことも検討
        raise HTTPException(status_code=500, detail=f"データベースモデルの作成に失敗しました: {e}")

    db.add(db_subscription)
    try:
        await db.commit()
        await db.refresh(db_subscription)
    except Exception as e:
        await db.rollback()
        logger.error(f"Subscription DB保存中にエラー: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="データベースへの保存中にエラーが発生しました。")
        
    return db_subscription

async def get_subscription(db: AsyncSession, subscription_id: UUID) -> Optional[Subscription]:
    result = await db.execute(select(Subscription).filter(Subscription.id == subscription_id))
    return result.scalars().first()

async def get_user_subscriptions(db: AsyncSession, user_id: UUID) -> List[Subscription]:
    result = await db.execute(select(Subscription).filter(Subscription.user_id == user_id))
    return result.scalars().all()

async def get_active_user_subscription(db: AsyncSession, user_id: UUID) -> Optional[Subscription]:
    result = await db.execute(
        select(Subscription)
        .options(selectinload(Subscription.plan))
        .filter(
            Subscription.user_id == user_id,
            Subscription.is_active == True,
            Subscription.status.in_( ["active", "trialing"] ),
        )
    )
    return result.scalars().first()

async def get_subscription_by_stripe_id(db: AsyncSession, stripe_subscription_id: str) -> Optional[Subscription]:
    result = await db.execute(
        select(Subscription).filter(Subscription.stripe_subscription_id == stripe_subscription_id)
    )
    return result.scalars().first()

async def update_subscription(db: AsyncSession, subscription_id: UUID, subscription_data: dict) -> Optional[Subscription]:
    subscription = await get_subscription(db, subscription_id)
    if subscription:
        for key, value in subscription_data.items():
            setattr(subscription, key, value)
        await db.commit()
        await db.refresh(subscription)
    return subscription

async def cancel_subscription(db: AsyncSession, subscription_id: UUID, canceled_at: datetime = None) -> Optional[Subscription]:
    subscription = await get_subscription(db, subscription_id)
    if subscription:
        subscription.status = "canceled"
        subscription.canceled_at = canceled_at or datetime.utcnow()
        subscription.is_active = False
        await db.commit()
        await db.refresh(subscription)
    return subscription

# --- 支払い履歴のCRUD操作 ---
async def create_payment_history(db: AsyncSession, payment: PaymentHistoryCreate) -> PaymentHistory:
    db_payment = PaymentHistory(**payment.dict())
    db.add(db_payment)
    await db.commit()
    await db.refresh(db_payment)
    return db_payment

async def get_payment_history(db: AsyncSession, payment_id: UUID) -> Optional[PaymentHistory]:
    result = await db.execute(
        select(PaymentHistory).filter(PaymentHistory.id == payment_id)
    )
    return result.scalars().first()

async def get_user_payment_history(db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 100) -> List[PaymentHistory]:
    result = await db.execute(
        select(PaymentHistory)
        .filter(PaymentHistory.user_id == user_id)
        .order_by(PaymentHistory.payment_date.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_payment_by_stripe_id(db: AsyncSession, stripe_payment_intent_id: str) -> Optional[PaymentHistory]:
    result = await db.execute(
        select(PaymentHistory).filter(PaymentHistory.stripe_payment_intent_id == stripe_payment_intent_id)
    )
    return result.scalars().first()

async def update_payment_history(db: AsyncSession, payment_id: UUID, payment_data: dict) -> Optional[PaymentHistory]:
    payment = await get_payment_history(db, payment_id)
    if payment:
        for key, value in payment_data.items():
            setattr(payment, key, value)
        await db.commit()
        await db.refresh(payment)
    return payment

# --- ★ StripeCoupon CRUD 操作 ---

async def create_db_coupon(db: AsyncSession, coupon_in: StripeCouponCreate) -> StripeCoupon:
    """DBにStripeCouponレコードを作成"""
    if not coupon_in.stripe_coupon_id:
        logger.error("create_db_coupon called without stripe_coupon_id in coupon_in")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="stripe_coupon_id is required to create a DB coupon record."
        )

    existing_coupon = await get_db_coupon_by_stripe_id(db, coupon_in.stripe_coupon_id)
    if existing_coupon:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Stripe Coupon ID '{coupon_in.stripe_coupon_id}' already exists in DB."
        )

    db_coupon_fields = coupon_in.model_dump(exclude_unset=True)

    if 'metadata' in db_coupon_fields:
        db_coupon_fields['metadata_'] = db_coupon_fields.pop('metadata')
    else:
        db_coupon_fields['metadata_'] = None

    # スキーマの `redeem_by` (int) をモデルの `redeem_by_timestamp` (int) にマッピング
    if 'redeem_by' in db_coupon_fields and db_coupon_fields['redeem_by'] is not None:
        db_coupon_fields['redeem_by_timestamp'] = db_coupon_fields.pop('redeem_by')
    elif 'redeem_by' in db_coupon_fields: # redeem_by が None の場合
        db_coupon_fields.pop('redeem_by') # redeem_by_timestamp には設定しない (モデル側で nullable)

    # スキーマの `created` (Stripeのintタイムスタンプ) をモデルの `stripe_created_timestamp` (int) にマッピング
    if 'created' in db_coupon_fields and db_coupon_fields['created'] is not None:
        db_coupon_fields['stripe_created_timestamp'] = db_coupon_fields.pop('created')
    elif 'created' in db_coupon_fields: # created が None の場合
        db_coupon_fields.pop('created')

    # `id` は coupon_in に含まれないので削除 (DBで自動生成)
    # また、StripeCouponCreate には db_created_at, db_updated_at はないので、それらも除外
    db_coupon_fields.pop('id', None)
    db_coupon_fields.pop('db_created_at', None) 
    db_coupon_fields.pop('db_updated_at', None)

    try:
        logger.debug(f"Creating StripeCoupon DB model instance with fields: {db_coupon_fields}")
        db_coupon = StripeCoupon(**db_coupon_fields)
    except TypeError as e:
        logger.error(f"Error creating StripeCoupon model instance: {e}. Fields: {db_coupon_fields}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DB Couponモデルの作成に失敗しました。フィールドの不整合の可能性があります: {str(e)}"
        )

    db.add(db_coupon)
    try:
        await db.commit()
        await db.refresh(db_coupon)
        logger.info(f"DB Coupon record created successfully. DB ID: {db_coupon.id}, Stripe ID: {db_coupon.stripe_coupon_id}")
        return db_coupon
    except IntegrityError as e: 
        await db.rollback()
        logger.error(f"DB Coupon 作成エラー (IntegrityError) for Stripe ID {coupon_in.stripe_coupon_id}: {e}", exc_info=True)
        original_error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        if "violates unique constraint" in original_error_msg or "already exists" in original_error_msg:
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"DB Coupon record conflict: {original_error_msg}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"DB Coupon作成時にデータ整合性エラーが発生しました: {original_error_msg}")
    except Exception as e:
        await db.rollback()
        logger.error(f"DB Coupon 作成エラー (Stripe ID: {coupon_in.stripe_coupon_id}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="DB Couponの作成に失敗しました。")

async def get_db_coupon(db: AsyncSession, coupon_id: UUID) -> Optional[StripeCoupon]:
    result = await db.execute(select(StripeCoupon).filter(StripeCoupon.id == coupon_id))
    return result.scalars().first()

async def get_db_coupon_by_stripe_id(db: AsyncSession, stripe_coupon_id: str) -> Optional[StripeCoupon]:
    """Stripe Coupon IDでStripeCouponレコードを取得"""
    result = await db.execute(select(StripeCoupon).filter(StripeCoupon.stripe_coupon_id == stripe_coupon_id))
    return result.scalars().first()

async def get_all_db_coupons(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[StripeCoupon]:
    """DB上のStripeCouponレコード一覧を取得"""
    result = await db.execute(
        select(StripeCoupon)
        .order_by(StripeCoupon.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def update_db_coupon(db: AsyncSession, coupon_id: UUID, coupon_update: StripeCouponUpdate) -> Optional[StripeCoupon]:
    db_coupon = await get_db_coupon(db, coupon_id)
    if not db_coupon:
        return None

    update_data = coupon_update.model_dump(exclude_unset=True)
    if not update_data: # 更新データがなければ何もしない
        return db_coupon

    logger.debug(f"Updating DB Coupon {coupon_id} with data: {update_data}")
    for key, value in update_data.items():
        setattr(db_coupon, key, value)

    # updated_at は自動更新されるはずだが、明示的に更新しても良い
    # db_coupon.updated_at = datetime.now(timezone.utc)

    try:
        await db.commit()
        await db.refresh(db_coupon)
        logger.info(f"Successfully updated DB Coupon {coupon_id}")
        return db_coupon
    except Exception as e:
        await db.rollback()
        logger.error(f"Error committing DB update for Coupon {coupon_id}: {e}", exc_info=True)
        raise # エラーを再raiseしてエンドポイント側で処理

async def delete_db_coupon(db: AsyncSession, coupon_id: UUID) -> bool:
    db_coupon = await get_db_coupon(db, coupon_id)
    if not db_coupon:
        return False # 対象が見つからない

    logger.info(f"Deleting DB Coupon {coupon_id} (Stripe ID: {db_coupon.stripe_coupon_id})")
    try:
        await db.delete(db_coupon)
        await db.commit()
        logger.info(f"Successfully deleted DB Coupon {coupon_id}")
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"Error committing DB deletion for Coupon {coupon_id}: {e}", exc_info=True)
        raise # エラーを再raiseしてエンドポイント側で処理

# --- CampaignCode CRUD 操作 (修正) ---

async def create_campaign_code(db: AsyncSession, campaign_code: CampaignCodeCreate, creator: User) -> CampaignCode:
    # ── DB に存在しなければ Stripe から取得して登録 ──
    db_coupon = await get_db_coupon_by_stripe_id(db, campaign_code.stripe_coupon_id)
    if not db_coupon:
        logger.warning(f"Stripe Coupon ID {campaign_code.stripe_coupon_id} provided but not found in DB. Attempting to import from Stripe.") # ログ追加
        try:
            # Stripe API からクーポン取得
            # ★ StripeService を経由するように修正
            stripe_obj = StripeService.retrieve_coupon(campaign_code.stripe_coupon_id) # await を削除

            # DB スキーマに沿ってインサート
            # ★ StripeCouponCreate のフィールドに合わせて調整が必要
            coupon_in = StripeCouponCreate(
                stripe_coupon_id=stripe_obj.id, # .id でアクセス
                amount_off=stripe_obj.get('amount_off'), # .get()で安全にアクセス
                percent_off=stripe_obj.get('percent_off'), # .get()で安全にアクセス
                name=stripe_obj.get('name'), # .get()で安全にアクセス
                duration=stripe_obj.get('duration'), # .get()で安全にアクセス
                duration_in_months=stripe_obj.get('duration_in_months'), # .get()で安全にアクセス
                redeem_by=stripe_obj.get('redeem_by'), # Unix タイムスタンプ (int) なのでそのまま渡す
                metadata=stripe_obj.get('metadata'), # .get()で安全にアクセス
                livemode=stripe_obj.get('livemode'), # .get()で安全にアクセス
                valid=stripe_obj.get('valid'),
                created=stripe_obj.get('created')
            )
            logger.info(f"Importing Stripe Coupon {stripe_obj.id} into DB.")
            db_coupon = await create_db_coupon(db, coupon_in)
            logger.info(f"Successfully imported Stripe Coupon {stripe_obj.id} as DB Coupon {db_coupon.id}.")
        except stripe.error.InvalidRequestError as e: 
             if "No such coupon" in str(e):
                 logger.error(f"Stripe Coupon {campaign_code.stripe_coupon_id} not found on Stripe either.")
                 raise HTTPException(
                     status_code=status.HTTP_404_NOT_FOUND,
                     detail=f"Stripe Coupon with ID '{campaign_code.stripe_coupon_id}' not found on Stripe."
                 )
             else:
                 logger.error(f"Stripe API error while retrieving coupon {campaign_code.stripe_coupon_id}: {e}")
                 raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve coupon from Stripe.")
        except HTTPException as e: 
            logger.error(f"Error retrieving/importing coupon {campaign_code.stripe_coupon_id} via StripeService: {e.detail}")
            raise 
        except Exception as e:
            logger.exception(f"Unexpected error during Stripe Coupon import for {campaign_code.stripe_coupon_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to import coupon from Stripe.")
    # ─────────────────────────────────────────────

    # タイムゾーン除去 (valid_from, valid_until がスキーマに残っている場合)
    naive_valid_from = campaign_code.valid_from.replace(tzinfo=None) if campaign_code.valid_from else None
    naive_valid_until = campaign_code.valid_until.replace(tzinfo=None) if campaign_code.valid_until else None

    # --- Stripe Promotion Code 作成処理 ---
    created_stripe_promo_code_id: Optional[str] = None
    try:
        stripe_promo_code = StripeService.create_promotion_code(
            coupon_id=db_coupon.stripe_coupon_id, # ★ DBから取得した Coupon の Stripe ID
            code=campaign_code.code,
            max_redemptions=campaign_code.max_uses,
            # expires_at は datetime オブジェクトを渡す (StripeService内で変換)
            expires_at=naive_valid_until,
            metadata={
                "db_campaign_code_creator": str(creator.id),
                "db_coupon_id": str(db_coupon.id), # DBのCoupon IDもメタデータに含める
                "description": campaign_code.description or ""
            }
        )
        if stripe_promo_code:
             created_stripe_promo_code_id = stripe_promo_code.id
    except HTTPException as e:
         raise e
    except Exception as e:
         logger.error(f"Stripe Promotion Code作成呼び出し中にエラー: {e}", exc_info=True)
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Stripe連携中にエラーが発生しました。")

    # DBに保存する CampaignCode オブジェクトを作成
    db_campaign_code = CampaignCode(
        code=campaign_code.code,
        description=campaign_code.description,
        max_uses=campaign_code.max_uses,
        valid_from=naive_valid_from,
        valid_until=naive_valid_until,
        is_active=campaign_code.is_active,
        created_by=creator.id,
        stripe_promotion_code_id=created_stripe_promo_code_id, # ★ 保存
        coupon_id=db_coupon.id # ★ DB Coupon の ID を保存
    )
    db.add(db_campaign_code)

    try:
        await db.commit()
        await db.refresh(db_campaign_code)
    except IntegrityError:
        await db.rollback()
        if created_stripe_promo_code_id:
             try:
                 logger.warning(f"DB保存失敗(IntegrityError)のため、作成済みのStripe Promotion Code {created_stripe_promo_code_id} を無効化します。")
                 StripeService.archive_promotion_code(created_stripe_promo_code_id)
             except Exception as e_archive:
                 logger.error(f"重複エラー時のStripe Promotion Code ({created_stripe_promo_code_id}) 無効化に失敗: {e_archive}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Campaign code '{campaign_code.code}' already exists in DB."
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"DBコミット中にエラー: {e}", exc_info=True)
        if created_stripe_promo_code_id:
             try:
                 logger.warning(f"DBコミット失敗のため、作成済みのStripe Promotion Code {created_stripe_promo_code_id} を無効化します。")
                 StripeService.archive_promotion_code(created_stripe_promo_code_id)
             except Exception as e_archive:
                 logger.error(f"コミット失敗時のStripe Promotion Code ({created_stripe_promo_code_id}) 無効化に失敗: {e_archive}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="データベースへの保存中にエラーが発生しました。")

    return db_campaign_code

async def get_campaign_code(db: AsyncSession, campaign_code_id: UUID) -> Optional[CampaignCode]:
    # --- ★ Coupon 情報も一緒にロード ---
    result = await db.execute(
        select(CampaignCode)
        .options(selectinload(CampaignCode.coupon)) # Couponリレーションをロード
        .filter(CampaignCode.id == campaign_code_id)
    )
    return result.scalars().first()

async def get_campaign_code_by_code(db: AsyncSession, code: str) -> Optional[CampaignCode]:
    # --- ★ Coupon 情報も一緒にロード ---
    result = await db.execute(
        select(CampaignCode)
        .options(selectinload(CampaignCode.coupon)) # Couponリレーションをロード
        .filter(CampaignCode.code == code)
    )
    return result.scalars().first()

async def get_all_campaign_codes(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
):
    """
    Retrieve all campaign codes.
    """
    query = select(CampaignCode)
    # is_active フィルタが指定されたら絞り込む
    if is_active is not None:
        query = query.where(CampaignCode.is_active == is_active)
    query = query.order_by(CampaignCode.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def get_user_campaign_codes(db: AsyncSession, owner_id: UUID, skip: int = 0, limit: int = 100) -> List[CampaignCode]:
    result = await db.execute(
        select(CampaignCode)
        # .filter(CampaignCode.owner_id == owner_id) # owner_id は削除したので created_by でフィルタするか検討
        .filter(CampaignCode.created_by == owner_id) # created_by でフィルタ
        .options(selectinload(CampaignCode.coupon)) # Couponリレーションをロード
        .order_by(CampaignCode.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().unique().all()

async def update_campaign_code(db: AsyncSession, campaign_code_id: UUID, campaign_code_data: CampaignCodeUpdate) -> Optional[CampaignCode]:
    # --- ★ Coupon 情報も一緒にロード ---
    campaign_code = await get_campaign_code(db, campaign_code_id) # get_campaign_code がロードする
    if campaign_code:
        update_data = campaign_code_data.model_dump(exclude_unset=True)

        # --- ★ is_active が False に更新されたら Stripe Promotion Code も無効化 ---
        if 'is_active' in update_data and update_data['is_active'] is False and campaign_code.stripe_promotion_code_id:
            try:
                logger.info(f"CampaignCode {campaign_code.code} が非アクティブ化されたため、Stripe Promotion Code {campaign_code.stripe_promotion_code_id} を無効化します。")
                StripeService.archive_promotion_code(campaign_code.stripe_promotion_code_id)
            except Exception as e_archive:
                # 無効化に失敗してもDB更新は続行する（エラーログは残す）
                 logger.error(f"Stripe Promotion Code ({campaign_code.stripe_promotion_code_id}) の無効化に失敗 (DB更新は続行): {e_archive}")
        # --- ★ ここまで追加 ---

        for key, value in update_data.items():
            setattr(campaign_code, key, value)
        try:
            await db.commit()
            await db.refresh(campaign_code)
        except Exception as e:
            await db.rollback()
            logger.error(f"Campaign Code 更新エラー (ID: {campaign_code_id}): {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="キャンペーンコードの更新に失敗しました。")
    return campaign_code

async def increment_campaign_code_usage(db: AsyncSession, campaign_code_id: UUID) -> Optional[CampaignCode]:
    campaign_code = await get_campaign_code(db, campaign_code_id)
    if campaign_code:
        campaign_code.used_count += 1
        await db.commit()
        await db.refresh(campaign_code)
    return campaign_code

async def delete_campaign_code(db: AsyncSession, campaign_code_id: UUID) -> bool:
    campaign_code = await get_campaign_code(db, campaign_code_id)
    if campaign_code:
        # --- ★ Stripe Promotion Code を無効化 ---
        if campaign_code.stripe_promotion_code_id:
            try:
                logger.info(f"CampaignCode {campaign_code.code} 削除のため、Stripe Promotion Code {campaign_code.stripe_promotion_code_id} を無効化します。")
                StripeService.archive_promotion_code(campaign_code.stripe_promotion_code_id)
            except Exception as e_archive:
                # 無効化に失敗してもDB削除は続行する（エラーログは残す）
                 logger.error(f"Stripe Promotion Code ({campaign_code.stripe_promotion_code_id}) の無効化に失敗 (DB削除は続行): {e_archive}")
        # --- ★ ここまで追加 ---
        try:
            await db.delete(campaign_code) # SQLAlchemy 2.0 スタイル
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Campaign Code 削除エラー (ID: {campaign_code_id}): {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="キャンペーンコードの削除に失敗しました。")
    return False

async def verify_campaign_code(db: AsyncSession, code: str, price_id: str) -> Dict[str, Any]:
    # --- ★ Coupon 情報を含めて取得 ---
    campaign_code = await get_campaign_code_by_code(db, code) # get_campaign_code_by_code がロードする

    # --- 1. CampaignCode自体の存在と有効性チェック --- 
    if not campaign_code:
        return {
            "valid": False, "message": "指定されたキャンペーンコードは存在しません",
            "campaign_code_id": None, "coupon_id": None, "stripe_coupon_id": None,
            "discount_type": None, "discount_value": None,
            "original_amount": None, "discounted_amount": None
        }

    if not campaign_code.is_valid: # is_valid プロパティを使用
        message = "このキャンペーンコードは現在利用できません。"
        if not campaign_code.is_active: message = "このキャンペーンコードは無効化されています。"
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        aware_valid_from = campaign_code.valid_from.replace(tzinfo=timezone.utc) if campaign_code.valid_from else None
        aware_valid_until = campaign_code.valid_until.replace(tzinfo=timezone.utc) if campaign_code.valid_until else None
        if aware_valid_from and aware_valid_from > now: message = f"このキャンペーンコードは {campaign_code.valid_from.strftime('%Y-%m-%d')} から有効になります"
        if aware_valid_until and aware_valid_until < now: message = "このキャンペーンコードは期限切れです"
        if campaign_code.max_uses is not None and campaign_code.used_count >= campaign_code.max_uses: message = "このキャンペーンコードは使用可能回数を超えています"
        return {
            "valid": False, "message": message, "campaign_code_id": campaign_code.id,
            "coupon_id": campaign_code.coupon_id,
            "stripe_coupon_id": campaign_code.coupon.stripe_coupon_id if campaign_code.coupon else None,
            "discount_type": None, "discount_value": None,
            "original_amount": None, "discounted_amount": None
        }

    # --- 2. Stripe Promotion Code の状態も確認 (DBにIDがあれば) --- 
    if campaign_code.stripe_promotion_code_id:
        try:
            stripe_promo_code = StripeService.retrieve_promotion_code(campaign_code.stripe_promotion_code_id)
            if not stripe_promo_code or not stripe_promo_code.get('active'):
                 return {
                    "valid": False, "message": "このキャンペーンコードは現在利用できません(Stripe側)。", # メッセージ変更
                    "campaign_code_id": campaign_code.id, "coupon_id": campaign_code.coupon_id,
                    "stripe_coupon_id": campaign_code.coupon.stripe_coupon_id if campaign_code.coupon else None,
                    "discount_type": None, "discount_value": None,
                    "original_amount": None, "discounted_amount": None
                 }
            # Coupon ID の整合性チェック
            if campaign_code.coupon and campaign_code.coupon.stripe_coupon_id != stripe_promo_code.get('coupon', {}).get('id'):
                 logger.error(f"DBとStripeでPromotion Code ({campaign_code.stripe_promotion_code_id}) に紐づくCoupon IDが不一致です。")
                 return {
                    "valid": False, "message": "キャンペーンコードの設定に問題があります(Coupon不一致)。",
                    "campaign_code_id": campaign_code.id, "coupon_id": campaign_code.coupon_id,
                    "stripe_coupon_id": None,
                    "discount_type": None, "discount_value": None,
                    "original_amount": None, "discounted_amount": None
                 }
        except HTTPException as e:
             logger.warning(f"Stripe Promotion Code ({campaign_code.stripe_promotion_code_id}) の取得に失敗: {e.detail}")
             return {
                 "valid": False, "message": "キャンペーンコードの状態を確認できませんでした。",
                 "campaign_code_id": campaign_code.id, "coupon_id": campaign_code.coupon_id, "stripe_coupon_id": None,
                 "discount_type": None, "discount_value": None,
                 "original_amount": None, "discounted_amount": None
             }
        except Exception as e:
             logger.error(f"Stripe Promotion Code ({campaign_code.stripe_promotion_code_id}) の取得中に予期せぬエラー: {e}", exc_info=True)
             return {
                 "valid": False, "message": "キャンペーンコードの状態確認中にエラーが発生しました。",
                 "campaign_code_id": campaign_code.id, "coupon_id": campaign_code.coupon_id, "stripe_coupon_id": None,
                 "discount_type": None, "discount_value": None,
                 "original_amount": None, "discounted_amount": None
             }
    else:
        logger.warning(f"CampaignCode {campaign_code.id} に stripe_promotion_code_id がありません。")
        return {
            "valid": False, "message": "キャンペーンコードの設定が不完全です。",
            "campaign_code_id": campaign_code.id, "coupon_id": campaign_code.coupon_id, "stripe_coupon_id": None,
            "discount_type": None, "discount_value": None,
            "original_amount": None, "discounted_amount": None
        }

    # --- 3. 関連する Coupon の存在と有効性チェック --- 
    db_coupon = campaign_code.coupon # selectinload でロード済みのはず
    if not db_coupon:
        logger.error(f"CampaignCode {campaign_code.id} に関連する Coupon がDBで見つかりません。")
        return {
            "valid": False, "message": "キャンペーンコードの設定に問題があります(Coupon欠損)。",
            "campaign_code_id": campaign_code.id, "coupon_id": campaign_code.coupon_id, "stripe_coupon_id": None,
            "discount_type": None, "discount_value": None,
            "original_amount": None, "discounted_amount": None
        }
    if not db_coupon.valid: # ★ is_active から valid に変更
        return {
            "valid": False, "message": "関連するクーポンが無効です。",
            "campaign_code_id": campaign_code.id, "coupon_id": campaign_code.coupon_id,
            "stripe_coupon_id": db_coupon.stripe_coupon_id,
            "discount_type": None, "discount_value": None,
            "original_amount": None, "discounted_amount": None
        }

    logger.info(f"Verifying campaign code: Step 3 completed. DB Coupon valid: {db_coupon.valid}")

    # --- 4. 割引情報の計算 --- 
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    original_amount: Optional[int] = None
    discounted_amount: Optional[int] = None

    try:
        logger.info(f"Verifying campaign code: Attempting to fetch price data for price_id: {price_id}")
        price_data = StripeService.get_price(price_id)
        original_amount = price_data.get("unit_amount")
        logger.info(f"Verifying campaign code: Original amount from Stripe: {original_amount}")

        if original_amount is None:
            logger.error(f"Failed to get original_amount for price_id: {price_id}")
            raise ValueError("価格情報から元の金額を取得できませんでした")

        # DB Coupon 情報から割引を計算
        if db_coupon.percent_off:
            discount_type = "percentage"
            discount_value = db_coupon.percent_off
            discount = int(original_amount * (discount_value / 100))
            discounted_amount = max(0, original_amount - discount)
            logger.info(f"Verifying campaign code: Calculated percentage discount. Type: {discount_type}, Value: {discount_value}, Discounted Amount: {discounted_amount}")
        elif db_coupon.amount_off:
            discount_type = "fixed"
            discount_value = db_coupon.amount_off
            discounted_amount = max(0, original_amount - discount_value)
            logger.info(f"Verifying campaign code: Calculated fixed amount discount. Type: {discount_type}, Value: {discount_value}, Discounted Amount: {discounted_amount}")
        else:
            logger.warning(f"Coupon {db_coupon.id} has no discount information (percent_off/amount_off). Using original amount.")
            discounted_amount = original_amount
            # 割引情報がない場合でも、discount_type や discount_value を何らかの形で設定するか、
            # フロントエンド側でこれらのキーが存在しない場合の表示を考慮する必要があるかもしれません。
            # 例えば、discount_type = "none", discount_value = 0 とするなど。

    except Exception as e:
        logger.error(f"割引計算中にエラーが発生しました (Price ID: {price_id}, Coupon ID: {db_coupon.id}): {e}", exc_info=True)
        # 割引計算エラーの場合はコードを無効として返すのが安全か
        return {
            "valid": False, "message": "割引情報の適用中にエラーが発生しました。",
            "campaign_code_id": campaign_code.id, "coupon_id": db_coupon.id,
            "stripe_coupon_id": db_coupon.stripe_coupon_id,
            "discount_type": None, "discount_value": None,
            "original_amount": original_amount, # 元の金額は返す
            "discounted_amount": None
        }
    
    logger.info(f"Verifying campaign code: Final response being returned: valid={True}, message='有効なキャンペーンコードです', cc_id={campaign_code.id}, c_id={db_coupon.id}, sc_id={db_coupon.stripe_coupon_id}, dtype={discount_type}, dvalue={discount_value}, orig_amt={original_amount}, disc_amt={discounted_amount}")

    # --- 5. 成功レスポンス --- 
    return {
        "valid": True,
        "message": "有効なキャンペーンコードです",
        "campaign_code_id": campaign_code.id,
        "coupon_id": db_coupon.id, # DBのCoupon ID
        "stripe_coupon_id": db_coupon.stripe_coupon_id, # StripeのCoupon ID
        # ★ 割引情報を追加
        "discount_type": discount_type,
        "discount_value": discount_value,
        "original_amount": original_amount,
        "discounted_amount": discounted_amount
    }

# --- Stripe顧客ID 操作 ---
async def get_stripe_customer_id(db: AsyncSession, user_id: UUID) -> Optional[str]:
    subscription = await get_active_user_subscription(db, user_id)
    if subscription:
        return subscription.stripe_customer_id
    return None

async def update_stripe_customer_id(db: AsyncSession, user_id: UUID, stripe_customer_id: str) -> bool:
    subscription = await get_active_user_subscription(db, user_id)
    if subscription:
        subscription.stripe_customer_id = stripe_customer_id
        await db.commit()
        await db.refresh(subscription)
        return True
    return False

# --- ★ Stripe Price IDからプランを取得する関数を追加 --- 
async def get_plan_by_price_id(db: AsyncSession, stripe_price_id: str) -> Optional[SubscriptionPlan]:
    """
    Stripe Price IDを使用してSubscriptionPlanレコードを取得します。
    """
    logger.debug(f"Searching for SubscriptionPlan with Stripe Price ID: {stripe_price_id}")
    result = await db.execute(
        select(SubscriptionPlan).filter(SubscriptionPlan.price_id == stripe_price_id)
    )
    plan = result.scalars().first()
    if plan:
        logger.debug(f"Found SubscriptionPlan: ID={plan.id}, Name={plan.name}")
    else:
        logger.warning(f"SubscriptionPlan not found for Stripe Price ID: {stripe_price_id}")
    return plan
# --- ここまで追加 ---

# --- ★ StripeDBProduct CRUD 操作 --- 
async def create_stripe_db_product(db: AsyncSession, product_in: StripeDbProductCreate) -> StripeDbProduct:
    """DBにStripeDbProductレコードを作成"""
    # Stripe Product IDの重複チェック
    existing_product = await get_stripe_db_product_by_stripe_id(db, product_in.stripe_product_id)
    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Stripe Product ID '{product_in.stripe_product_id}' already exists in DB."
        )
    
    # スキーマのエイリアス(metadata)をモデルのフィールド名(metadata_)に合わせる準備
    product_data = product_in.model_dump(exclude_unset=True)
    if 'metadata' in product_data and product_data['metadata'] is not None: # metadata_ from alias
        product_data['metadata_'] = product_data.pop('metadata')
    elif 'metadata' in product_data: # metadata が None の場合
         product_data.pop('metadata') # metadata_ には設定しない

    db_product = StripeDbProduct(**product_data)
    db.add(db_product)
    try:
        await db.commit()
        await db.refresh(db_product)
        logger.info(f"StripeDbProduct record created: {db_product.id} (Stripe ID: {db_product.stripe_product_id})")
        return db_product
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Error creating StripeDbProduct (IntegrityError) for Stripe ID {product_in.stripe_product_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Database integrity error.")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating StripeDbProduct for Stripe ID {product_in.stripe_product_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create product in DB.")

async def get_stripe_db_product(db: AsyncSession, product_db_id: UUID) -> Optional[StripeDbProduct]:
    """DB UUIDでStripeDbProductレコードを取得"""
    result = await db.execute(select(StripeDbProduct).filter(StripeDbProduct.id == product_db_id))
    return result.scalars().first()

async def get_stripe_db_product_by_stripe_id(db: AsyncSession, stripe_product_id: str) -> Optional[StripeDbProduct]:
    """Stripe Product IDでStripeDbProductレコードを取得"""
    result = await db.execute(select(StripeDbProduct).filter(StripeDbProduct.stripe_product_id == stripe_product_id))
    return result.scalars().first()

async def list_stripe_db_products(db: AsyncSession, skip: int = 0, limit: int = 100, active: Optional[bool] = None) -> List[StripeDbProduct]:
    """DB上のStripeDbProductレコード一覧を取得 (activeフィルタ付き)"""
    query = select(StripeDbProduct).order_by(StripeDbProduct.created_at.desc())
    if active is not None:
        query = query.filter(StripeDbProduct.active == active)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def update_stripe_db_product(db: AsyncSession, product_db_id: UUID, product_in: StripeDbProductUpdate) -> Optional[StripeDbProduct]:
    """DB上のStripeDbProductレコードを更新"""
    db_product = await get_stripe_db_product(db, product_db_id)
    if not db_product:
        return None

    update_data = product_in.model_dump(exclude_unset=True)
    if 'metadata' in update_data and update_data['metadata'] is not None:
        update_data['metadata_'] = update_data.pop('metadata')
    elif 'metadata' in update_data: # metadata が None の場合
         update_data.pop('metadata')

    for key, value in update_data.items():
        setattr(db_product, key, value)
    
    try:
        await db.commit()
        await db.refresh(db_product)
        return db_product
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating StripeDbProduct {product_db_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update product in DB.")

async def delete_stripe_db_product(db: AsyncSession, product_db_id: UUID) -> bool:
    """DB上のStripeDbProductレコードを削除"""
    # TODO: 関連するSubscriptionPlanが存在する場合は削除を拒否するロジックを追加検討
    db_product = await get_stripe_db_product(db, product_db_id)
    if not db_product:
        return False
    
    try:
        await db.delete(db_product)
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting StripeDbProduct {product_db_id}: {e}", exc_info=True)
        # 外部キー制約違反などで削除できない場合のエラーハンドリングを具体的にする
        if "foreign key constraint" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot delete product. It is associated with existing plans or subscriptions.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not delete product from DB.")

# --- ここまで StripeDBProduct CRUD 操作 ---

async def create_subscription_plan(db: AsyncSession, plan_in: SubscriptionPlanCreate) -> SubscriptionPlan:
    """
    新しいSubscriptionPlanレコードをデータベースに作成します。
    """
    # SubscriptionPlanCreate スキーマのデータをモデルのフィールドにマッピング
    db_plan = SubscriptionPlan(
        name=plan_in.name,
        description=plan_in.description,
        price_id=plan_in.price_id,
        stripe_db_product_id=plan_in.stripe_db_product_id,
        amount=plan_in.amount,
        currency=plan_in.currency,
        interval=plan_in.interval,
        interval_count=plan_in.interval_count,
        is_active=plan_in.is_active,
        features=plan_in.features if plan_in.features is not None else [],
        plan_metadata=plan_in.plan_metadata if plan_in.plan_metadata is not None else {},
        trial_days=plan_in.trial_days
        # created_at, updated_at は TimestampMixin により自動設定
    )
    db.add(db_plan)
    try:
        await db.commit()
        await db.refresh(db_plan)
        logger.info(f"SubscriptionPlan '{db_plan.name}' (ID: {db_plan.id}) created successfully in DB.")
        return db_plan
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating SubscriptionPlan '{plan_in.name}' in DB: {e}", exc_info=True)
        raise # エラーを呼び出し元に再raiseして処理させる

async def update_stripe_db_product_by_stripe_id(db: AsyncSession, stripe_product_id: str, product_update_data: StripeDbProductUpdate) -> Optional[StripeDbProduct]:
    """
    Stripe Product IDを使用してStripeDbProductレコードを更新します。
    """
    db_product = await get_stripe_db_product_by_stripe_id(db, stripe_product_id=stripe_product_id)
    if not db_product:
        logger.warning(f"StripeDbProduct not found with Stripe ID: {stripe_product_id} for update.")
        return None

    update_data = product_update_data.model_dump(exclude_unset=True)
    if 'metadata' in update_data and update_data['metadata'] is not None:
        update_data['metadata_'] = update_data.pop('metadata')
    elif 'metadata' in update_data: # metadata が None の場合
         update_data.pop('metadata')


    for key, value in update_data.items():
        setattr(db_product, key, value)
    
    try:
        await db.commit()
        await db.refresh(db_product)
        logger.info(f"StripeDbProduct with Stripe ID {stripe_product_id} updated successfully.")
        return db_product
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating StripeDbProduct with Stripe ID {stripe_product_id}: {e}", exc_info=True)
        raise # エラーを呼び出し元に再raise

async def update_subscription_plan_by_price_id(db: AsyncSession, price_id: str, plan_update_data: SubscriptionPlanUpdate) -> Optional[SubscriptionPlan]:
    """
    Stripe Price ID を使用して SubscriptionPlan レコードを更新します。
    """
    # 既存の get_plan_by_price_id を使用
    db_plan = await get_plan_by_price_id(db, stripe_price_id=price_id)
    if not db_plan:
        logger.warning(f"SubscriptionPlan not found with Price ID: {price_id} for update.")
        return None

    update_data = plan_update_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_plan, key, value)
    
    try:
        await db.commit()
        await db.refresh(db_plan)
        logger.info(f"SubscriptionPlan with Price ID {price_id} updated successfully.")
        return db_plan
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating SubscriptionPlan with Price ID {price_id}: {e}", exc_info=True)
        raise

async def get_active_subscription_plans(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[SubscriptionPlan]:
    """
    DBからアクティブなSubscriptionPlanのリストを取得します。
    関連するStripeDbProduct情報もEager Loadします。
    """
    result = await db.execute(
        select(SubscriptionPlan)
        .options(selectinload(SubscriptionPlan.stripe_db_product)) # StripeDbProductをEager Load
        .filter(SubscriptionPlan.is_active == True)
        .order_by(SubscriptionPlan.created_at.desc()) # 例: 作成日時の降順
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()