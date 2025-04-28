from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Body
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, require_permission
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
from app.crud import user as crud_user
from app.schemas.user import UserUpdate, UserStatus

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/stripe-plans", response_model=List[SubscriptionPlanResponse])
async def get_stripe_plans(
    db: Session = Depends(get_db)
):
    """
    Stripeから直接サブスクリプションプラン情報を取得する（パブリックエンドポイント）
    """
    try:
        # Stripeから直接プラン情報を取得
        logger.info("Stripeからプラン情報を取得します")
        stripe_prices = StripeService.list_prices(active=True)
        logger.info(f"取得したプラン数: {len(stripe_prices)}")
        
        # Stripeのレスポンスを必要な形式に変換
        plans = []
        for price in stripe_prices:
            try:
                # デバッグ情報
                price_id = price.get("id", "不明")
                logger.debug(f"プラン処理中: {price_id}")
                
                # プラン全体の構造をデバッグ出力
                logger.debug(f"Price データ構造: {type(price)}")
                if isinstance(price, dict):
                    logger.debug(f"Price キー一覧: {list(price.keys())}")
                    # unitの有無をチェック
                    if price.get("unit_amount") is None:
                        logger.warning(f"プラン {price_id} のunit_amountがありません")
                
                # プロダクト情報を取得（すでに展開されている場合とIDのみの場合を処理）
                product_data = price.get("product")
                if product_data:
                    logger.debug(f"Product data type: {type(product_data)}")
                else:
                    logger.warning(f"プラン {price_id} のproduct情報がありません")
                
                product = None
                
                # productがオブジェクトかどうかをチェック
                if isinstance(product_data, dict) and "name" in product_data:
                    # すでに展開されたプロダクトデータを使用
                    product = product_data
                    logger.debug(f"プラン {price_id} は展開済みのproduct情報を持っています: {product.get('name')}")
                elif isinstance(product_data, str):
                    # IDのみの場合は商品情報を取得
                    try:
                        logger.debug(f"プラン {price_id} のproduct IDから商品情報を取得: {product_data}")
                        product = StripeService.get_product(product_data)
                    except Exception as e:
                        logger.error(f"商品情報取得エラー（ID: {product_data}）: {str(e)}")
                        continue
                else:
                    # 型が不明な場合はログに記録してスキップ
                    logger.error(f"不明なproduct型: {type(product_data)} 値: {product_data}")
                    continue
                
                # 必要なデータを抽出
                if product is None:
                    logger.error(f"プロダクト情報がNullです。price_id: {price_id}")
                    continue
                
                # 安全に値を取得（存在しない場合はデフォルト値を使用）
                plan_id = price.get("id", "")
                plan_name = product.get("name", "不明なプラン")
                plan_description = product.get("description") or "詳細情報なし"
                
                # 金額情報の安全な取得（unitは任意/なしの場合は0設定）
                unit_amount = price.get("unit_amount")
                if unit_amount is not None:
                    plan_amount = unit_amount
                else:
                    logger.warning(f"プラン {plan_id} の金額情報がありません。0として扱います。")
                    plan_amount = 0
                
                plan_currency = price.get("currency", "jpy")
                
                # recurring が None の場合があるのでさらに安全に取得
                recurring = price.get("recurring")
                if recurring is not None and isinstance(recurring, dict):
                    plan_interval = recurring.get("interval", "month")
                else:
                    plan_interval = "month"  # デフォルト値
                
                plan_is_active = price.get("active", True)
                
                logger.debug(f"プラン情報: id={plan_id}, name={plan_name}, amount={plan_amount}")
                
                # タイムスタンプの安全な取得
                created_timestamp = price.get("created")
                if created_timestamp:
                    created_at = datetime.fromtimestamp(created_timestamp)
                    updated_at = datetime.fromtimestamp(created_timestamp)
                else:
                    current_time = datetime.utcnow()
                    created_at = current_time
                    updated_at = current_time
                
                plan = SubscriptionPlanResponse(
                    id=plan_id,
                    name=plan_name,
                    description=plan_description,
                    price_id=plan_id,
                    amount=plan_amount,
                    currency=plan_currency,
                    interval=plan_interval,
                    is_active=plan_is_active,
                    created_at=created_at,
                    updated_at=updated_at
                )
                plans.append(plan)
                logger.debug(f"プラン '{plan_name}' を追加しました")
            except Exception as e:
                logger.error(f"プラン情報変換エラー: {str(e)}", exc_info=True)
                continue
            
        # プランが取得できなかった場合はデモデータを返す
        if not plans:
            logger.warning("Stripeからプランを取得できませんでした。デモデータを使用します。")
            now = datetime.utcnow()
            plans = [
                SubscriptionPlanResponse(
                    id="price_demo_standard",  # Stripeの命名規則に合わせて修正
                    name="スタンダードプラン",
                    description="ベーシックな機能が使えるスタンダードなプランです。",
                    price_id="price_demo_standard",
                    amount=1980,
                    currency="jpy",
                    interval="month",
                    is_active=True,
                    created_at=now,
                    updated_at=now
                ),
                SubscriptionPlanResponse(
                    id="price_demo_premium",  # Stripeの命名規則に合わせて修正
                    name="プレミアムプラン",
                    description="全ての機能が使える高機能なプランです。",
                    price_id="price_demo_premium",
                    amount=3980,
                    currency="jpy",
                    interval="month",
                    is_active=True,
                    created_at=now,
                    updated_at=now
                )
            ]
        
        logger.info(f"返却するプラン数: {len(plans)}")
        return plans
    except Exception as e:
        logger.error(f"Stripeプラン取得エラー: {str(e)}", exc_info=True)
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
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    キャンペーンコードの有効性を検証する
    """
    try:
        # Stripeから直接価格情報を取得
        price = None
        price_id = request.price_id
        
        try:
            price = StripeService.get_price(price_id)
        except Exception as e:
            logger.error(f"Stripe価格情報取得エラー: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"指定された価格ID({price_id})は無効です"
            )
            
        # 金額の取得
        original_amount = price.get("unit_amount")
        if original_amount is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="価格情報から金額を取得できませんでした"
            )
            
        # キャンペーンコードを検証
        result = crud.verify_campaign_code(db, request.code, request.price_id)
        
        # 有効な場合は割引を計算
        if result.get("valid"):
            discount_type = result.get("discount_type", "percentage")
            discount_value = result.get("discount_value", 0)
            
            # 割引額の計算
            discounted_amount = original_amount
            if discount_type == "percentage":
                # 割合による割引
                discount = int(original_amount * discount_value / 100)
                discounted_amount = original_amount - discount
            elif discount_type == "fixed":
                # 固定額割引
                discounted_amount = max(0, original_amount - int(discount_value))
            
            # レスポンスを作成
            return VerifyCampaignCodeResponse(
                valid=True,
                message="キャンペーンコードは有効です",
                discount_type=discount_type,
                discount_value=discount_value,
                original_amount=original_amount,
                discounted_amount=discounted_amount,
                campaign_code_id=result.get("campaign_code_id")
            )
        
        # 無効な場合はエラーメッセージを返す
        return VerifyCampaignCodeResponse(
            valid=False,
            message=result.get("message", "キャンペーンコードは無効です"),
            campaign_code_id=result.get("campaign_code_id")
        )
    except HTTPException:
        raise
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
    Stripeチェックアウトセッションを作成し、ユーザーをリダイレクトするURLを返す
    """
    logger.info(f"チェックアウトセッション作成リクエスト: User ID={current_user.id}, Price ID={request.price_id}")
    
    # 必須データの検証
    if not request.price_id or not request.success_url or not request.cancel_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必要なパラメータ（price_id, success_url, cancel_url）が不足しています。"
        )

    try:
        # Stripe 価格IDを検証
        try:
            logger.info(f"Stripe価格情報を取得: {request.price_id}")
            price = StripeService.get_price(request.price_id)
            logger.info(f"Stripe価格情報取得成功: {price.id}")
        except Exception as e:
            logger.error(f"Stripe価格情報取得エラー: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"指定された価格ID({request.price_id})は無効か、取得できませんでした。"
            )

        # 既存のStripe顧客IDを検索
        stripe_customer_id = crud.get_stripe_customer_id(db, current_user.id)
        
        # Stripe顧客IDがない場合は新規作成
        if not stripe_customer_id:
            logger.info(f"Stripe顧客IDが見つかりません。新規作成します: User ID={current_user.id}")
            try:
                customer = StripeService.create_customer(
                    email=current_user.email,
                    name=current_user.full_name,
                    metadata={'user_id': str(current_user.id)}
                )
                stripe_customer_id = customer
                crud.update_stripe_customer_id(db, current_user.id, stripe_customer_id)
                logger.info(f"Stripe顧客を作成しました: Customer ID={stripe_customer_id}")
            except Exception as e:
                logger.error(f"Stripe顧客作成エラー: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="顧客情報の作成中にエラーが発生しました。"
                )
        else:
            logger.info(f"既存のStripe顧客IDが見つかりました: {stripe_customer_id}")

        # キャンペーンコードの処理
        discount_info = None
        if request.campaign_code:
            logger.info(f"キャンペーンコードを検証: {request.campaign_code}")
            # Stripeから直接価格情報を取得
            try:
                price_data = StripeService.get_price(request.price_id)
                original_amount = price_data.get("unit_amount")
                if original_amount is None:
                    raise ValueError("価格情報から金額を取得できませんでした")
            except Exception as e:
                logger.error(f"Stripe価格情報取得エラー（キャンペーンコード検証時）: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="キャンペーンコードの検証中に価格情報の取得に失敗しました。"
                )
            
            # キャンペーンコードの検証
            try:
                campaign_result = crud.verify_campaign_code(db, request.campaign_code, request.price_id)
                if campaign_result.is_valid:
                    discount_info = {
                        "coupon": campaign_result.stripe_coupon_id, # クーポンIDを使用
                        "promotion_code": campaign_result.stripe_promotion_code_id # プロモーションコードIDを使用
                    }
                    logger.info(f"キャンペーンコード適用成功: {campaign_result}")
                else:
                    logger.warning(f"無効なキャンペーンコード: {request.campaign_code}")
                    # 無効なコードでもエラーにはせず、割引なしで続行
            except Exception as e:
                logger.error(f"キャンペーンコード検証中のエラー: {str(e)}", exc_info=True)
                # 検証エラーでもチェックアウトは続行（割引なし）

        # チェックアウトセッションの作成に必要なパラメータを構築
        checkout_params = {
            'customer_id': stripe_customer_id,
            'line_items': [{
                'price': request.price_id,
                'quantity': 1,
            }],
            'mode': 'subscription',
            'success_url': request.success_url,
            'cancel_url': request.cancel_url,
            'metadata': {
                'user_id': str(current_user.id),
                'plan_id': request.plan_id # フロントエンドから渡されるプランID（DB用）
            },
            # 課金詳細を必須とする
            'billing_address_collection': 'required',
            # 顧客情報更新を許可（住所変更など）
            'customer_update': {
                'address': 'auto',
                'name': 'auto',
                'shipping': 'auto'
            },
            # 税IDの収集を有効にする
            'tax_id_collection': {
                'enabled': True
            }
        }
        
        # 割引情報を追加
        if discount_info:
            # StripeのAPI仕様に合わせてdiscountsパラメータを設定
            checkout_params['discounts'] = []
            if discount_info.get("coupon"):
                checkout_params['discounts'].append({"coupon": discount_info["coupon"]})
            if discount_info.get("promotion_code"):
                checkout_params['discounts'].append({"promotion_code": discount_info["promotion_code"]})
        
        logger.debug(f"Stripeチェックアウトセッション作成パラメータ: {checkout_params}")

        # Stripeチェックアウトセッションの作成
        checkout_session = StripeService.create_checkout_session(
            customer_id=stripe_customer_id,
            price_id=request.price_id,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata=checkout_params.get('metadata'),
            discounts=checkout_params.get('discounts')
        )
        logger.info(f"Stripeチェックアウトセッション作成成功: Session ID={checkout_session.session_id}")

        return CheckoutSessionResponse(
            session_id=checkout_session.session_id,
            url=checkout_session.url
        )

    except HTTPException as e:
        logger.error(f"HTTPException in create_checkout_session: {e.status_code} - {e.detail}")
        raise e # HTTP例外はそのまま再送出
    except Exception as e:
        logger.error(f"予期せぬエラー in create_checkout_session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="チェックアウトセッションの作成中に予期せぬエラーが発生しました。"
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
            # price_idまたはplan_idが必要 (plan_idが指定された場合はそれをprice_idとして使用)
            price_id = request.price_id or request.plan_id
            if not price_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="プラン変更には新しい価格IDが必要です"
                )
                
            # Stripeから価格情報を取得
            try:
                price_info = StripeService.get_price(price_id)
                # 商品情報も取得
                product_info = StripeService.get_product(price_info.get('product'))
                plan_name = product_info.get('name', '不明なプラン')
            except Exception as e:
                logger.error(f"Stripe価格情報取得エラー: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"指定された価格ID({price_id})は無効です"
                )
                
            # Stripeサブスクリプション更新
            result = StripeService.update_subscription(subscription.stripe_subscription_id, price_id)
            crud.update_subscription(db, subscription.id, {
                "plan_name": plan_name,
                "price_id": price_id
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
        user_id_str = metadata.get("user_id") # 文字列として取得される可能性
        plan_name = metadata.get("plan_name")

        if not user_id_str or not plan_name:
            logger.error("メタデータに必要な情報がありません")
            return

        user_id = UUID(user_id_str) # UUID に変換

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

        # ユーザーを取得
        db_user = crud_user.get_user(db, user_id=user_id)
        if not db_user:
            logger.error(f"Webhook: ユーザーが見つかりません: {user_id}")
            # エラーハンドリングが必要な場合はここに追加（例: Responseを返す）
            # return Response(status_code=400)

        # サブスクリプションレコードを作成
        from app.schemas.subscription import SubscriptionCreate
        subscription_create = SubscriptionCreate(
            user_id=user_id,
            plan_name=plan_name,
            price_id=price_id,
            status="active" # サブスクリプション自体のステータス
        )

        # 既存のサブスクリプションを探す（重複作成を避ける）
        existing_subscription = crud.get_subscription_by_stripe_id(db, subscription_id)
        if existing_subscription:
            logger.info(f"Webhook: 既存のサブスクリプションが見つかりました。更新します: {existing_subscription.id}")
            # 既存のサブスクリプションを更新 (status など)
            crud.update_subscription(db, existing_subscription.id, {
                "status": "active", # 再アクティブ化の場合など
                "is_active": True, # ★ is_active を True に設定
                "stripe_customer_id": customer_id,
                "stripe_subscription_id": subscription_id,
                "current_period_start": subscription_data.get("current_period_start"),
                "current_period_end": subscription_data.get("current_period_end"),
                "plan_name": plan_name, # プラン変更の場合も考慮
                "price_id": price_id,
            })
            db_subscription = existing_subscription
        else:
            logger.info("Webhook: 新規サブスクリプションを作成します。")
            new_subscription = crud.create_subscription(db, subscription_create)
             # Stripeの情報でアップデート
            crud.update_subscription(db, new_subscription.id, {
                "stripe_customer_id": customer_id,
                "stripe_subscription_id": subscription_id,
                "current_period_start": subscription_data.get("current_period_start"),
                "current_period_end": subscription_data.get("current_period_end"),
                "is_active": True # ★ 新規作成時にも念のため is_active を True に設定
            })
            db_subscription = new_subscription

        # ユーザーステータスを 'active' (または適切な値) に更新
        if db_user:
            user_update_schema = UserUpdate(status=UserStatus.ACTIVE) # 更新用スキーマを作成
            try:
                # 既に 'active' の場合は更新しないオプションも検討可能
                if db_user.status != UserStatus.ACTIVE:
                    updated_user = crud_user.update_user(db, db_user=db_user, user_in=user_update_schema)
                    logger.info(f"Webhook: ユーザーステータスを更新しました: user_id={user_id}, status={updated_user.status}")
                else:
                    logger.info(f"Webhook: ユーザーステータスは既に '{db_user.status}' です。更新はスキップされました: user_id={user_id}")

            except Exception as user_update_e:
                logger.error(f"Webhook: ユーザーステータス更新中にエラー: {user_update_e}")
                # エラーハンドリング
        else:
             logger.warning(f"Webhook: ユーザーが見つからなかったため、ステータス更新はスキップされました: user_id={user_id_str}")

        logger.info(f"サブスクリプション処理が完了しました: Subscription ID={db_subscription.id}")

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
            
        # ユーザーを取得
        user_id = db_subscription.user_id
        db_user = crud_user.get_user(db, user_id=user_id)
        if not db_user:
            logger.error(f"Webhook(Invoice Paid): ユーザーが見つかりません: {user_id}")
            # 必要に応じてエラーハンドリング

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
        
        # ★ サブスクリプションのステータスを 'active', is_active を True に更新
        try:
            if db_subscription.status != "active" or not db_subscription.is_active:
                crud.update_subscription(db, db_subscription.id, {"status": "active", "is_active": True})
                logger.info(f"Webhook(Invoice Paid): サブスクリプションステータスを更新しました: id={db_subscription.id}, status=active, is_active=True")
            else:
                 logger.info(f"Webhook(Invoice Paid): サブスクリプションは既にアクティブです。更新はスキップされました: id={db_subscription.id}")
        except Exception as sub_update_e:
            logger.error(f"Webhook(Invoice Paid): サブスクリプションステータス更新中にエラー: {sub_update_e}")

        # ユーザーステータスを 'active' に更新 (サブスクリプションがアクティブな場合)
        if db_user:
            # 支払い成功時は基本的に active にする（トライアルからの移行なども含む）
            user_update_schema = UserUpdate(status=UserStatus.ACTIVE)
            try:
                if db_user.status != UserStatus.ACTIVE:
                    updated_user = crud_user.update_user(db, db_user=db_user, user_in=user_update_schema)
                    logger.info(f"Webhook(Invoice Paid): ユーザーステータスを更新しました: user_id={user_id}, status={updated_user.status}")
                else:
                    logger.info(f"Webhook(Invoice Paid): ユーザーステータスは既に '{db_user.status}' です。更新はスキップされました: user_id={user_id}")
            except Exception as user_update_e:
                logger.error(f"Webhook(Invoice Paid): ユーザーステータス更新中にエラー: {user_update_e}")
        else:
             logger.warning(f"Webhook(Invoice Paid): ユーザーが見つからなかったため、ステータス更新はスキップされました: user_id={user_id}")

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
            
        # ユーザーを取得
        user_id = db_subscription.user_id
        db_user = crud_user.get_user(db, user_id=user_id)
        if not db_user:
            logger.error(f"Webhook(Payment Failed): ユーザーが見つかりません: {user_id}")
            # 必要に応じてエラーハンドリング

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
        
        # ユーザーステータスを 'unpaid' に更新
        if db_user:
            user_update_schema = UserUpdate(status=UserStatus.UNPAID)
            try:
                if db_user.status != UserStatus.UNPAID:
                    updated_user = crud_user.update_user(db, db_user=db_user, user_in=user_update_schema)
                    logger.info(f"Webhook(Payment Failed): ユーザーステータスを更新しました: user_id={user_id}, status={updated_user.status}")
                else:
                    logger.info(f"Webhook(Payment Failed): ユーザーステータスは既に '{db_user.status}' です。更新はスキップされました: user_id={user_id}")
            except Exception as user_update_e:
                logger.error(f"Webhook(Payment Failed): ユーザーステータス更新中にエラー: {user_update_e}")
        else:
             logger.warning(f"Webhook(Payment Failed): ユーザーが見つからなかったため、ステータス更新はスキップされました: user_id={user_id}")

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
            
        # ユーザーを取得
        user_id = db_subscription.user_id
        db_user = crud_user.get_user(db, user_id=user_id)
        if not db_user:
            logger.error(f"Webhook(Subscription Deleted): ユーザーが見つかりません: {user_id}")
            # 必要に応じてエラーハンドリング

        # サブスクリプションステータスを更新
        update_data = {
            "status": "canceled",
            "canceled_at": event_data.get("canceled_at", datetime.utcnow()),
            "is_active": False
        }
        
        crud.update_subscription(db, db_subscription.id, update_data)
        logger.info(f"サブスクリプションが削除されました: {db_subscription.id}")
        
        # ユーザーステータスを 'inactive' に更新
        if db_user:
            user_update_schema = UserUpdate(status=UserStatus.INACTIVE)
            try:
                if db_user.status != UserStatus.INACTIVE:
                    updated_user = crud_user.update_user(db, db_user=db_user, user_in=user_update_schema)
                    logger.info(f"Webhook(Subscription Deleted): ユーザーステータスを更新しました: user_id={user_id}, status={updated_user.status}")
                else:
                     logger.info(f"Webhook(Subscription Deleted): ユーザーステータスは既に '{db_user.status}' です。更新はスキップされました: user_id={user_id}")
            except Exception as user_update_e:
                logger.error(f"Webhook(Subscription Deleted): ユーザーステータス更新中にエラー: {user_update_e}")
        else:
             logger.warning(f"Webhook(Subscription Deleted): ユーザーが見つからなかったため、ステータス更新はスキップされました: user_id={user_id}")

    except Exception as e:
        logger.error(f"サブスクリプション削除処理エラー: {str(e)}")

# キャンペーンコード管理エンドポイント
@router.get("/campaign-codes", response_model=List[CampaignCodeResponse])
async def get_campaign_codes(
    skip: int = 0,
    limit: int = 20,
    owner_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission('admin_access', 'campaign_code_read'))
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
    current_user: User = Depends(require_permission('admin_access', 'campaign_code_write'))
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
    current_user: User = Depends(require_permission('admin_access', 'campaign_code_read'))
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
    current_user: User = Depends(require_permission('admin_access', 'campaign_code_write'))
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
    current_user: User = Depends(require_permission('admin_access', 'campaign_code_write'))
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