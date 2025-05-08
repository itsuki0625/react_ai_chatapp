# backend/app/api/v1/endpoints/subscription.py

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
import stripe
import logging
from uuid import UUID
from datetime import datetime # datetime をインポート

from app.core.config import settings
from app.api.deps import get_async_db, get_current_user
from app.services.stripe_service import StripeService
from app.crud import subscription as crud_subscription
from app.crud import user as crud_user # ユーザー情報取得用にインポート
from app.crud import crud_role # crud_role をインポート
from app.models.user import User as UserModel, Role # CampaignCode もインポート
from app.models.subscription import CampaignCode, SubscriptionPlan as SubscriptionPlanModel # SubscriptionModelは不要になったので削除

# --- スキーマのインポート (修正) ---
from app.schemas.subscription import (
    SubscriptionResponse,
    PaymentHistoryResponse,
    CampaignCodeResponse,
    VerifyCampaignCodeRequest,
    VerifyCampaignCodeResponse,
    CreateCheckoutRequest,
    CheckoutSessionResponse,
    ManageSubscriptionRequest,
    SubscriptionPlanResponse
)
from app.schemas.user import UserUpdate, UserStatus as SchemaUserStatus # UserUpdate と UserStatus をインポート
# --- ここまで ---

logger = logging.getLogger(__name__)

router = APIRouter(tags=["subscriptions"])


@router.get("/stripe-plans", response_model=List[SubscriptionPlanResponse])
async def get_stripe_plans(
    db: AsyncSession = Depends(get_async_db),
    skip: int = 0, # ページネーション用に skip と limit を追加
    limit: int = 100
):
    """
    データベースからアクティブな料金プラン (SubscriptionPlan) のリストを取得します。
    """
    try:
        # DBからアクティブなSubscriptionPlanのリストを取得
        # crud_subscription.get_active_subscription_plans は SubscriptionPlanModel のリストを返す
        db_plans: List[SubscriptionPlanModel] = await crud_subscription.get_active_subscription_plans(db, skip=skip, limit=limit)

        response_plans: List[SubscriptionPlanResponse] = []
        for db_plan_model in db_plans:
            # SubscriptionPlanResponse に必要なデータをマッピング
            # SubscriptionPlanResponse の from_attributes = True を活用するため、
            # 基本的にはそのまま渡せるが、不足するフィールドや変換が必要なフィールドがあればここで対応
            
            # stripe_db_product がロードされていることを確認 (get_active_subscription_plansでロード済みのはず)
            if not db_plan_model.stripe_db_product:
                 logger.warning(f"SubscriptionPlan (ID: {db_plan_model.id}, Name: {db_plan_model.name}) is missing related StripeDbProduct. Skipping.")
                 continue
            
            # SubscriptionPlanResponseが期待するフィールドをモデルから直接取得して渡す
            # (from_attributesが正しく機能すれば、多くは自動でマッピングされる)
            plan_data_for_response = {
                "id": db_plan_model.id,
                "name": db_plan_model.name,
                "description": db_plan_model.description,
                "price_id": db_plan_model.price_id,
                "stripe_db_product_id": db_plan_model.stripe_db_product_id, # これは UUID
                "amount": db_plan_model.amount,
                "currency": db_plan_model.currency,
                "interval": db_plan_model.interval,
                "interval_count": db_plan_model.interval_count,
                "is_active": db_plan_model.is_active,
                "features": db_plan_model.features, # JSONフィールド
                "plan_metadata": db_plan_model.plan_metadata, # JSONフィールド
                "trial_days": db_plan_model.trial_days,
                "created_at": db_plan_model.created_at,
                "updated_at": db_plan_model.updated_at,
                # SubscriptionPlanResponse に追加のフィールドがあればここでマッピング
            }
            try:
                # model_validate を使用して辞書からPydanticモデルインスタンスを作成
                validated_plan_response = SubscriptionPlanResponse.model_validate(plan_data_for_response)
                response_plans.append(validated_plan_response)
            except Exception as e_validate:
                logger.error(f"Pydantic validation error for SubscriptionPlan ID {db_plan_model.id} during response model creation: {e_validate}", exc_info=True)
                # バリデーションエラーが発生したプランはスキップ

        return response_plans

    except Exception as e:
        logger.error(f"DBからの料金プラン取得エラー: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="料金プランの取得に失敗しました。")

@router.get("/user-subscription", response_model=Optional[SubscriptionResponse])
async def get_user_subscription(
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user)
):
    """ユーザーの現在アクティブなサブスクリプションを取得します。"""
    subscription = await crud_subscription.get_active_user_subscription(db, user_id=current_user.id)
    if not subscription:
        return None
    
    plan_name_for_logging = "プラン情報なし" # Logging/debugging purpose, not for response schema
    price_id_to_return = None 
    plan_id_to_return = None

    if subscription.plan: 
        plan_name_for_logging = subscription.plan.name
        price_id_to_return = subscription.plan.price_id
        plan_id_to_return = subscription.plan.id
    elif hasattr(subscription, 'plan_id') and subscription.plan_id:
        plan_id_to_return = subscription.plan_id
        logger.warning(f"Subscription ID {subscription.id} には plan オブジェクトがロードされていませんでしたが、plan_id ({subscription.plan_id}) は存在しました。plan_name '{plan_name_for_logging}' と price_id は不完全な可能性があります。")
    
    if plan_id_to_return is None:
        logger.error(f"Subscription ID {subscription.id} から有効な plan_id を特定できませんでした。Subscription.plan_id: {getattr(subscription, 'plan_id', 'N/A')}, Subscription.plan: {'Exists' if subscription.plan else 'None'}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="サブスクリプションに関連するプラン情報が見つかりませんでした。データ不整合の可能性があります。"
        )

    response_data = {
        "id": subscription.id,
        "user_id": subscription.user_id,
        "plan_id": plan_id_to_return, # 必須フィールド
        "plan_name": plan_name_for_logging, # スキーマに追加したので含める
        "stripe_customer_id": subscription.stripe_customer_id,
        "stripe_subscription_id": subscription.stripe_subscription_id,
        "status": subscription.status,
        "price_id": price_id_to_return,
        "current_period_start": subscription.current_period_start,
        "current_period_end": subscription.current_period_end,
        "cancel_at": subscription.cancel_at,
        "canceled_at": subscription.canceled_at,
        "is_active": subscription.is_active,
        "created_at": subscription.created_at,
        "updated_at": subscription.updated_at
    }
    
    logger.debug(f"Data prepared for SubscriptionResponse.model_validate: {response_data}")

    try:
        # datetimeフィールドはisoformat()せずに直接渡す（Pydanticが処理する）
        # UUIDフィールドもstr()せずに直接渡す
        return SubscriptionResponse.model_validate(response_data)
    except Exception as e_pydantic:
        logger.error(f"Pydantic validation failed for SubscriptionResponse. Data: {response_data}. Error: {e_pydantic}", exc_info=True)
        # Pydanticのバリデーションエラーの詳細をクライアントに返すことも検討できるが、基本は500エラー
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="サブスクリプションレスポンスの作成に失敗しました。")

@router.get("/payment-history", response_model=List[PaymentHistoryResponse])
async def get_payment_history(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user)
):
    """ユーザーの支払い履歴を取得します。"""
    history = await crud_subscription.get_user_payment_history(db, user_id=current_user.id, skip=skip, limit=limit)
    return history

@router.post("/verify-campaign-code", response_model=VerifyCampaignCodeResponse)
async def verify_campaign_code(
    request_data: VerifyCampaignCodeRequest, # ★ 修正: スキーマを使用
    db: AsyncSession = Depends(get_async_db),
    # 認証は必須ではないかもしれないが、ユーザー情報をログ等で使う可能性を考慮
    current_user: Optional[UserModel] = Depends(get_current_user) # Optional に
):
    """
    キャンペーンコードを検証します。
    """
    db_code = await crud_subscription.get_campaign_code_by_code(db, request_data.code)
    if not db_code or not db_code.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無効なキャンペーンコードです。")

    if db_code.valid_until and db_code.valid_until < datetime.utcnow().replace(tzinfo=None): # naive datetimeと比較
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="キャンペーンコードの有効期限が切れています。")

    if db_code.max_uses is not None and db_code.used_count >= db_code.max_uses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="キャンペーンコードの利用回数上限に達しています。")
    
    # Stripe Coupon ID があるか確認 (これがないと割引計算が難しい)
    if not db_code.stripe_coupon_id:
        logger.error(f"DB CampaignCode {db_code.code} に stripe_coupon_id が設定されていません。")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="キャンペーンコードの設定に問題があります。")

    try:
        stripe_coupon = StripeService.retrieve_coupon(db_code.stripe_coupon_id) # type: ignore
    except Exception as e:
        logger.error(f"Stripe Coupon ({db_code.stripe_coupon_id}) 取得エラー: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="割引情報の取得に失敗しました。")

    # プランの価格を取得 (リクエストから plan_id または price_id を受け取る想定)
    # ここでは request_data.price_id を使用
    original_amount = 0
    try:
        price_data = StripeService.get_price(request_data.price_id)
        original_amount = price_data.get('unit_amount', 0)
    except Exception:
        # 価格取得に失敗しても、コードの有効性だけは返すこともできる
        logger.warning(f"価格情報 (Price ID: {request_data.price_id}) の取得に失敗。割引額計算はスキップ。")
        # raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="プラン価格の取得に失敗しました。")

    discounted_amount = original_amount
    discount_type = None
    discount_value = 0

    if stripe_coupon.get('percent_off') is not None:
        percent_off = stripe_coupon['percent_off']
        discounted_amount = original_amount * (1 - percent_off / 100)
        discount_type = 'percentage'
        discount_value = percent_off
    elif stripe_coupon.get('amount_off') is not None:
        amount_off = stripe_coupon['amount_off']
        discounted_amount = max(0, original_amount - amount_off)
        discount_type = 'fixed'
        discount_value = amount_off

    return VerifyCampaignCodeResponse(
        valid=True,
        message="キャンペーンコードが適用されました。",
        discount_type=discount_type, # type: ignore
        discount_value=discount_value,
        original_amount=original_amount,
        discounted_amount=int(discounted_amount),
        campaign_code_id=str(db_code.id),
        stripe_coupon_id=db_code.stripe_coupon_id
    )


@router.post("/create-checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request_data: CreateCheckoutRequest, # ★ 修正: スキーマを使用
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Stripeチェックアウトセッションを作成します。
    """
    try:
        # Stripe顧客IDを取得または作成
        stripe_customer_id = await crud_subscription.get_stripe_customer_id(db, current_user.id)
        if not stripe_customer_id:
            stripe_customer_id = StripeService.create_customer(
                    email=current_user.email,
                    name=current_user.full_name,
                    metadata={'user_id': str(current_user.id)}
                )
            logger.info(f"新規Stripe Customer作成: {stripe_customer_id} for User: {current_user.id}")

        metadata = {
                'user_id': str(current_user.id),
            'price_id': request_data.price_id,
            'plan_id': request_data.plan_id or request_data.price_id
        }

        discounts = []
        if request_data.coupon_id:
            discounts.append({'coupon': request_data.coupon_id})
            metadata['applied_coupon_id'] = request_data.coupon_id

        session_response = StripeService.create_checkout_session(
            customer_id=stripe_customer_id,
            price_id=request_data.price_id,
            success_url=request_data.success_url,
            cancel_url=request_data.cancel_url,
            metadata=metadata,
            discounts=discounts
        )

        return session_response

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"チェックアウトセッション作成エラー (User: {current_user.id}, Price: {request_data.price_id}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="チェックアウトセッションの作成に失敗しました。")


@router.post("/create-portal-session")
async def create_portal_session(
    request_data: Dict[str, str],
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Stripeカスタマーポータルセッションを作成します。
    """
    return_url = request_data.get("return_url")
    if not return_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="return_urlが必要です。")

    try:
        stripe_customer_id = await crud_subscription.get_stripe_customer_id(db, current_user.id)
        if not stripe_customer_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stripe顧客情報が見つかりません。")

        portal_url = StripeService.create_portal_session(stripe_customer_id, return_url)
        return {"url": portal_url}

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"ポータルセッション作成エラー (User: {current_user.id}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="ポータルセッションの作成に失敗しました。")


@router.post("/manage-subscription")
async def manage_subscription(
    request_data: ManageSubscriptionRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    サブスクリプションを管理します (キャンセル、再開、プラン変更など)。
    """
    action = request_data.action
    subscription_id = request_data.subscription_id # これはStripe Subscription IDを期待
    new_plan_price_id = request_data.plan_id # Stripe Price ID

    if not subscription_id and action != 'update':
        active_sub = await crud_subscription.get_active_user_subscription(db, current_user.id)
        if not active_sub or not active_sub.stripe_subscription_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="操作対象のサブスクリプションが見つかりません。")
        subscription_id = active_sub.stripe_subscription_id
    
    if not subscription_id: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="StripeサブスクリプションIDが必要です。")

    try:
        if action == "cancel":
            stripe_sub_obj = StripeService.cancel_subscription(subscription_id, cancel_at_period_end=True)
            db_sub = await crud_subscription.get_subscription_by_stripe_id(db, subscription_id)
            if db_sub:
                update_data = {
                    "status": stripe_sub_obj.status,
                    "cancel_at": datetime.fromtimestamp(stripe_sub_obj.cancel_at) if stripe_sub_obj.cancel_at else None,
                    "canceled_at": datetime.fromtimestamp(stripe_sub_obj.canceled_at) if stripe_sub_obj.canceled_at else None,
                    "is_active": stripe_sub_obj.status in ['active', 'trialing']
                }
                await crud_subscription.update_subscription(db, db_sub.id, update_data)
            return {"message": "サブスクリプションは期間終了時に解約されます。", "subscription": stripe_sub_obj}
        
        elif action == "reactivate":
            stripe_sub_obj = StripeService.reactivate_subscription(subscription_id)
            db_sub = await crud_subscription.get_subscription_by_stripe_id(db, subscription_id)
            if db_sub:
                update_data = {
                    "status": stripe_sub_obj.status,
                    "current_period_start": datetime.fromtimestamp(stripe_sub_obj.current_period_start) if stripe_sub_obj.current_period_start else None,
                    "current_period_end": datetime.fromtimestamp(stripe_sub_obj.current_period_end) if stripe_sub_obj.current_period_end else None,
                    "cancel_at": None, 
                    "canceled_at": None,
                    "is_active": stripe_sub_obj.status in ['active', 'trialing']
                }
                await crud_subscription.update_subscription(db, db_sub.id, update_data)
            return {"message": "サブスクリプションが再開されました。", "subscription": stripe_sub_obj}
        
        elif action == "update":
            if not new_plan_price_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="新しいプランのPrice IDが必要です。")
            
            stripe_sub_obj = StripeService.update_subscription(subscription_id, new_plan_price_id)
            
            db_sub = await crud_subscription.get_subscription_by_stripe_id(db, subscription_id)
            db_plan = await crud_subscription.get_plan_by_price_id(db, new_plan_price_id)

            if not db_plan:
                logger.error(f"プラン変更エラー: 指定されたStripe Price ID '{new_plan_price_id}' に対応するDBプランが見つかりません。")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="指定された新しいプランが見つかりません。")

            if db_sub:
                update_data = {
                    "status": stripe_sub_obj.status,
                    "plan_id": db_plan.id, 
                    "current_period_start": datetime.fromtimestamp(stripe_sub_obj.current_period_start) if stripe_sub_obj.current_period_start else None,
                    "current_period_end": datetime.fromtimestamp(stripe_sub_obj.current_period_end) if stripe_sub_obj.current_period_end else None,
                    "is_active": stripe_sub_obj.status in ['active', 'trialing']
                }
                await crud_subscription.update_subscription(db, db_sub.id, update_data)
            return {"message": "サブスクリプションプランが変更されました。", "subscription": stripe_sub_obj}
        
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無効なアクションです。")

    except stripe.error.StripeError as e:
        logger.error(f"Stripe APIエラー (Action: {action}, SubID: {subscription_id}): {e}")
        raise HTTPException(status_code=e.http_status or status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e.user_message) if e.user_message else "Stripe APIエラー") # Ensure user_message is str
    except Exception as e:
        logger.error(f"サブスクリプション管理エラー (Action: {action}, SubID: {subscription_id}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="サブスクリプションの管理に失敗しました。")


@router.get("/campaign-codes", response_model=List[CampaignCodeResponse])
async def get_my_campaign_codes(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user)
):
    """管理者が作成した（または特定のユーザーに紐づく）有効なキャンペーンコード一覧を取得"""
    # ここでは簡易的に全ての有効なコードを返す（管理者用を想定）
    # ユーザー個別のコードを扱う場合は、owner_id などでフィルタリングが必要
    codes = await crud_subscription.get_all_active_campaign_codes(db, skip=skip, limit=limit)
    return codes


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: AsyncSession = Depends(get_async_db)
):
    """
    StripeからのWebhookイベントを処理します。
    主にサブスクリプションのステータス変更や支払い完了イベントをハンドルします。
    """
    payload = await request.body()
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = StripeService.verify_webhook_signature(payload.decode(), stripe_signature)
    except ValueError as e:
        logger.error(f"Webhookペイロード解析エラー: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e: # type: ignore
        logger.error(f"Webhook署名検証エラー: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Webhook 処理エラー（署名検証中）: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Webhook processing error")

    event_type = event['type']
    data = event['data']['object']

    logger.info(f"Webhook受信: Type={event_type}, EventID={event['id']}")

    try:
        if event_type == 'checkout.session.completed':
            session = data
            logger.info(f"Checkout Session Completed: {session.id}")
            metadata = session.get('metadata', {})
            user_id_str = metadata.get('user_id')
            price_id = metadata.get('price_id')
            stripe_subscription_id = session.get('subscription')
            stripe_customer_id = session.get('customer')
            applied_coupon_id = metadata.get('applied_coupon_id')
            db_campaign_code: Optional[CampaignCode] = None

            if applied_coupon_id:
                db_coupon = await crud_subscription.get_db_coupon_by_stripe_id(db, applied_coupon_id)
                if db_coupon and db_coupon.campaign_codes:
                    db_campaign_code = db_coupon.campaign_codes[0]
                    logger.info(f"Checkoutに適用されたDB Campaign Code ID: {db_campaign_code.id} (via Stripe Coupon: {applied_coupon_id})")
                else:
                    logger.warning(f"メタデータのStripe Coupon ID {applied_coupon_id} に対応するDB CampaignCodeが見つかりません。")

            if not user_id_str:
                logger.error("Webhook checkout.session.completed: metadataにuser_idがありません")
                return {"status": "error", "message": "user_id not found in metadata"}

            try:
                user_id = UUID(user_id_str)
            except ValueError:
                 logger.error(f"Webhook checkout.session.completed: 無効なuser_id形式です: {user_id_str}")
                 return {"status": "error", "message": "Invalid user_id format"}

            existing_sub = await crud_subscription.get_subscription_by_stripe_id(db, stripe_subscription_id)

            if existing_sub:
                 logger.info(f"既存サブスクリプション更新 (Stripe ID: {stripe_subscription_id})")
                 stripe_sub_data = StripeService.get_subscription(stripe_subscription_id)
                 update_data = {
                     "status": stripe_sub_data.get('status'),
                     "current_period_start": datetime.fromtimestamp(cps) if (cps := stripe_sub_data.get('current_period_start')) is not None else None,
                     "current_period_end": datetime.fromtimestamp(cpe) if (cpe := stripe_sub_data.get('current_period_end')) is not None else None,
                     "cancel_at": datetime.fromtimestamp(ca) if (ca := stripe_sub_data.get('cancel_at')) is not None else None,
                     "canceled_at": datetime.fromtimestamp(cat) if (cat := stripe_sub_data.get('canceled_at')) is not None else None,
                     "is_active": stripe_sub_data.get('status') in ['active', 'trialing'],
                     "campaign_code_id": db_campaign_code.id if db_campaign_code else existing_sub.campaign_code_id,
                     "stripe_customer_id": stripe_customer_id
                 }
                 await crud_subscription.update_subscription(db, existing_sub.id, update_data)
            else:
                logger.info(f"新規サブスクリプション作成 (Stripe ID: {stripe_subscription_id})")
                stripe_sub_data = StripeService.get_subscription(stripe_subscription_id)
                # plan_data = stripe_sub_data.get('items', {}).get('data', [{}])[0].get('plan', {}) # plan_dataの取得は不要になるか確認
                # plan_name = plan_data.get('nickname') if plan_data and plan_data.get('nickname') is not None else 'プラン名不明' # plan_nameも不要

                # ★★★ Stripe Price ID から DBのPlan UUIDを取得 ★★★
                stripe_price_id = stripe_sub_data.get('items', {}).get('data', [{}])[0].get('price', {}).get('id')
                db_plan = None
                if stripe_price_id:
                    db_plan = await crud_subscription.get_plan_by_price_id(db, stripe_price_id)
                else:
                    logger.error("Stripe SubscriptionデータからPrice IDを取得できませんでした。")
                
                if not db_plan:
                     logger.error(f"Stripe Price ID {stripe_price_id} に対応するDBプランが見つかりません。")
                     raise HTTPException(status_code=500, detail="プラン情報の紐付けに失敗しました。")
                # ★★★ ここまで ★★★

                new_sub_data = {
                    "user_id": user_id,
                    "plan_id": db_plan.id, # ★ DBから取得したUUIDを設定
                    "price_id": stripe_price_id, # ★ StripeのPrice IDを設定
                    "stripe_subscription_id": stripe_subscription_id,
                    "stripe_customer_id": stripe_customer_id,
                    "status": stripe_sub_data.get('status'),
                    "current_period_start": datetime.fromtimestamp(cps) if (cps := stripe_sub_data.get('current_period_start')) is not None else None,
                    "current_period_end": datetime.fromtimestamp(cpe) if (cpe := stripe_sub_data.get('current_period_end')) is not None else None,
                    "is_active": stripe_sub_data.get('status') in ['active', 'trialing'],
                    "campaign_code_id": db_campaign_code.id if db_campaign_code else None,
                }
                # SubscriptionCreate スキーマの検証 (plan_id が必須になっているはず)
                await crud_subscription.create_subscription(db, crud_subscription.SubscriptionCreate(**new_sub_data))

            # --- ★ 購入商品に紐づくロールをユーザーに割り当て --- (ここから修正)
            if session.get('line_items'):
                for item in session.get('line_items', {}).get('data', []):
                    price_obj = item.get('price')
                    if price_obj and price_obj.get('product'):
                        stripe_product_id = price_obj.get('product')
                        try:
                            product_data = StripeService.get_product(stripe_product_id)
                            if product_data and product_data.get('metadata'):
                                assigned_role_id_str = product_data.get('metadata', {}).get('assigned_role')
                                if assigned_role_id_str:
                                    logger.info(f"商品 {stripe_product_id} に紐づくロールID(str): {assigned_role_id_str} をユーザー {user_id} に割り当て試行")
                                    try:
                                        assigned_role_id = UUID(assigned_role_id_str)
                                        target_role_obj = await crud_role.get_role(db, role_id=assigned_role_id)

                                        if target_role_obj:
                                            target_role_name = target_role_obj.name
                                            user_to_update = await crud_user.get_user(db, user_id)
                                            if user_to_update:
                                                await crud_user.update_user(db, db_user=user_to_update, user_in=UserUpdate(role=target_role_name))
                                                logger.info(f"ユーザー {user_id} のプライマリロールを '{target_role_name}' (ID: {assigned_role_id}) に更新しました。")
                                            else:
                                                logger.warning(f"ロール割り当て対象のユーザー {user_id} がDBで見つかりません。")
                                        else:
                                            logger.error(f"指定されたロールID {assigned_role_id} に該当するロールがDBで見つかりません。")
                                    except ValueError:
                                        logger.error(f"メタデータの assigned_role '{assigned_role_id_str}' は有効なUUIDではありません。")
                                    except Exception as e_role_assign:
                                        logger.error(f"ロール割り当て処理中に予期せぬエラー: {e_role_assign}", exc_info=True)
                                else:
                                    logger.info(f"商品 {stripe_product_id} のメタデータに assigned_role が設定されていません。")
                        except Exception as e_get_product:
                            logger.error(f"Stripe商品 {stripe_product_id} の情報取得またはロール割り当て処理中にエラー: {e_get_product}", exc_info=True)
                        break # 通常サブスクリプションは商品一つなので、最初のitemで処理を終える
            # --- ★ ロール割り当て処理ここまで ---

            if db_campaign_code:
                await crud_subscription.increment_campaign_code_usage(db, db_campaign_code.id)

            user = await crud_user.get_user(db, user_id)
            if user and user.status != SchemaUserStatus.ACTIVE:
                 await crud_user.update_user(db, db_user=user, user_in=UserUpdate(status=SchemaUserStatus.ACTIVE))

        elif event_type == 'invoice.payment_succeeded':
            invoice = data
            logger.info(f"Invoice Payment Succeeded: {invoice.id}")
            stripe_subscription_id = invoice.get('subscription')
            stripe_payment_intent_id = invoice.get('payment_intent')

            if stripe_subscription_id:
                # 既存のサブスクリプション情報を更新
                db_subscription = await crud_subscription.get_subscription_by_stripe_id(db, stripe_subscription_id)
                if db_subscription:
                    # Stripeから最新のサブスクリプション情報を取得して更新
                    stripe_sub_data = StripeService.get_subscription(stripe_subscription_id)
                    update_data = {
                        "status": stripe_sub_data.get('status'),
                        "current_period_start": datetime.fromtimestamp(cps) if (cps := stripe_sub_data.get('current_period_start')) is not None else None,
                        "current_period_end": datetime.fromtimestamp(cpe) if (cpe := stripe_sub_data.get('current_period_end')) is not None else None,
                        "cancel_at": datetime.fromtimestamp(ca) if (ca := stripe_sub_data.get('cancel_at')) is not None else None,
                        "canceled_at": datetime.fromtimestamp(cat) if (cat := stripe_sub_data.get('canceled_at')) is not None else None,
                        "is_active": stripe_sub_data.get('status') in ['active', 'trialing'],
                    }
                    await crud_subscription.update_subscription(db, db_subscription.id, update_data)
        
        # 支払い履歴を作成
                    payment_data = {
                        "user_id": db_subscription.user_id,
                        "subscription_id": db_subscription.id,
                        "stripe_payment_intent_id": stripe_payment_intent_id,
                        "stripe_invoice_id": invoice.id,
                        "amount": invoice.amount_paid,
                        "currency": invoice.currency,
                        "payment_date": datetime.fromtimestamp(spst) if (spst := invoice.status_transitions.paid_at) is not None else None,
                        "status": "succeeded",
                        "description": f"サブスクリプション支払い ({db_subscription.plan_name})"
                    }
                    await crud_subscription.create_payment_history(db, crud_subscription.PaymentHistoryCreate(**payment_data))
                else:
                     logger.error(f"Webhook invoice.payment_succeeded: Stripe Sub ID {stripe_subscription_id} に対応するDBレコードが見つかりません。")


        elif event_type == 'invoice.payment_failed':
            invoice = data
            logger.warning(f"Invoice Payment Failed: {invoice.id}, Subscription: {invoice.get('subscription')}")
            stripe_subscription_id = invoice.get('subscription')
            if stripe_subscription_id:
                # 支払い失敗に対応する処理（例：サブスクリプションステータスを 'past_due' or 'unpaid' に更新）
                db_subscription = await crud_subscription.get_subscription_by_stripe_id(db, stripe_subscription_id)
                if db_subscription:
                    stripe_sub_data = StripeService.get_subscription(stripe_subscription_id)
                    update_data = {"status": stripe_sub_data.get('status', 'past_due'), "is_active": False} # Stripe側のステータスを反映
                    await crud_subscription.update_subscription(db, db_subscription.id, update_data)
                    # ユーザーへの通知など


        elif event_type == 'customer.subscription.updated':
            stripe_sub_event_data = data # イベントデータ内の subscription オブジェクト
            logger.info(f"Customer Subscription Updated: {stripe_sub_event_data.get('id')}, Status: {stripe_sub_event_data.get('status')}")
            db_subscription = await crud_subscription.get_subscription_by_stripe_id(db, stripe_sub_event_data.get('id'))
            if db_subscription:
                new_stripe_price_id = None
                if stripe_sub_event_data.get('items') and stripe_sub_event_data['items'].get('data'):
                    current_item = stripe_sub_event_data['items']['data'][0]
                    if current_item.get('price'):
                        new_stripe_price_id = current_item['price'].get('id')
                
                new_db_plan_id = db_subscription.plan_id 
                if new_stripe_price_id:
                    db_plan = await crud_subscription.get_plan_by_price_id(db, new_stripe_price_id)
                    if db_plan:
                        new_db_plan_id = db_plan.id
                    else:
                        logger.warning(f"Webhook customer.subscription.updated: 新しいPrice ID {new_stripe_price_id} に対応するDBプランが見つかりません。plan_idは更新されません。")

                update_data = {
                    "status": stripe_sub_event_data.get('status'),
                    "plan_id": new_db_plan_id,
                    "current_period_start": datetime.fromtimestamp(cps) if (cps := stripe_sub_event_data.get('current_period_start')) is not None else None,
                    "current_period_end": datetime.fromtimestamp(cpe) if (cpe := stripe_sub_event_data.get('current_period_end')) is not None else None,
                    "cancel_at": datetime.fromtimestamp(ca) if (ca := stripe_sub_event_data.get('cancel_at')) is not None else None,
                    "canceled_at": datetime.fromtimestamp(cat) if (cat := stripe_sub_event_data.get('canceled_at')) is not None else None,
                    "is_active": stripe_sub_event_data.get('status') in ['active', 'trialing'],
                }
                await crud_subscription.update_subscription(db, db_subscription.id, update_data)
            else:
                 logger.warning(f"Webhook customer.subscription.updated: Stripe Sub ID {stripe_sub_event_data.get('id')} に対応するDBレコードが見つかりません。")

        elif event_type == 'customer.subscription.deleted':
            subscription = data
            logger.info(f"Customer Subscription Deleted: {subscription.id}")
            # DBのサブスクリプションをキャンセル済みに更新
            db_subscription = await crud_subscription.get_subscription_by_stripe_id(db, subscription.id)
            if db_subscription:
                 # cancel_subscription を使うか、直接ステータス更新
                 await crud_subscription.cancel_subscription(db, db_subscription.id, canceled_at=datetime.utcnow())
            else:
                 logger.warning(f"Webhook customer.subscription.deleted: Stripe Sub ID {subscription.id} に対応するDBレコードが見つかりません。")

        # --- ★ customer.created イベントで Stripe Customer ID を DB に保存 --- 
        elif event_type == 'customer.created':
             customer = data
             logger.info(f"Customer Created: {customer.id}, Email: {customer.email}")
             metadata = customer.get('metadata', {})
             user_id_str = metadata.get('user_id')
             if user_id_str:
                 try:
                     user_id = UUID(user_id_str)
                     # ユーザーの既存サブスクリプションを探して更新、なければ何もしない
                     # （Checkout完了時にSubscriptionレコードは作成されるはず）
                     user_subs = await crud_subscription.get_user_subscriptions(db, user_id)
                     updated = False
                     for sub in user_subs:
                         if not sub.stripe_customer_id:
                             await crud_subscription.update_subscription(db, sub.id, {"stripe_customer_id": customer.id})
                             logger.info(f"DB Subscription {sub.id} に Stripe Customer ID {customer.id} を設定しました。")
                             updated = True
                     if not updated:
                         logger.info(f"ユーザー {user_id} に Stripe Customer ID {customer.id} を設定する対象のDB Subscriptionが見つかりませんでした。")
                 except ValueError:
                     logger.error(f"Webhook customer.created: 無効なuser_id形式です: {user_id_str}")
                 except Exception as e:
                      logger.error(f"Webhook customer.created: DB更新中にエラー (User: {user_id_str}): {e}", exc_info=True)
             else:
                 logger.warning("Webhook customer.created: metadataにuser_idがありません。")
        # --- ★ ここまで追加 ---

        else:
            logger.info(f"未処理のWebhookイベントタイプ: {event_type}")

    except HTTPException as e:
         # DB操作などでHTTPExceptionが発生した場合
         logger.error(f"Webhook処理中にHTTPエラー (Type: {event_type}): {e.detail}")
         # Stripeにエラーを返すか検討 (500エラーを返せば再試行される)
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Webhook処理中にエラーが発生しました。")
    except Exception as e:
         # その他の予期せぬエラー
         logger.error(f"Webhook処理中に予期せぬエラー (Type: {event_type}): {e}", exc_info=True)
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Webhook処理中に予期せぬエラーが発生しました。")

    return {"status": "success"}
