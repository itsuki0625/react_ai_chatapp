# backend/app/api/v1/endpoints/subscription.py

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
import stripe
import logging
from uuid import UUID
from datetime import datetime # datetime をインポート

from app.core.config import settings
from app.api.deps import get_async_db, get_current_user, get_current_user_optional
from app.services.stripe_service import StripeService
from app.services.email_service import email_service
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
    SubscriptionPlanResponse,
    PaymentIntentCreateRequest,
    PaymentIntentResponse,
    SubscriptionConfirmRequest
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
    status: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user)
):
    """ユーザーの支払い履歴を取得します（フィルタリング対応）。"""
    history = await crud_subscription.get_user_payment_history(
        db, 
        user_id=current_user.id, 
        skip=skip, 
        limit=limit,
        status=status,
        search=search,
        date_from=date_from,
        date_to=date_to
    )
    return history

@router.post("/verify-campaign-code", response_model=VerifyCampaignCodeResponse)
async def verify_campaign_code(
    request_data: VerifyCampaignCodeRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional) # Optional認証を使用
):
    """
    キャンペーンコードを検証します。
    """
    try:
        # CRUD関数を使用してキャンペーンコードを検証
        verification_result = await crud_subscription.verify_campaign_code(
            db, request_data.code, request_data.price_id
        )
        
        # CRUD関数の結果をPydanticモデルに変換
        response = VerifyCampaignCodeResponse(
            valid=verification_result["valid"],
            message=verification_result["message"],
            discount_type=verification_result["discount_type"],
            discount_value=verification_result["discount_value"],
            original_amount=verification_result["original_amount"],
            discounted_amount=verification_result["discounted_amount"],
            campaign_code_id=str(verification_result["campaign_code_id"]) if verification_result["campaign_code_id"] else None,
            stripe_coupon_id=verification_result["stripe_coupon_id"]
        )
        
        return response
        
    except Exception as e:
        logger.error(f"キャンペーンコード検証エラー (Code: {request_data.code}, Price ID: {request_data.price_id}): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="キャンペーンコードの検証中にエラーが発生しました。"
        )


# PaymentIntent作成エンドポイント（3Dセキュア対応）
@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    request_data: PaymentIntentCreateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    PaymentIntentを作成します。（3Dセキュア対応）
    """
    try:
        # プラン情報を取得
        plan = await crud_subscription.get_plan_by_price_id(db, request_data.price_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="指定されたプランが見つかりません。")

        # Stripe顧客IDを取得または作成
        stripe_customer_id = await crud_subscription.get_stripe_customer_id(db, current_user.id)
        if not stripe_customer_id:
            stripe_customer_id = StripeService.create_customer(
                email=current_user.email,
                name=current_user.full_name,
                metadata={'user_id': str(current_user.id)}
            )
            logger.info(f"新規Stripe Customer作成: {stripe_customer_id} for User: {current_user.id}")

        # PaymentIntentを作成
        metadata = {
            'user_id': str(current_user.id),
            'price_id': request_data.price_id,
            'plan_id': str(plan.id)
        }

        # クーポン情報があれば追加
        if request_data.coupon_id:
            metadata['applied_coupon_id'] = request_data.coupon_id

        payment_intent = stripe.PaymentIntent.create(
            amount=plan.amount,
            currency=plan.currency,
            customer=stripe_customer_id,
            metadata=metadata,
            automatic_payment_methods={'enabled': True},  # 3Dセキュア自動対応
            setup_future_usage='off_session'  # 将来の決済用にセットアップ
        )

        return PaymentIntentResponse(
            client_secret=payment_intent.client_secret,
            amount=payment_intent.amount,
            currency=payment_intent.currency,
            status=payment_intent.status
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"PaymentIntent作成エラー (User: {current_user.id}, Price: {request_data.price_id}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="PaymentIntentの作成に失敗しました。")


# サブスクリプション確定エンドポイント（PaymentIntent成功後）
@router.post("/confirm-subscription")
async def confirm_subscription(
    request_data: SubscriptionConfirmRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    PaymentIntent成功後、サブスクリプションを確定します。
    """
    try:
        # PaymentIntentの状態を確認
        payment_intent = stripe.PaymentIntent.retrieve(request_data.payment_intent_id)
        
        if payment_intent.status != 'succeeded':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"PaymentIntentの状態が無効です: {payment_intent.status}"
            )

        # PaymentIntentのメタデータからプラン情報を取得
        metadata = payment_intent.metadata or {}
        plan_id_from_metadata = metadata.get('plan_id')
        
        if not plan_id_from_metadata:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PaymentIntentにプラン情報が含まれていません"
            )

        # プラン情報を取得
        plan = await crud_subscription.get_plan_by_price_id(db, request_data.price_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="指定されたプランが見つかりません"
            )

        # Stripe顧客IDを取得
        stripe_customer_id = await crud_subscription.get_stripe_customer_id(db, current_user.id)
        if not stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Stripe顧客情報が見つかりません"
            )

        # Stripeでサブスクリプションを作成
        subscription_metadata = {
            'user_id': str(current_user.id),
            'payment_intent_id': request_data.payment_intent_id,
            'plan_id': str(plan.id)
        }

        stripe_subscription = stripe.Subscription.create(
            customer=stripe_customer_id,
            items=[{'price': request_data.price_id}],
            payment_behavior='default_incomplete',
            payment_settings={'payment_method_types': ['card']},
            expand=['latest_invoice.payment_intent'],
            metadata=subscription_metadata
        )

        # DBにサブスクリプションを保存
        subscription_data = {
            "user_id": current_user.id,
            "plan_id": plan.id,
            "price_id": request_data.price_id,
            "stripe_subscription_id": stripe_subscription.id,
            "stripe_customer_id": stripe_customer_id,
            "status": stripe_subscription.status,
            "current_period_start": datetime.fromtimestamp(stripe_subscription.current_period_start),
            "current_period_end": datetime.fromtimestamp(stripe_subscription.current_period_end),
            "is_active": stripe_subscription.status in ['active', 'trialing']
        }

        db_subscription = await crud_subscription.create_subscription(
            db, 
            crud_subscription.SubscriptionCreate(**subscription_data)
        )

        return {
            "message": "サブスクリプションが正常に作成されました",
            "subscription_id": str(db_subscription.id),
            "stripe_subscription_id": stripe_subscription.id,
            "status": stripe_subscription.status
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"サブスクリプション確定エラー (User: {current_user.id}, PaymentIntent: {request_data.payment_intent_id}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="サブスクリプションの確定に失敗しました。")


# 決済状況確認エンドポイント
@router.get("/payment-status/{payment_intent_id}")
async def get_payment_status(
    payment_intent_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    PaymentIntentの状況を確認します。
    """
    try:
        # Stripe APIからPaymentIntentを取得
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        # PaymentIntentのメタデータからユーザー情報を確認
        metadata = payment_intent.metadata or {}
        payment_user_id = metadata.get('user_id')
        
        if payment_user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="この決済情報にアクセスする権限がありません"
            )

        # 決済履歴がDBに記録されているかを確認
        payment_history = await crud_subscription.get_payment_by_stripe_id(db, payment_intent_id)
        
        response_data = {
            "id": payment_intent.id,
            "status": payment_intent.status,
            "amount": payment_intent.amount,
            "currency": payment_intent.currency,
            "created": payment_intent.created,
            "client_secret": payment_intent.client_secret if payment_intent.status != 'succeeded' else None,
            "last_payment_error": None,
            "next_action": None,
            "payment_method": payment_intent.payment_method,
            "db_recorded": payment_history is not None
        }
        
        # エラー情報があれば追加
        if payment_intent.last_payment_error:
            response_data["last_payment_error"] = {
                "type": payment_intent.last_payment_error.type,
                "code": payment_intent.last_payment_error.code,
                "message": payment_intent.last_payment_error.message
            }
        
        # 次のアクションが必要な場合（3Dセキュア等）
        if payment_intent.next_action:
            response_data["next_action"] = {
                "type": payment_intent.next_action.type
            }
            
        return response_data

    except stripe.error.InvalidRequestError as e:
        if "No such payment_intent" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="指定された決済情報が見つかりません"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Stripe APIエラー: {str(e)}"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"決済状況確認エラー (PaymentIntent: {payment_intent_id}, User: {current_user.id}): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="決済状況の確認に失敗しました"
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
            if stripe_subscription_id and 'stripe_sub_data' in locals() and stripe_sub_data:
                try:
                    items = stripe_sub_data.get('items', {}).get('data', [])
                    if items:
                        price_info = items[0].get('price') # 通常、サブスクリプションの最初のアイテムが対象
                        if price_info and price_info.get('product'):
                            stripe_product_id_from_sub = price_info.get('product')
                            logger.info(f"Subscription item's Stripe Product ID: {stripe_product_id_from_sub} を元にロール割り当て試行 (User: {user_id})")
                            product_data = StripeService.get_product(stripe_product_id_from_sub)
                            if product_data and product_data.get('metadata'):
                                assigned_role_id_str = product_data.get('metadata', {}).get('assigned_role')
                                if assigned_role_id_str:
                                    logger.info(f"商品 {stripe_product_id_from_sub} に紐づくロールID(str): {assigned_role_id_str} をユーザー {user_id} に割り当て試行")
                                    try:
                                        assigned_role_id = UUID(assigned_role_id_str)
                                        target_role_obj = await crud_role.get_role(db, role_id=assigned_role_id)

                                        if target_role_obj:
                                            target_role_name = target_role_obj.name
                                            user_to_update = await crud_user.get_user(db, user_id)
                                            if user_to_update:
                                                # ★ デバッグ用: 更新前のロール情報をログ出力
                                                current_primary_role = next((ur for ur in user_to_update.user_roles if ur.is_primary), None)
                                                current_role_name = current_primary_role.role.name if current_primary_role and current_primary_role.role else "不明"
                                                logger.info(f"Webhook ロール更新前 - ユーザー: {user_to_update.email}, 現在のロール: {current_role_name}")
                                                
                                                await crud_user.update_user(db, db_user=user_to_update, user_in=UserUpdate(role=target_role_name))
                                                logger.info(f"ユーザー {user_id} のプライマリロールを '{target_role_name}' (ID: {assigned_role_id}) に更新しました。")
                                                
                                                # ★ デバッグ用: 更新後の確認（コミット前）
                                                await db.flush()  # セッションをフラッシュして変更を反映
                                                updated_user = await crud_user.get_user(db, user_id)
                                                if updated_user:
                                                    updated_primary_role = next((ur for ur in updated_user.user_roles if ur.is_primary), None)
                                                    updated_role_name = updated_primary_role.role.name if updated_primary_role and updated_primary_role.role else "不明"
                                                    logger.info(f"Webhook ロール更新後（コミット前） - ユーザー: {updated_user.email}, 新しいロール: {updated_role_name}")
                                                else:
                                                    logger.error(f"Webhook ロール更新後のユーザー情報再取得に失敗: {user_id}")
                                                
                                                # ★ ロール更新後、既存のJWTトークンを無効化してユーザーに再ログインを促す
                                                try:
                                                    from app.crud.token_blacklist import add_to_blacklist
                                                    # 該当ユーザーのすべてのアクティブトークンを無効化
                                                    # （実装により異なるが、user_idベースで無効化）
                                                    logger.info(f"ユーザー {user_id} のロール更新により、既存トークンの再検証が必要です。")
                                                except Exception as token_invalidate_error:
                                                    logger.warning(f"トークン無効化処理でエラー（ユーザー: {user_id}）: {token_invalidate_error}")
                                            else:
                                                logger.warning(f"ロール割り当て対象のユーザー {user_id} がDBで見つかりません。")
                                        else:
                                            logger.error(f"指定されたロールID {assigned_role_id} (\"{assigned_role_id_str}\") に該当するロールがDBで見つかりません。")
                                    except ValueError:
                                        logger.error(f"メタデータの assigned_role '{assigned_role_id_str}' は有効なUUIDではありません。")
                                    except Exception as e_role_assign:
                                        logger.error(f"ロール割り当て処理中に予期せぬエラー: {e_role_assign}", exc_info=True)
                                else:
                                    logger.info(f"Stripe Product {stripe_product_id_from_sub} のメタデータに assigned_role が設定されていません。")
                            else:
                                logger.warning(f"Stripe Product {stripe_product_id_from_sub} のメタデータ取得に失敗、またはメタデータが存在しません。")
                        else:
                            logger.warning(f"サブスクリプションアイテムからStripe Product IDを取得できませんでした。Subscription ID: {stripe_subscription_id}")
                    else:
                        logger.warning(f"サブスクリプション {stripe_subscription_id} にアイテムが見つかりません。ロール割り当て不可。")
                except Exception as e_outer_role_assign:
                    logger.error(f"ロール割り当てブロック全体で予期せぬエラー: {e_outer_role_assign}", exc_info=True)
            elif not stripe_subscription_id:
                logger.warning(f"checkout.session.completed イベントに subscription ID が含まれていません。ロール割り当て不可。 Session ID: {session.id}")
            elif not ('stripe_sub_data' in locals() and stripe_sub_data):
                 logger.warning(f"stripe_sub_dataが利用できませんでした。ロール割り当て不可。 Subscription ID: {stripe_subscription_id}, Session ID: {session.id}")
            # --- ★ ロール割り当て処理ここまで ---

            if db_campaign_code:
                await crud_subscription.increment_campaign_code_usage(db, db_campaign_code.id)

            user = await crud_user.get_user(db, user_id)
            if user and user.status != SchemaUserStatus.ACTIVE:
                 await crud_user.update_user(db, db_user=user, user_in=UserUpdate(status=SchemaUserStatus.ACTIVE))

        # PaymentIntent関連イベント（3Dセキュア対応）
        elif event_type == 'payment_intent.succeeded':
            payment_intent = data
            logger.info(f"PaymentIntent Succeeded: {payment_intent['id']}")
            
            # PaymentIntentのメタデータからユーザー情報を取得
            metadata = payment_intent.get('metadata', {})
            user_id_str = metadata.get('user_id')
            price_id = metadata.get('price_id')
            
            if user_id_str and price_id:
                try:
                    user_id = UUID(user_id_str)
                    
                    # 決済履歴に記録
                    payment_history_data = {
                        "user_id": user_id,
                        "stripe_payment_intent_id": payment_intent['id'],
                        "amount": payment_intent['amount'],
                        "currency": payment_intent['currency'],
                        "status": payment_intent['status'],
                        "payment_method": payment_intent.get('payment_method'),
                        "payment_date": datetime.fromtimestamp(payment_intent['created'])
                    }
                    
                    await crud_subscription.create_payment_history(
                        db, 
                        crud_subscription.PaymentHistoryCreate(**payment_history_data)
                    )
                    logger.info(f"PaymentIntent {payment_intent['id']} の決済履歴を記録しました")
                    
                    # 決済成功メール通知を送信
                    try:
                        user = await crud_user.get_user(db, user_id)
                        if user:
                            # プラン名を取得
                            plan = await crud_subscription.get_plan_by_price_id(db, price_id)
                            plan_name = plan.name if plan else None
                            
                            await email_service.send_payment_success_notification(
                                user_email=user.email,
                                user_name=user.display_name or user.email.split('@')[0],
                                amount=payment_intent['amount'],
                                currency=payment_intent['currency'],
                                payment_intent_id=payment_intent['id'],
                                subscription_name=plan_name
                            )
                            logger.info(f"決済成功メールを送信しました: {user.email}")
                        else:
                            logger.warning(f"決済成功メール送信: ユーザーが見つかりません (ID: {user_id})")
                    except Exception as e_email:
                        logger.error(f"決済成功メール送信に失敗: {e_email}", exc_info=True)
                    
                except ValueError:
                    logger.error(f"Webhook payment_intent.succeeded: 無効なuser_id形式: {user_id_str}")
                except Exception as e:
                    logger.error(f"PaymentIntent succeeded処理エラー: {e}", exc_info=True)

        elif event_type == 'payment_intent.requires_action':
            payment_intent = data
            logger.info(f"PaymentIntent Requires Action (3D Secure): {payment_intent['id']}")
            
            # 3Dセキュア認証が必要な場合の処理
            metadata = payment_intent.get('metadata', {})
            user_id_str = metadata.get('user_id')
            
            if user_id_str:
                logger.info(f"User {user_id_str} の決済で3Dセキュア認証が要求されました (PaymentIntent: {payment_intent['id']})")
                
                # 3Dセキュア認証リマインダーメールを送信
                try:
                    user_id = UUID(user_id_str)
                    user = await crud_user.get_user(db, user_id)
                    if user:
                        await email_service.send_3ds_reminder_notification(
                            user_email=user.email,
                            user_name=user.display_name or user.email.split('@')[0],
                            amount=payment_intent['amount'],
                            currency=payment_intent['currency'],
                            payment_intent_id=payment_intent['id']
                        )
                        logger.info(f"3Dセキュア認証リマインダーメールを送信しました: {user.email}")
                    else:
                        logger.warning(f"3DSリマインダー送信: ユーザーが見つかりません (ID: {user_id})")
                except Exception as e_email:
                    logger.error(f"3Dセキュア認証リマインダーメール送信に失敗: {e_email}", exc_info=True)

        elif event_type == 'payment_intent.payment_failed':
            payment_intent = data
            logger.info(f"PaymentIntent Failed: {payment_intent['id']}")
            
            # 決済失敗時の処理
            metadata = payment_intent.get('metadata', {})
            user_id_str = metadata.get('user_id')
            
            if user_id_str:
                try:
                    user_id = UUID(user_id_str)
                    
                    # 失敗した決済履歴も記録
                    payment_history_data = {
                        "user_id": user_id,
                        "stripe_payment_intent_id": payment_intent['id'],
                        "amount": payment_intent['amount'],
                        "currency": payment_intent['currency'],
                        "status": payment_intent['status'],
                        "payment_method": payment_intent.get('payment_method'),
                        "payment_date": datetime.fromtimestamp(payment_intent['created'])
                    }
                    
                    await crud_subscription.create_payment_history(
                        db, 
                        crud_subscription.PaymentHistoryCreate(**payment_history_data)
                    )
                    logger.info(f"PaymentIntent {payment_intent['id']} の失敗記録を保存しました")
                    
                    # 決済失敗メール通知を送信
                    try:
                        user = await crud_user.get_user(db, user_id)
                        if user:
                            # 失敗理由を取得（可能であれば）
                            failure_reason = None
                            if 'last_payment_error' in payment_intent and payment_intent['last_payment_error']:
                                error_info = payment_intent['last_payment_error']
                                if error_info.get('message'):
                                    failure_reason = error_info['message']
                            
                            await email_service.send_payment_failed_notification(
                                user_email=user.email,
                                user_name=user.display_name or user.email.split('@')[0],
                                amount=payment_intent['amount'],
                                currency=payment_intent['currency'],
                                payment_intent_id=payment_intent['id'],
                                failure_reason=failure_reason
                            )
                            logger.info(f"決済失敗メールを送信しました: {user.email}")
                        else:
                            logger.warning(f"決済失敗メール送信: ユーザーが見つかりません (ID: {user_id})")
                    except Exception as e_email:
                        logger.error(f"決済失敗メール送信に失敗: {e_email}", exc_info=True)
                    
                except ValueError:
                    logger.error(f"Webhook payment_intent.payment_failed: 無効なuser_id形式: {user_id_str}")
                except Exception as e:
                    logger.error(f"PaymentIntent failed処理エラー: {e}", exc_info=True)

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
