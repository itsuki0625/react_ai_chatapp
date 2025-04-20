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
    Stripeチェックアウトセッションを作成する
    """
    try:
        # price_idの検証（必須）
        if not request.price_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="価格IDは必須です"
            )
            
        stripe_price_id = request.price_id
        
        # Stripeから直接価格情報を取得して検証
        try:
            price = StripeService.get_price(stripe_price_id)
            logger.debug(f"取得した価格情報: {price}")
            if not price.get("active", False):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="指定された価格は現在無効です"
                )
        except Exception as e:
            logger.error(f"Stripe価格情報取得エラー: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"指定された価格ID({stripe_price_id})は無効です"
            )
        
        # キャンペーンコードの処理
        coupon_id = None
        if request.campaign_code:
            # キャンペーンコードを検証
            result = crud.verify_campaign_code(db, request.campaign_code, request.price_id)
            
            # キャンペーンコードが有効な場合
            if result.get("valid") and result.get("campaign_code_id"):
                campaign_code_id = result.get("campaign_code_id")
                db_campaign_code = crud.get_campaign_code(db, campaign_code_id)
                
                if db_campaign_code:
                    # Stripe上にクーポンを作成
                    try:
                        coupon_data = {
                            "duration": "once",  # 一回だけ適用
                            "id": f"camp_{db_campaign_code.code}",  # クーポンID
                        }
                        
                        # 割引タイプに応じたパラメータ設定
                        if db_campaign_code.discount_type == "percentage":
                            coupon_data["percent_off"] = db_campaign_code.discount_value
                        else:  # fixed
                            coupon_data["amount_off"] = int(db_campaign_code.discount_value)
                            coupon_data["currency"] = "jpy"
                            
                        # クーポン作成（または既存のものを取得）
                        try:
                            coupon = StripeService.create_coupon(coupon_data)
                            coupon_id = coupon.get("id")
                            logger.info(f"Stripeクーポン作成成功: {coupon_id}")
                        except Exception as e:
                            if "already exists" in str(e):
                                # 既に存在する場合は既存のクーポンを使用
                                coupon_id = coupon_data["id"]
                                logger.info(f"既存のStripeクーポンを使用: {coupon_id}")
                            else:
                                raise
                                
                        # キャンペーンコードの使用回数をインクリメント
                        crud.increment_campaign_code_usage(db, campaign_code_id)
                        
                    except Exception as e:
                        logger.error(f"Stripeクーポン作成エラー: {str(e)}")
                        # クーポンが作成できなくても処理は続行するが、割引は適用されない
            else:
                logger.warning(f"キャンペーンコード '{request.campaign_code}' は無効です: {result.get('message')}")
        
        # 顧客情報の取得または作成
        stripe_customer_id = None
        active_subscription = crud.get_active_user_subscription(db, current_user.id)
        
        if active_subscription and active_subscription.stripe_customer_id:
            # 既存の顧客IDを使用
            stripe_customer_id = active_subscription.stripe_customer_id
            logger.debug(f"既存の顧客IDを使用: {stripe_customer_id}")
        else:
            # 新規顧客を作成
            try:
                customer = StripeService.create_customer({
                    "email": current_user.email,
                    "name": current_user.fullname,
                    "metadata": {
                        "user_id": str(current_user.id)
                    }
                })
                stripe_customer_id = customer.get("id")
                logger.debug(f"新規顧客作成: {stripe_customer_id}")
            except Exception as e:
                logger.error(f"Stripe顧客作成エラー: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="顧客情報の作成中にエラーが発生しました"
                )
        
        # 成功URL確認
        success_url = request.success_url
        if "{CHECKOUT_SESSION_ID}" not in success_url:
            logger.warning("success_urlに{CHECKOUT_SESSION_ID}が含まれていません")
            success_url = f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}"
        
        # チェックアウトセッション作成
        try:
            session_data = {
                "success_url": success_url,
                "cancel_url": request.cancel_url,
                "mode": "subscription",
                "customer": stripe_customer_id,
                "line_items": [
                    {
                        "price": stripe_price_id,
                        "quantity": 1
                    }
                ],
                "metadata": {
                    "user_id": str(current_user.id)
                }
            }
            
            # クーポンがある場合は追加
            if coupon_id:
                session_data["discounts"] = [{"coupon": coupon_id}]
                
            # セッション作成
            session = StripeService.create_checkout_session(session_data)
            
            return CheckoutSessionResponse(
                session_id=session.get("id"),
                url=session.get("url")
            )
        except Exception as e:
            logger.error(f"チェックアウトセッション作成エラー: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="チェックアウトセッションの作成中にエラーが発生しました"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"チェックアウトセッション作成エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="チェックアウトセッションの作成中に予期せぬエラーが発生しました"
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