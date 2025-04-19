import stripe
from app.core.config import settings
from app.schemas.subscription import CheckoutSessionResponse
from typing import Optional, Dict, Any
from uuid import UUID
import logging

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
        支払い方法の詳細を取得する
        """
        try:
            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
            return payment_method
        except Exception as e:
            logger.error(f"支払い方法取得エラー: {str(e)}")
            raise 