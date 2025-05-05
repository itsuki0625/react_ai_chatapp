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

from app.models.subscription import Subscription, PaymentHistory, CampaignCode, DiscountType, StripeCoupon
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionCreate,
    PaymentHistoryCreate,
    CampaignCodeCreate,
    CampaignCodeUpdate,
    DiscountTypeCreate,
    DiscountTypeUpdate,
    StripeCouponCreate,
    StripeCouponUpdate,
    StripeCouponResponse
)
from app.services.stripe_service import StripeService

logger = logging.getLogger(__name__)

# --- サブスクリプションのCRUD操作 ---
async def create_subscription(db: AsyncSession, subscription: SubscriptionCreate) -> Subscription:
    db_subscription = Subscription(**subscription.dict())
    db.add(db_subscription)
    await db.commit()
    await db.refresh(db_subscription)
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
    # Stripe ID の重複チェック
    existing_coupon = await get_db_coupon_by_stripe_id(db, coupon_in.stripe_coupon_id)
    if existing_coupon:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Stripe Coupon ID '{coupon_in.stripe_coupon_id}' already exists in DB."
        )
    db_coupon = StripeCoupon(
        **coupon_in.model_dump(exclude={'metadata'}), # スキーマから基本情報をコピー
        metadata_=coupon_in.metadata # エイリアスに合わせて設定
    )
    db.add(db_coupon)
    try:
        await db.commit()
        await db.refresh(db_coupon)
        return db_coupon
    except Exception as e:
        await db.rollback()
        logger.error(f"DB Coupon 作成エラー (Stripe ID: {coupon_in.stripe_coupon_id}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="DB Couponの作成に失敗しました。")

async def get_db_coupon(db: AsyncSession, coupon_db_id: UUID) -> Optional[StripeCoupon]:
    """DB UUIDでStripeCouponレコードを取得"""
    result = await db.execute(select(StripeCoupon).filter(StripeCoupon.id == coupon_db_id))
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

async def update_db_coupon(db: AsyncSession, coupon_db_id: UUID, coupon_in: StripeCouponUpdate) -> Optional[StripeCoupon]:
    """DB上のStripeCouponレコードを更新 (主に is_active, metadata)"""
    db_coupon = await get_db_coupon(db, coupon_db_id)
    if not db_coupon:
        return None

    update_data = coupon_in.model_dump(exclude_unset=True)
    # metadata は metadata_ にマッピング
    if 'metadata' in update_data:
        db_coupon.metadata_ = update_data.pop('metadata')

    for key, value in update_data.items():
        setattr(db_coupon, key, value)

    try:
        await db.commit()
        await db.refresh(db_coupon)
        return db_coupon
    except Exception as e:
        await db.rollback()
        logger.error(f"DB Coupon 更新エラー (ID: {coupon_db_id}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="DB Couponの更新に失敗しました。")

# (DB Coupon の削除関数は、関連する Promotion Code がある場合などを考慮して慎重に設計する必要あり)


# --- CampaignCode CRUD 操作 (修正) ---

async def create_campaign_code(db: AsyncSession, campaign_code: CampaignCodeCreate, creator: User) -> CampaignCode:
    # --- ★ 紐付ける Coupon をDBから取得 ---
    db_coupon = await get_db_coupon(db, campaign_code.coupon_id)
    if not db_coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coupon with DB ID '{campaign_code.coupon_id}' not found."
        )
    if not db_coupon.is_active:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Coupon '{db_coupon.name or db_coupon.stripe_coupon_id}' is not active."
        )
    # --- ★ ここまで追加 ---

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

async def get_all_campaign_codes(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[CampaignCode]:
    # --- ★ Coupon 情報も一緒にロード ---
    result = await db.execute(
        select(CampaignCode)
        .options(selectinload(CampaignCode.coupon)) # Couponリレーションをロード
        .order_by(CampaignCode.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().unique().all() # unique() を追加推奨

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
    if not db_coupon.is_active:
        return {
            "valid": False, "message": "関連するクーポンが無効です。",
            "campaign_code_id": campaign_code.id, "coupon_id": campaign_code.coupon_id,
            "stripe_coupon_id": db_coupon.stripe_coupon_id,
            "discount_type": None, "discount_value": None,
            "original_amount": None, "discounted_amount": None
        }

    # --- 4. 割引情報の計算 --- 
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    original_amount: Optional[int] = None
    discounted_amount: Optional[int] = None

    try:
        # Stripeから価格情報を取得 (割引計算のために必要)
        price_data = StripeService.get_price(price_id)
        original_amount = price_data.get("unit_amount")
        if original_amount is None:
            raise ValueError("価格情報から元の金額を取得できませんでした")

        # DB Coupon 情報から割引を計算
        if db_coupon.percent_off:
            discount_type = "percentage"
            discount_value = db_coupon.percent_off
            discount = int(original_amount * (discount_value / 100))
            discounted_amount = max(0, original_amount - discount)
        elif db_coupon.amount_off:
            discount_type = "fixed"
            # amount_off はセント/基本通貨単位なのでそのまま使う (JPYの場合)
            discount_value = db_coupon.amount_off
            discounted_amount = max(0, original_amount - discount_value)
        else:
            # 割引情報がない場合 (エラーとするか、割引なしとして扱うか)
            logger.warning(f"Coupon {db_coupon.id} に割引情報 (percent_off/amount_off) がありません。")
            # ここでは割引なしとして扱う
            discounted_amount = original_amount

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

# --- DiscountType CRUD 操作 (現状維持または削除検討) ---
async def get_discount_type(db: AsyncSession, discount_type_id: UUID) -> Optional[DiscountType]:
    result = await db.execute(
        select(DiscountType).filter(DiscountType.id == discount_type_id)
    )
    return result.scalars().first()

async def get_discount_type_by_name(db: AsyncSession, name: str) -> Optional[DiscountType]:
    result = await db.execute(
        select(DiscountType).filter(DiscountType.name == name)
    )
    return result.scalars().first()

async def get_all_discount_types(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[DiscountType]:
    result = await db.execute(
        select(DiscountType).offset(skip).limit(limit)
    )
    return result.scalars().all()

async def create_discount_type(db: AsyncSession, discount_type: DiscountTypeCreate) -> DiscountType:
    existing = await get_discount_type_by_name(db, discount_type.name)
    if existing:
        raise HTTPException(status_code=400, detail=f"Discount type with name '{discount_type.name}' already exists.")
    db_discount_type = DiscountType(**discount_type.model_dump())
    db.add(db_discount_type)
    await db.commit()
    await db.refresh(db_discount_type)
    return db_discount_type

async def update_discount_type(db: AsyncSession, discount_type_id: UUID, discount_type_data: DiscountTypeUpdate) -> Optional[DiscountType]:
    discount_type = await get_discount_type(db, discount_type_id)
    if not discount_type:
        return None
    update_data = discount_type_data.model_dump(exclude_unset=True)
    if "name" in update_data:
        existing = await get_discount_type_by_name(db, update_data["name"])
        if existing and existing.id != discount_type_id:
            raise HTTPException(status_code=400, detail=f"Discount type with name '{update_data['name']}' already exists.")
    for key, value in update_data.items():
        setattr(discount_type, key, value)
    await db.commit()
    await db.refresh(discount_type)
    return discount_type

async def delete_discount_type(db: AsyncSession, discount_type_id: UUID) -> bool:
    discount_type = await get_discount_type(db, discount_type_id)
    if not discount_type:
        return False
    db.delete(discount_type)
    await db.commit()
    return True

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