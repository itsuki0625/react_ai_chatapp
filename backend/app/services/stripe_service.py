import stripe
from app.core.config import settings
from app.schemas.subscription import CheckoutSessionResponse
from typing import Optional, Dict, Any, List
from uuid import UUID
import logging
from ..models.user import User
from sqlalchemy.orm import Session
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Stripe APIキーの設定
stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    @staticmethod
    def create_customer(email: str, name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Stripeカスタマーを作成する
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata
            )
            return customer.id
        except Exception as e:
            logger.error(f"Stripeカスタマー作成エラー: {str(e)}")
            raise

    @staticmethod
    def create_checkout_session(
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None,
        discounts: Optional[list] = None
    ) -> CheckoutSessionResponse:
        """
        決済用のチェックアウトセッションを作成する
        割引情報も含める場合は discounts パラメータを使用
        """
        try:
            session_params = {
                'payment_method_types': ['card'],
                'line_items': [{
                    'price': price_id,
                    'quantity': 1,
                }],
                'mode': 'subscription',
                'success_url': success_url,
                'cancel_url': cancel_url,
                'customer': customer_id,
            }
            
            # メタデータがあれば追加
            if metadata:
                session_params['metadata'] = metadata
                
            # 割引があれば追加
            if discounts:
                session_params['discounts'] = discounts
            
            session = stripe.checkout.Session.create(**session_params)
            
            return CheckoutSessionResponse(
                session_id=session.id,
                url=session.url
            )
        except Exception as e:
            logger.error(f"チェックアウトセッション作成エラー: {str(e)}")
            raise

    @staticmethod
    def list_prices(
        product_id: Optional[str] = None,
        active: bool = True, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Stripeから価格リストを取得する
        product_id を指定すると、その商品に関連する価格のみを取得
        """
        try:
            list_params = {
                'active': active,
                'limit': limit,
                'expand': ['data.product']
            }
            if product_id:
                list_params['product'] = product_id
            
            prices = stripe.Price.list(**list_params)
            return prices.data
        except Exception as e:
            logger.error(f"価格一覧取得エラー: {str(e)}")
            raise

    @staticmethod
    def get_product(product_id: str) -> Dict[str, Any]:
        """
        Stripeから商品情報を取得する
        """
        try:
            # 型チェック: product_idが文字列ではない場合の対応
            if not isinstance(product_id, str):
                if hasattr(product_id, 'id'):
                    # オブジェクトからIDを取得
                    product_id = product_id.id
                elif isinstance(product_id, dict) and 'id' in product_id:
                    # 辞書からIDを取得
                    product_id = product_id['id']
                else:
                    # 対応できない型の場合はエラー
                    raise ValueError(f"product_idは文字列である必要があります。受け取った型: {type(product_id)}")
            
            product = stripe.Product.retrieve(product_id)
            return product
        except Exception as e:
            logger.error(f"商品情報取得エラー: {str(e)}")
            raise

    @staticmethod
    def create_coupon(
        discount_type: str,  # 'percentage' or 'amount_off'
        discount_value: float,
        duration: str = 'once',  # 'once', 'forever', 'repeating'
        duration_in_months: Optional[int] = None,
        currency: str = 'jpy',
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Stripeクーポンを作成する
        """
        try:
            coupon_params = {
                'duration': duration,
            }
            
            # 割引タイプに基づいてパラメータを設定
            if discount_type == 'percentage':
                coupon_params['percent_off'] = discount_value
            elif discount_type == 'fixed':
                coupon_params['amount_off'] = int(discount_value)
                coupon_params['currency'] = currency
            else:
                raise ValueError("discount_typeは 'percentage' または 'fixed' である必要があります")
                
            # リピート期間を設定（durationが'repeating'の場合のみ必要）
            if duration == 'repeating' and duration_in_months:
                coupon_params['duration_in_months'] = duration_in_months
                
            # 名前があれば設定
            if name:
                coupon_params['name'] = name
                
            # メタデータがあれば設定
            if metadata:
                coupon_params['metadata'] = metadata
                
            coupon = stripe.Coupon.create(**coupon_params)
            return coupon
        except Exception as e:
            logger.error(f"クーポン作成エラー: {str(e)}")
            raise

    @staticmethod
    def create_promotion_code(
        coupon_id: str,
        code: Optional[str] = None,
        max_redemptions: Optional[int] = None,
        expires_at: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Stripeプロモーションコードを作成する
        """
        try:
            promotion_params = {
                'coupon': coupon_id,
            }
            
            # コードが指定されていれば使用
            if code:
                promotion_params['code'] = code
                
            # 最大利用回数が指定されていれば使用
            if max_redemptions:
                promotion_params['max_redemptions'] = max_redemptions
                
            # 有効期限が指定されていれば使用
            if expires_at:
                promotion_params['expires_at'] = expires_at
                
            # メタデータがあれば使用
            if metadata:
                promotion_params['metadata'] = metadata
                
            promotion_code = stripe.PromotionCode.create(**promotion_params)
            return promotion_code
        except Exception as e:
            logger.error(f"プロモーションコード作成エラー: {str(e)}")
            raise

    @staticmethod
    def retrieve_promotion_code(promotion_code: str) -> Dict[str, Any]:
        """
        プロモーションコードを取得する
        """
        try:
            return stripe.PromotionCode.retrieve(promotion_code)
        except Exception as e:
            logger.error(f"プロモーションコード取得エラー: {str(e)}")
            raise

    @staticmethod
    def retrieve_coupon(coupon_id: str) -> Dict[str, Any]:
        """
        クーポンを取得する
        """
        try:
            return stripe.Coupon.retrieve(coupon_id)
        except Exception as e:
            logger.error(f"クーポン取得エラー: {str(e)}")
            raise

    @staticmethod
    def create_portal_session(customer_id: str, return_url: str) -> str:
        """
        顧客ポータルセッションを作成する
        """
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            return session.url
        except Exception as e:
            logger.error(f"ポータルセッション作成エラー: {str(e)}")
            raise

    @staticmethod
    def cancel_subscription(subscription_id: str, cancel_at_period_end: bool = True) -> Dict[str, Any]:
        """
        サブスクリプションをキャンセルする
        """
        try:
            if cancel_at_period_end:
                # 期間終了時にキャンセル
                result = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                # 即時キャンセル
                result = stripe.Subscription.delete(subscription_id)
            
            return result
        except Exception as e:
            logger.error(f"サブスクリプションキャンセルエラー: {str(e)}")
            raise

    @staticmethod
    def reactivate_subscription(subscription_id: str) -> Dict[str, Any]:
        """
        キャンセル予定のサブスクリプションを再開する
        """
        try:
            result = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            return result
        except Exception as e:
            logger.error(f"サブスクリプション再開エラー: {str(e)}")
            raise

    @staticmethod
    def update_subscription(subscription_id: str, price_id: str) -> Dict[str, Any]:
        """
        サブスクリプションのプランを変更する
        """
        try:
            # 現在のサブスクリプションアイテムを取得
            subscription = stripe.Subscription.retrieve(subscription_id)
            subscription_item_id = subscription['items']['data'][0]['id']
            
            # 新しいプランに更新
            updated_subscription = stripe.Subscription.modify(
                subscription_id,
                items=[{
                    'id': subscription_item_id,
                    'price': price_id,
                }]
            )
            return updated_subscription
        except Exception as e:
            logger.error(f"サブスクリプション更新エラー: {str(e)}")
            raise

    @staticmethod
    def verify_webhook_signature(payload: str, sig_header: str) -> Dict[str, Any]:
        """
        Webhookのシグネチャを検証する
        """
        try:
            # ペイロードをイベントに変換
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig_header,
                secret=settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook署名検証エラー: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Webhookイベント処理エラー: {str(e)}")
            raise

    @staticmethod
    def get_subscription(subscription_id: str) -> Dict[str, Any]:
        """
        サブスクリプション情報を取得する
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return subscription
        except Exception as e:
            logger.error(f"サブスクリプション取得エラー: {str(e)}")
            raise
            
    @staticmethod
    def get_price(price_id: str) -> Dict[str, Any]:
        """
        価格情報を取得する
        """
        try:
            price = stripe.Price.retrieve(price_id)
            return price
        except Exception as e:
            logger.error(f"価格情報取得エラー: {str(e)}")
            raise
            
    @staticmethod
    def get_payment_method(payment_method_id: str) -> Dict[str, Any]:
        """
        支払い方法を取得する
        """
        try:
            return stripe.PaymentMethod.retrieve(payment_method_id)
        except Exception as e:
            logger.error(f"支払い方法取得エラー: {str(e)}")
            raise

    @staticmethod
    def create_product(
        name: str,
        description: Optional[str] = None,
        active: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Stripe 商品 (Product) を作成する"""
        try:
            product = stripe.Product.create(
                name=name,
                description=description,
                active=active,
                metadata=metadata
            )
            logger.info(f"Stripe Product 作成成功: {product.id}")
            return product
        except Exception as e:
            logger.error(f"Stripe Product 作成エラー: {str(e)}")
            raise

    @staticmethod
    def update_product(
        product_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        active: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Stripe 商品 (Product) を更新する"""
        try:
            params = {}
            if name is not None: params['name'] = name
            if description is not None: params['description'] = description
            if active is not None: params['active'] = active
            if metadata is not None: params['metadata'] = metadata

            if not params:
                 logger.warning(f"Stripe Product ({product_id}) の更新パラメータが指定されていません。")
                 # 更新するものがない場合はそのまま商品情報を返す
                 return StripeService.get_product(product_id)

            product = stripe.Product.modify(product_id, **params)
            logger.info(f"Stripe Product 更新成功: {product.id}")
            return product
        except Exception as e:
            logger.error(f"Stripe Product ({product_id}) 更新エラー: {str(e)}")
            raise

    @staticmethod
    def list_products(active: Optional[bool] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Stripe 商品 (Product) のリストを取得する"""
        try:
            params = {'limit': limit}
            if active is not None:
                params['active'] = active
            products = stripe.Product.list(**params)
            logger.info(f"Stripe Product リスト取得: {len(products.data)} 件")
            return products.data
        except Exception as e:
            logger.error(f"Stripe Product リスト取得エラー: {str(e)}")
            raise

    @staticmethod
    def archive_product(product_id: str) -> Dict[str, Any]:
        """Stripe 商品 (Product) をアーカイブする (active=False に設定)"""
        try:
            # アーカイブは active=False の更新と同じ
            product = stripe.Product.modify(product_id, active=False)
            logger.info(f"Stripe Product アーカイブ成功: {product.id}")
            return product
        except Exception as e:
            logger.error(f"Stripe Product ({product_id}) アーカイブエラー: {str(e)}")
            raise

    @staticmethod
    def create_price(
        product_id: str,
        unit_amount: int,
        currency: str,
        recurring: Dict[str, Any], # {'interval': 'month', 'interval_count': 1}
        active: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
        lookup_key: Optional[str] = None # 必要であればルックアップキーも設定
    ) -> Dict[str, Any]:
        """Stripe 価格 (Price) を作成する"""
        try:
            price_params = {
                'unit_amount': unit_amount,
                'currency': currency,
                'recurring': recurring,
                'product': product_id,
                'active': active,
            }
            if metadata:
                price_params['metadata'] = metadata
            if lookup_key:
                price_params['lookup_key'] = lookup_key

            price = stripe.Price.create(**price_params)
            logger.info(f"Stripe Price 作成成功: {price.id} (Product: {product_id})" )
            return price
        except Exception as e:
            logger.error(f"Stripe Price 作成エラー (Product: {product_id}): {str(e)}")
            raise

    @staticmethod
    def update_price(
        price_id: str,
        active: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
        lookup_key: Optional[str] = None # ルックアップキーの更新も可能
    ) -> Dict[str, Any]:
        """Stripe 価格 (Price) を更新する (active, metadata, lookup_key のみ更新可能)"""
        try:
            params = {}
            if active is not None: params['active'] = active
            if metadata is not None: params['metadata'] = metadata
            if lookup_key is not None: params['lookup_key'] = lookup_key

            if not params:
                logger.warning(f"Stripe Price ({price_id}) の更新パラメータが指定されていません。")
                return StripeService.get_price(price_id)

            price = stripe.Price.modify(price_id, **params)
            logger.info(f"Stripe Price 更新成功: {price.id}")
            return price
        except Exception as e:
            logger.error(f"Stripe Price ({price_id}) 更新エラー: {str(e)}")
            raise 