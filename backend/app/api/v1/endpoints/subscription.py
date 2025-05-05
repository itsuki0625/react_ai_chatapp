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
from app.models.user import User as UserModel # UserModel をインポート
from app.models.subscription import Subscription as SubscriptionModel, CampaignCode # CampaignCode もインポート

# --- スキーマのインポート (修正) ---
from app.schemas.subscription import (
    SubscriptionResponse,
    PaymentHistoryResponse,
    CampaignCodeResponse, # ★ ユーザー向けに返す可能性もあるため維持
    VerifyCampaignCodeRequest, # ★ 修正後のスキーマ
    VerifyCampaignCodeResponse, # ★ 修正後のスキーマ
    CreateCheckoutRequest, # ★ 修正後のスキーマ
    CheckoutSessionResponse,
    ManageSubscriptionRequest,
    SubscriptionPlanResponse # ★ Stripeプラン用スキーマ
)
# --- ここまで ---

logger = logging.getLogger(__name__)

router = APIRouter(tags=["subscriptions"])

# Stripe APIキーの設定 (StripeService内で設定されるため不要な場合が多い)
# stripe.api_key = settings.STRIPE_SECRET_KEY


@router.get("/stripe-plans", response_model=List[SubscriptionPlanResponse])
async def get_stripe_plans(
    # 認証は不要なので current_user は削除
    db: AsyncSession = Depends(get_async_db) # DBセッションはロギング等で使う可能性を考慮して残すか検討
):
    """
    利用可能なサブスクリプションプラン（Stripe Price）を取得します。
    （注意: このエンドポイントはDBではなくStripeから直接データを取得します）
    """
    try:
        # StripeService を使用して価格リストを取得
        # SubscriptionPlanResponse は from_attributes=False なのでDBモデル不要
        stripe_prices = StripeService.list_prices(active=True, limit=100) # 有効な価格のみ

        # Stripeの価格データを SubscriptionPlanResponse に変換
        plans = []
        for price in stripe_prices:
            # 必要な情報が price['product'] に展開されているか確認
            product_info = price.get('product', {})
            if not isinstance(product_info, dict): # ID文字列の場合、別途商品情報を取得する必要がある
                try:
                    product_info = StripeService.get_product(str(product_info)) if product_info else {}
                except Exception:
                    logger.warning(f"Failed to retrieve product info for price {price.id}. Skipping plan.")
                    product_info = {} # エラーでも処理を続ける

            # 価格データからスキーマを作成
            plan_data = {
                "id": price.id, # 価格IDをプランIDとして使用
                "name": product_info.get('name', 'プラン名不明'), # 商品名を使用
                "description": product_info.get('description'),
                "price_id": price.id,
                "amount": price.unit_amount,
                "currency": price.currency,
                "interval": price.recurring.get('interval') if price.recurring else 'unknown',
                "is_active": price.active,
                # created_at, updated_at は Stripe の created タイムスタンプを使うか、固定値にする
                "created_at": datetime.fromtimestamp(price.created),
                "updated_at": datetime.fromtimestamp(price.created) # Stripe Price に updated はない
            }
            plans.append(SubscriptionPlanResponse(**plan_data))

        return plans
    except Exception as e:
        logger.error(f"Stripeプラン取得エラー: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="プラン情報の取得に失敗しました。")


@router.get("/user-subscription", response_model=Optional[SubscriptionResponse])
async def get_user_subscription(
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    現在のユーザーのアクティブなサブスクリプションを取得します。
    """
    subscription = await crud_subscription.get_active_user_subscription(db, user_id=current_user.id)
    return subscription # 返り値は SubscriptionResponse | None


@router.get("/payment-history", response_model=List[PaymentHistoryResponse])
async def get_payment_history(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    現在のユーザーの支払い履歴を取得します。
    """
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
    キャンペーンコードの有効性を検証します。
    """
    try:
        # ★ 修正: 修正された CRUD 関数を呼び出す
        verification_result = await crud_subscription.verify_campaign_code(
            db=db,
            code=request_data.code,
            price_id=request_data.price_id # price_id も渡す (将来的な利用のため)
        )
        # ★ 修正: CRUD関数の返り値を VerifyCampaignCodeResponse に変換
        # crud 関数の返り値 Dict をそのまま利用できるか、スキーマでラップするか検討
        # crud 関数の返り値のキー名とスキーマのフィールド名が一致していればそのまま返せる
        return VerifyCampaignCodeResponse(**verification_result)
    except HTTPException as e:
        raise e # CRUD関数内で発生したHTTPExceptionはそのまま返す
    except Exception as e:
        logger.error(f"キャンペーンコード検証エラー (Code: {request_data.code}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="キャンペーンコードの検証中にエラーが発生しました。")


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
            # ★ 注意: DBに stripe_customer_id を保存する処理が必要
            # webhook で customer.created をハンドルするか、ここで Subscription を更新する
            # ここでは webhook に任せる想定で進める (あるいは既存Subscriptionがあれば更新)
            logger.info(f"新規Stripe Customer作成: {stripe_customer_id} for User: {current_user.id}")

        # メタデータ設定
        metadata = {
                'user_id': str(current_user.id),
            'price_id': request_data.price_id,
            'plan_id': request_data.plan_id or request_data.price_id # plan_id がなければ price_id を使う
        }

        # --- ★ 割引情報の処理 (修正) ---
        discounts = []
        if request_data.coupon_id: # ★ coupon_id (Stripe Coupon ID) が渡された場合
            # ここで coupon_id が有効か Stripe に問い合わせることも可能だが、
            # Checkout Session 作成時に Stripe 側で検証されるため、必須ではない。
            # DB に保存されている Coupon かどうかのチェックは行っても良いかもしれない。
            # db_coupon = await crud_subscription.get_db_coupon_by_stripe_id(db, request_data.coupon_id)
            # if not db_coupon or not db_coupon.is_active:
            #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="指定されたクーポンは無効です。")
            discounts.append({'coupon': request_data.coupon_id})
            metadata['applied_coupon_id'] = request_data.coupon_id # メタデータにも記録

        # --- ★ ここまで ---

        session_response = StripeService.create_checkout_session(
            customer_id=stripe_customer_id,
            price_id=request_data.price_id,
            success_url=request_data.success_url,
            cancel_url=request_data.cancel_url,
            metadata=metadata,
            discounts=discounts # ★ 修正: 作成した discounts を渡す
        )

        return session_response # CheckoutSessionResponse を返す

    except HTTPException as e:
        raise e # StripeService等で発生したHTTPExceptionはそのまま返す
    except Exception as e:
        logger.error(f"チェックアウトセッション作成エラー (User: {current_user.id}, Price: {request_data.price_id}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="チェックアウトセッションの作成に失敗しました。")


@router.post("/create-portal-session")
async def create_portal_session(
    request_data: Dict[str, str], # return_url を含む想定
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
    サブスクリプションの管理（キャンセル、再開、プラン変更）を行います。
    """
    try:
        action = request_data.action
        subscription_id = request_data.subscription_id # キャンセル、再開には必要
        new_price_id = request_data.plan_id # プラン変更（更新）時に使用

        # DBから現在のアクティブなサブスクリプションを取得 (Stripe Sub IDを取得するため)
        current_db_sub = await crud_subscription.get_active_user_subscription(db, user_id=current_user.id)
        if not current_db_sub or not current_db_sub.stripe_subscription_id:
             # アクションによってはサブスクリプションIDがリクエストに含まれる場合もある
             if not subscription_id:
                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="アクティブなサブスクリプションが見つかりません。")
             stripe_sub_id_to_manage = subscription_id
        else:
             stripe_sub_id_to_manage = current_db_sub.stripe_subscription_id

        result = None
        if action == "cancel":
            result = StripeService.cancel_subscription(stripe_sub_id_to_manage, cancel_at_period_end=True)
            # DB更新はWebhook (customer.subscription.updated) に任せるのが一般的
        elif action == "reactivate":
            result = StripeService.reactivate_subscription(stripe_sub_id_to_manage)
            # DB更新はWebhook (customer.subscription.updated) に任せる
        elif action == "update":
            if not new_price_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="新しいプランID (price_id) が必要です。")
            result = StripeService.update_subscription(stripe_sub_id_to_manage, new_price_id)
            # DB更新はWebhook (customer.subscription.updated) に任せる
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無効なアクションです。")

        return {"status": "success", "result": result}

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"サブスクリプション管理エラー (User: {current_user.id}, Action: {request_data.action}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="サブスクリプションの管理に失敗しました。")


# --- ★ ユーザー向けキャンペーンコード取得 (必要であれば) ---
@router.get("/campaign-codes", response_model=List[CampaignCodeResponse])
async def get_my_campaign_codes(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    現在のユーザーが作成したキャンペーンコード一覧を取得します。
    （アフィリエイト機能などで利用する場合）
    """
    # ★ crud_subscription.get_user_campaign_codes を使用
    codes = await crud_subscription.get_user_campaign_codes(db, owner_id=current_user.id, skip=skip, limit=limit)
    return codes


# --- Webhook エンドポイント (修正) ---
@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: AsyncSession = Depends(get_async_db)
):
    """
    StripeからのWebhookイベントを処理します。
    """
    payload = await request.body()
    try:
        event = StripeService.verify_webhook_signature(payload.decode('utf-8'), stripe_signature)
    except ValueError as e:
        # Invalid payload
        logger.error(f"Webhook ペイロードエラー: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Webhook 署名検証エラー: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Webhook 処理エラー（署名検証中）: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Webhook processing error")

    # イベントタイプに基づいて処理
    event_type = event['type']
    data = event['data']['object']

    logger.info(f"Webhook受信: Type={event_type}, EventID={event['id']}")

    try:
        if event_type == 'checkout.session.completed':
            session = data
            logger.info(f"Checkout Session Completed: {session.id}")
            metadata = session.get('metadata', {})
            user_id_str = metadata.get('user_id')
            price_id = metadata.get('price_id') # Stripe Price ID
            plan_id_metadata = metadata.get('plan_id') # 念のため
            stripe_subscription_id = session.get('subscription')
            stripe_customer_id = session.get('customer')
            # --- ★ 割引情報の取得 ---
            applied_coupon_id = metadata.get('applied_coupon_id') # メタデータからStripe Coupon ID取得
            db_campaign_code: Optional[CampaignCode] = None
            if applied_coupon_id:
                # Stripe Coupon ID から DBの CampaignCode を検索する必要がある
                db_coupon = await crud_subscription.get_db_coupon_by_stripe_id(db, applied_coupon_id)
                if db_coupon and db_coupon.campaign_codes:
                    # 簡易的に最初のCampaignCodeを使う（より厳密な紐付けが必要な場合あり）
                    db_campaign_code = db_coupon.campaign_codes[0]
                    logger.info(f"Checkoutに適用されたDB Campaign Code ID: {db_campaign_code.id} (via Stripe Coupon: {applied_coupon_id})")
                else:
                    logger.warning(f"メタデータのStripe Coupon ID {applied_coupon_id} に対応するDB CampaignCodeが見つかりません。")
            # --- ★ ここまで ---

            if not user_id_str:
                logger.error("Webhook checkout.session.completed: metadataにuser_idがありません")
                return {"status": "error", "message": "user_id not found in metadata"}

            try:
                user_id = UUID(user_id_str)
            except ValueError:
                 logger.error(f"Webhook checkout.session.completed: 無効なuser_id形式です: {user_id_str}")
                 return {"status": "error", "message": "Invalid user_id format"}


            # サブスクリプション情報をDBに保存または更新
            # 既存のサブスクリプションがあるか確認 (Stripe Sub ID で)
            existing_sub = await crud_subscription.get_subscription_by_stripe_id(db, stripe_subscription_id)

            if existing_sub:
                 # 既存サブスクリプションを更新 (再アクティブ化など)
                 logger.info(f"既存サブスクリプション更新 (Stripe ID: {stripe_subscription_id})")
                 # Stripeから最新のサブスクリプション情報を取得
                 stripe_sub_data = StripeService.get_subscription(stripe_subscription_id)
                 update_data = {
                     "status": stripe_sub_data.get('status'),
                     "current_period_start": datetime.fromtimestamp(stripe_sub_data.get('current_period_start')),
                     "current_period_end": datetime.fromtimestamp(stripe_sub_data.get('current_period_end')),
                     "cancel_at": datetime.fromtimestamp(stripe_sub_data.get('cancel_at')) if stripe_sub_data.get('cancel_at') else None,
                     "canceled_at": datetime.fromtimestamp(stripe_sub_data.get('canceled_at')) if stripe_sub_data.get('canceled_at') else None,
                     "is_active": stripe_sub_data.get('status') in ['active', 'trialing'],
                     # ★ キャンペーンコードIDも更新（Checkoutで適用されたもの）
                     "campaign_code_id": db_campaign_code.id if db_campaign_code else existing_sub.campaign_code_id,
                     "stripe_customer_id": stripe_customer_id # 念のため顧客IDも更新
                 }
                 await crud_subscription.update_subscription(db, existing_sub.id, update_data)

            else:
                # 新規サブスクリプションを作成
                logger.info(f"新規サブスクリプション作成 (Stripe ID: {stripe_subscription_id})")
                # Stripeからサブスクリプション情報を取得してDBに保存
                stripe_sub_data = StripeService.get_subscription(stripe_subscription_id)
                new_sub_data = {
                    "user_id": user_id,
                    "plan_name": stripe_sub_data.get('items', {}).get('data', [{}])[0].get('plan', {}).get('nickname', 'プラン名不明'), # Plan名を取得
                    "price_id": price_id, # メタデータから
                    "stripe_subscription_id": stripe_subscription_id,
                    "stripe_customer_id": stripe_customer_id,
                    "status": stripe_sub_data.get('status'),
                    "current_period_start": datetime.fromtimestamp(stripe_sub_data.get('current_period_start')),
                    "current_period_end": datetime.fromtimestamp(stripe_sub_data.get('current_period_end')),
                    "is_active": stripe_sub_data.get('status') in ['active', 'trialing'],
                    # ★ キャンペーンコードIDを設定
                    "campaign_code_id": db_campaign_code.id if db_campaign_code else None,
                    # plan_id (DBのFK) を設定 - price_id からプランを検索する必要がある
                    # ここでは簡易的に plan_name を保存しているが、FK制約がある場合は注意
                    # plan = await crud_subscription.get_plan_by_price_id(db, price_id) # このような関数が必要
                    # if plan: new_sub_data["plan_id"] = plan.id
                }
                await crud_subscription.create_subscription(db, crud_subscription.SubscriptionCreate(**new_sub_data))

            # --- ★ キャンペーンコード使用回数をインクリメント ---
            if db_campaign_code:
                await crud_subscription.increment_campaign_code_usage(db, db_campaign_code.id)
                # TODO: CampaignCodeRedemption レコードを作成する
            # --- ★ ここまで ---

            # ユーザーのステータスを更新 (例: 'active' に)
            user = await crud_user.get_user(db, user_id)
            if user and user.status != 'active':
                 await crud_user.update_user(db, db_user=user, user_in=crud_user.UserUpdate(status='active'))


        elif event_type == 'invoice.payment_succeeded':
            invoice = data
            logger.info(f"Invoice Payment Succeeded: {invoice.id}")
            stripe_subscription_id = invoice.get('subscription')
            stripe_customer_id = invoice.get('customer')
            stripe_payment_intent_id = invoice.get('payment_intent')

            if stripe_subscription_id:
                # 既存のサブスクリプション情報を更新
                db_subscription = await crud_subscription.get_subscription_by_stripe_id(db, stripe_subscription_id)
                if db_subscription:
                    # Stripeから最新のサブスクリプション情報を取得して更新
                    stripe_sub_data = StripeService.get_subscription(stripe_subscription_id)
                    update_data = {
                        "status": stripe_sub_data.get('status'),
                        "current_period_start": datetime.fromtimestamp(stripe_sub_data.get('current_period_start')),
                        "current_period_end": datetime.fromtimestamp(stripe_sub_data.get('current_period_end')),
                        "cancel_at": datetime.fromtimestamp(stripe_sub_data.get('cancel_at')) if stripe_sub_data.get('cancel_at') else None,
                        "canceled_at": datetime.fromtimestamp(stripe_sub_data.get('canceled_at')) if stripe_sub_data.get('canceled_at') else None,
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
                        "payment_date": datetime.fromtimestamp(invoice.status_transitions.paid_at),
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
            subscription = data
            logger.info(f"Customer Subscription Updated: {subscription.id}, Status: {subscription.status}")
            # DBのサブスクリプション情報を更新
            db_subscription = await crud_subscription.get_subscription_by_stripe_id(db, subscription.id)
            if db_subscription:
                update_data = {
                    "status": subscription.status,
                    "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
                    "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                    "cancel_at": datetime.fromtimestamp(subscription.cancel_at) if subscription.cancel_at else None,
                    "canceled_at": datetime.fromtimestamp(subscription.canceled_at) if subscription.canceled_at else None,
                    "is_active": subscription.status in ['active', 'trialing'],
                    # プラン変更があった場合、plan_name, price_id も更新が必要
                    # "plan_name": ...,
                    # "price_id": ...,
                }
                await crud_subscription.update_subscription(db, db_subscription.id, update_data)
            else:
                 logger.warning(f"Webhook customer.subscription.updated: Stripe Sub ID {subscription.id} に対応するDBレコードが見つかりません。")

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
