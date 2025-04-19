from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Body
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.stripe_service import StripeService
from app.schemas.subscription import (
    SubscriptionResponse, SubscriptionPlanResponse, PaymentHistoryResponse,
    CreateCheckoutSessionRequest, CheckoutSessionResponse, 
    ManageSubscriptionRequest, WebhookEventValidation,
    CampaignCodeResponse, CampaignCodeCreate, CampaignCodeUpdate,
    VerifyCampaignCodeRequest, VerifyCampaignCodeResponse
)
from app.crud import subscription as crud
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging
import json
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def get_subscription_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    利用可能なサブスクリプションプランの一覧を取得する
    """
    try:
        plans = crud.get_active_subscription_plans(db)
        return plans
    except Exception as e:
        logger.error(f"サブスクリプションプラン取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="サブスクリプションプランの取得中にエラーが発生しました"
        )

@router.get("/user-subscription", response_model=Optional[SubscriptionResponse])
async def get_user_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ユーザーのアクティブなサブスクリプション情報を取得する
    """
    try:
        subscription = crud.get_active_user_subscription(db, current_user.id)
        return subscription
    except Exception as e:
        logger.error(f"ユーザーのサブスクリプション取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="サブスクリプション情報の取得中にエラーが発生しました"
        )

@router.get("/payment-history", response_model=List[PaymentHistoryResponse])
async def get_payment_history(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ユーザーの支払い履歴を取得する
    """
    try:
        payments = crud.get_user_payment_history(db, current_user.id, skip, limit)
        return payments
    except Exception as e:
        logger.error(f"支払い履歴取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="支払い履歴の取得中にエラーが発生しました"
        )

@router.post("/verify-campaign-code", response_model=VerifyCampaignCodeResponse)
async def verify_campaign_code(
    request: VerifyCampaignCodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    キャンペーンコードの有効性を検証する
    """
    try:
        # キャンペーンコードを検証
        result = crud.verify_campaign_code(db, request.code, request.plan_id)
        
        return VerifyCampaignCodeResponse(
            valid=result["valid"],
            message=result["message"],
            discount_type=result.get("discount_type"),
            discount_value=result.get("discount_value"),
            original_amount=result.get("original_amount"),
            discounted_amount=result.get("discounted_amount"),
            campaign_code_id=result.get("campaign_code_id")
        )
    except Exception as e:
        logger.error(f"キャンペーンコード検証エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="キャンペーンコードの検証中にエラーが発生しました"
        )

@router.post("/create-checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CreateCheckoutSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Stripeのチェックアウトセッションを作成する
    """
    try:
        # 既存のアクティブなサブスクリプションがあるか確認
        existing_subscription = crud.get_active_user_subscription(db, current_user.id)
        if existing_subscription:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="既にアクティブなサブスクリプションがあります"
            )
        
        # プランの存在確認
        plan = crud.get_subscription_plan(db, request.plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたプランが見つかりません"
            )
        
        # Stripeカスタマーの作成または取得
        stripe_customer_id = None
        for subscription in crud.get_user_subscriptions(db, current_user.id):
            if subscription.stripe_customer_id:
                stripe_customer_id = subscription.stripe_customer_id
                break
        
        if not stripe_customer_id:
            stripe_customer_id = StripeService.create_customer(
                email=current_user.email,
                name=current_user.full_name,
                metadata={"user_id": str(current_user.id)}
            )
        
        # セッションメタデータを準備
        metadata = {
            "user_id": str(current_user.id),
            "plan_id": str(plan.id),
            "plan_name": plan.name
        }
        
        # キャンペーンコードの処理
        campaign_code_id = None
        discounts = None
        
        if request.campaign_code:
            # キャンペーンコードを検証
            verification = crud.verify_campaign_code(db, request.campaign_code, request.plan_id)
            
            if not verification["valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=verification["message"]
                )
                
            campaign_code_id = verification["campaign_code_id"]
            metadata["campaign_code_id"] = str(campaign_code_id)
            
            # 割引情報を作成
            db_campaign_code = crud.get_campaign_code(db, campaign_code_id)
            
            # Stripeクーポンの作成
            try:
                discount_type = "percentage" if db_campaign_code.discount_type == "percentage" else "fixed"
                
                coupon = StripeService.create_coupon(
                    discount_type=discount_type,
                    discount_value=db_campaign_code.discount_value,
                    duration="once",
                    currency="jpy",
                    name=f"キャンペーンコード: {db_campaign_code.code}",
                    metadata={
                        "campaign_code_id": str(campaign_code_id),
                        "owner_id": str(db_campaign_code.owner_id) if db_campaign_code.owner_id else None
                    }
                )
                
                # 割引を適用
                discounts = [{"coupon": coupon.id}]
                
            except Exception as e:
                logger.error(f"Stripeクーポン作成エラー: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="割引処理中にエラーが発生しました"
                )
        
        # チェックアウトセッションの作成
        checkout_session = StripeService.create_checkout_session(
            customer_id=stripe_customer_id,
            price_id=plan.price_id,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata=metadata,
            discounts=discounts
        )
        
        return checkout_session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"チェックアウトセッション作成エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="チェックアウトセッションの作成中にエラーが発生しました"
        )

@router.post("/create-portal-session")
async def create_portal_session(
    return_url: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Stripe顧客ポータルセッションを作成する
    """
    try:
        # アクティブなサブスクリプションを取得
        subscription = crud.get_active_user_subscription(db, current_user.id)
        if not subscription or not subscription.stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="アクティブなサブスクリプションが見つかりません"
            )
        
        # ポータルセッションURLを作成
        portal_url = StripeService.create_portal_session(
            customer_id=subscription.stripe_customer_id,
            return_url=return_url
        )
        
        return {"url": portal_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ポータルセッション作成エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="顧客ポータルセッションの作成中にエラーが発生しました"
        )

@router.post("/manage-subscription")
async def manage_subscription(
    request: ManageSubscriptionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    サブスクリプションを管理する（キャンセル、再開、プラン変更）
    """
    try:
        # サブスクリプションの存在確認
        subscription = crud.get_subscription(db, request.subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたサブスクリプションが見つかりません"
            )
        
        # 権限確認（自分のサブスクリプションかどうか）
        if subscription.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="このサブスクリプションを管理する権限がありません"
            )
        
        # アクションの実行
        if request.action == "cancel":
            result = StripeService.cancel_subscription(subscription.stripe_subscription_id)
            crud.update_subscription(db, subscription.id, {"status": "canceled", "canceled_at": result.canceled_at})
            return {"message": "サブスクリプションが正常にキャンセルされました"}
            
        elif request.action == "reactivate":
            result = StripeService.reactivate_subscription(subscription.stripe_subscription_id)
            crud.update_subscription(db, subscription.id, {"status": "active", "canceled_at": None})
            return {"message": "サブスクリプションが正常に再開されました"}
            
        elif request.action == "update":
            if not request.plan_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="プラン変更には新しいプランIDが必要です"
                )
                
            # 新しいプランの存在確認
            new_plan = crud.get_subscription_plan(db, request.plan_id)
            if not new_plan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="指定された新しいプランが見つかりません"
                )
                
            result = StripeService.update_subscription(subscription.stripe_subscription_id, new_plan.price_id)
            crud.update_subscription(db, subscription.id, {
                "plan_name": new_plan.name,
                "price_id": new_plan.price_id
            })
            return {"message": "サブスクリプションプランが正常に更新されました"}
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不正なアクション。'cancel', 'reactivate', または 'update' を指定してください"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"サブスクリプション管理エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="サブスクリプションの管理中にエラーが発生しました"
        )

@router.post("/webhook", status_code=status.HTTP_200_OK)
async def webhook_received(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Stripeからのwebhookイベントを処理する
    """
    try:
        # リクエストボディと署名を取得
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        if not sig_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="stripe-signatureヘッダーがありません"
            )
            
        # イベントの検証
        event = StripeService.verify_webhook_signature(payload.decode(), sig_header)
        
        # イベントタイプに応じた処理
        event_type = event["type"]
        event_data = event["data"]["object"]
        
        if event_type == "checkout.session.completed":
            # チェックアウト完了時の処理
            await handle_checkout_completed(db, event_data)
            
        elif event_type == "invoice.paid":
            # 請求書支払い完了時の処理
            await handle_invoice_paid(db, event_data)
            
        elif event_type == "invoice.payment_failed":
            # 請求書支払い失敗時の処理
            await handle_payment_failed(db, event_data)
            
        elif event_type == "customer.subscription.created":
            # サブスクリプション作成時の処理
            await handle_subscription_created(db, event_data)
            
        elif event_type == "customer.subscription.updated":
            # サブスクリプション更新時の処理
            await handle_subscription_updated(db, event_data)
            
        elif event_type == "customer.subscription.deleted":
            # サブスクリプション削除時の処理
            await handle_subscription_deleted(db, event_data)
            
        # 他のイベントタイプも必要に応じて追加可能
        
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"Webhook処理エラー: {str(e)}")
        # Webhookエラーは200を返して再試行を防ぐ（エラーログのみ）
        return {"status": "error", "message": str(e)}

# Webhookイベントハンドラー関数

async def handle_checkout_completed(db: Session, event_data: Dict[str, Any]):
    """チェックアウト完了イベントの処理"""
    logger.info("チェックアウト完了イベント処理")
    
    try:
        # メタデータからユーザーIDとプラン情報を取得
        metadata = event_data.get("metadata", {})
        user_id = metadata.get("user_id")
        plan_name = metadata.get("plan_name")
        
        if not user_id or not plan_name:
            logger.error("メタデータに必要な情報がありません")
            return
            
        # サブスクリプションIDを取得
        subscription_id = event_data.get("subscription")
        if not subscription_id:
            logger.error("サブスクリプションIDがありません")
            return
            
        # Stripeからサブスクリプション詳細を取得
        subscription_data = StripeService.get_subscription(subscription_id)
        
        # 顧客IDを取得
        customer_id = event_data.get("customer")
        
        # プラン情報を取得
        price_id = None
        for item in subscription_data.get("items", {}).get("data", []):
            if item.get("price", {}).get("id"):
                price_id = item["price"]["id"]
                break
                
        if not price_id:
            logger.error("価格IDが見つかりません")
            return
            
        # サブスクリプションレコードを作成
        from app.schemas.subscription import SubscriptionCreate
        subscription_create = SubscriptionCreate(
            user_id=UUID(user_id),
            plan_name=plan_name,
            price_id=price_id,
            status="active"
        )
        
        new_subscription = crud.create_subscription(db, subscription_create)
        
        # Stripeの情報でアップデート
        crud.update_subscription(db, new_subscription.id, {
            "stripe_customer_id": customer_id,
            "stripe_subscription_id": subscription_id,
            "current_period_start": subscription_data.get("current_period_start"),
            "current_period_end": subscription_data.get("current_period_end"),
        })
        
        logger.info(f"サブスクリプションが正常に作成されました: {new_subscription.id}")
        
    except Exception as e:
        logger.error(f"チェックアウト完了処理エラー: {str(e)}")

async def handle_invoice_paid(db: Session, event_data: Dict[str, Any]):
    """請求書支払い完了イベントの処理"""
    logger.info("請求書支払い完了イベント処理")
    
    try:
        customer_id = event_data.get("customer")
        subscription_id = event_data.get("subscription")
        
        if not customer_id or not subscription_id:
            logger.error("顧客IDまたはサブスクリプションIDがありません")
            return
            
        # サブスクリプションをDBから取得
        db_subscription = crud.get_subscription_by_stripe_id(db, subscription_id)
        if not db_subscription:
            logger.error(f"サブスクリプションが見つかりません: {subscription_id}")
            return
            
        # 支払い履歴を作成
        from app.schemas.subscription import PaymentHistoryCreate
        payment_create = PaymentHistoryCreate(
            user_id=db_subscription.user_id,
            subscription_id=db_subscription.id,
            stripe_invoice_id=event_data.get("id"),
            amount=event_data.get("amount_paid", 0),
            currency=event_data.get("currency", "jpy"),
            status="succeeded",
            payment_method=event_data.get("payment_method", None),
            payment_date=event_data.get("created")
        )
        
        payment = crud.create_payment_history(db, payment_create)
        logger.info(f"支払い履歴が正常に作成されました: {payment.id}")
        
    except Exception as e:
        logger.error(f"請求書支払い完了処理エラー: {str(e)}")

async def handle_payment_failed(db: Session, event_data: Dict[str, Any]):
    """請求書支払い失敗イベントの処理"""
    logger.info("請求書支払い失敗イベント処理")
    
    try:
        customer_id = event_data.get("customer")
        subscription_id = event_data.get("subscription")
        
        if not customer_id or not subscription_id:
            logger.error("顧客IDまたはサブスクリプションIDがありません")
            return
            
        # サブスクリプションをDBから取得
        db_subscription = crud.get_subscription_by_stripe_id(db, subscription_id)
        if not db_subscription:
            logger.error(f"サブスクリプションが見つかりません: {subscription_id}")
            return
            
        # サブスクリプションステータスを更新
        crud.update_subscription(db, db_subscription.id, {"status": "past_due"})
        
        # 支払い履歴を作成
        from app.schemas.subscription import PaymentHistoryCreate
        payment_create = PaymentHistoryCreate(
            user_id=db_subscription.user_id,
            subscription_id=db_subscription.id,
            stripe_invoice_id=event_data.get("id"),
            amount=event_data.get("amount_due", 0),
            currency=event_data.get("currency", "jpy"),
            status="failed",
            payment_method=event_data.get("payment_method", None),
            payment_date=event_data.get("created")
        )
        
        payment = crud.create_payment_history(db, payment_create)
        logger.info(f"失敗した支払い履歴が作成されました: {payment.id}")
        
    except Exception as e:
        logger.error(f"請求書支払い失敗処理エラー: {str(e)}")

async def handle_subscription_created(db: Session, event_data: Dict[str, Any]):
    """サブスクリプション作成イベントの処理"""
    logger.info("サブスクリプション作成イベント処理")
    # このイベントは基本的にcheckout.session.completedで処理されるため、特別な処理は不要

async def handle_subscription_updated(db: Session, event_data: Dict[str, Any]):
    """サブスクリプション更新イベントの処理"""
    logger.info("サブスクリプション更新イベント処理")
    
    try:
        subscription_id = event_data.get("id")
        if not subscription_id:
            logger.error("サブスクリプションIDがありません")
            return
            
        # サブスクリプションをDBから取得
        db_subscription = crud.get_subscription_by_stripe_id(db, subscription_id)
        if not db_subscription:
            logger.error(f"サブスクリプションが見つかりません: {subscription_id}")
            return
            
        # サブスクリプションステータスを更新
        update_data = {
            "status": event_data.get("status", db_subscription.status),
            "current_period_start": event_data.get("current_period_start", db_subscription.current_period_start),
            "current_period_end": event_data.get("current_period_end", db_subscription.current_period_end),
            "cancel_at": event_data.get("cancel_at", db_subscription.cancel_at)
        }
        
        crud.update_subscription(db, db_subscription.id, update_data)
        logger.info(f"サブスクリプションが更新されました: {db_subscription.id}")
        
    except Exception as e:
        logger.error(f"サブスクリプション更新処理エラー: {str(e)}")

async def handle_subscription_deleted(db: Session, event_data: Dict[str, Any]):
    """サブスクリプション削除イベントの処理"""
    logger.info("サブスクリプション削除イベント処理")
    
    try:
        subscription_id = event_data.get("id")
        if not subscription_id:
            logger.error("サブスクリプションIDがありません")
            return
            
        # サブスクリプションをDBから取得
        db_subscription = crud.get_subscription_by_stripe_id(db, subscription_id)
        if not db_subscription:
            logger.error(f"サブスクリプションが見つかりません: {subscription_id}")
            return
            
        # サブスクリプションステータスを更新
        update_data = {
            "status": "canceled",
            "canceled_at": event_data.get("canceled_at", datetime.utcnow()),
            "is_active": False
        }
        
        crud.update_subscription(db, db_subscription.id, update_data)
        logger.info(f"サブスクリプションが削除されました: {db_subscription.id}")
        
    except Exception as e:
        logger.error(f"サブスクリプション削除処理エラー: {str(e)}")

# キャンペーンコード管理エンドポイント
@router.get("/campaign-codes", response_model=List[CampaignCodeResponse])
async def get_campaign_codes(
    skip: int = 0,
    limit: int = 20,
    owner_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    キャンペーンコードの一覧を取得する
    管理者は全てのコードを取得可能、一般ユーザーは自分のコードのみ
    """
    try:
        # 管理者権限チェック（ロールベースのアクセス制御）
        is_admin = current_user.role and current_user.role.permissions and "admin" in current_user.role.permissions.lower()
        
        # 管理者で特定のユーザーのコードを要求された場合
        if is_admin and owner_id:
            campaign_codes = crud.get_user_campaign_codes(db, owner_id, skip, limit)
        # 管理者の場合は全てのコードを取得
        elif is_admin:
            campaign_codes = crud.get_all_campaign_codes(db, skip, limit)
        # 一般ユーザーは自分のコードのみ取得可能
        else:
            campaign_codes = crud.get_user_campaign_codes(db, current_user.id, skip, limit)
            
        return campaign_codes
    except Exception as e:
        logger.error(f"キャンペーンコード一覧取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="キャンペーンコードの取得中にエラーが発生しました"
        )

@router.post("/campaign-codes", response_model=CampaignCodeResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign_code(
    campaign_code: CampaignCodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    新しいキャンペーンコードを作成する
    管理者は任意のユーザーのコードを作成可能、一般ユーザーは自分のコードのみ
    """
    try:
        # 管理者権限チェック
        is_admin = current_user.role and current_user.role.permissions and "admin" in current_user.role.permissions.lower()
        
        # 既存のコードとの重複チェック
        existing_code = crud.get_campaign_code_by_code(db, campaign_code.code)
        if existing_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"コード '{campaign_code.code}' は既に使用されています"
            )
        
        # 管理者でない場合は自分のコードのみ作成可能
        if not is_admin:
            campaign_code.owner_id = current_user.id
        # 管理者で所有者が指定されていない場合は自分を所有者に
        elif not campaign_code.owner_id:
            campaign_code.owner_id = current_user.id
            
        new_campaign_code = crud.create_campaign_code(db, campaign_code)
        return new_campaign_code
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"キャンペーンコード作成エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="キャンペーンコードの作成中にエラーが発生しました"
        )

@router.get("/campaign-codes/{campaign_code_id}", response_model=CampaignCodeResponse)
async def get_campaign_code(
    campaign_code_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    特定のキャンペーンコードの詳細を取得する
    """
    try:
        campaign_code = crud.get_campaign_code(db, campaign_code_id)
        if not campaign_code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたキャンペーンコードが見つかりません"
            )
            
        # 管理者権限チェック
        is_admin = current_user.role and current_user.role.permissions and "admin" in current_user.role.permissions.lower()
        
        # アクセス権チェック（管理者または所有者のみ）
        if not is_admin and campaign_code.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="このキャンペーンコードにアクセスする権限がありません"
            )
            
        return campaign_code
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"キャンペーンコード取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="キャンペーンコードの取得中にエラーが発生しました"
        )

@router.put("/campaign-codes/{campaign_code_id}", response_model=CampaignCodeResponse)
async def update_campaign_code(
    campaign_code_id: UUID,
    campaign_code_update: CampaignCodeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    キャンペーンコードを更新する
    """
    try:
        # コードの存在確認
        db_campaign_code = crud.get_campaign_code(db, campaign_code_id)
        if not db_campaign_code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたキャンペーンコードが見つかりません"
            )
            
        # 管理者権限チェック
        is_admin = current_user.role and current_user.role.permissions and "admin" in current_user.role.permissions.lower()
        
        # アクセス権チェック（管理者または所有者のみ）
        if not is_admin and db_campaign_code.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="このキャンペーンコードを更新する権限がありません"
            )
            
        updated_campaign_code = crud.update_campaign_code(db, campaign_code_id, campaign_code_update)
        return updated_campaign_code
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"キャンペーンコード更新エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="キャンペーンコードの更新中にエラーが発生しました"
        )

@router.delete("/campaign-codes/{campaign_code_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign_code(
    campaign_code_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    キャンペーンコードを削除する
    """
    try:
        # コードの存在確認
        db_campaign_code = crud.get_campaign_code(db, campaign_code_id)
        if not db_campaign_code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたキャンペーンコードが見つかりません"
            )
            
        # 管理者権限チェック
        is_admin = current_user.role and current_user.role.permissions and "admin" in current_user.role.permissions.lower()
        
        # アクセス権チェック（管理者または所有者のみ）
        if not is_admin and db_campaign_code.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="このキャンペーンコードを削除する権限がありません"
            )
            
        crud.delete_campaign_code(db, campaign_code_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"キャンペーンコード削除エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="キャンペーンコードの削除中にエラーが発生しました"
        ) 