import stripe
from app.core.config import settings
from app.schemas.subscription import CheckoutSessionResponse
from typing import Optional, Dict, Any, List
from uuid import UUID
import logging
from ..models.user import User
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.subscription import CampaignCode
from datetime import datetime, timezone

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
        duration: str,
        duration_in_months: Optional[int] = None,
        currency: Optional[str] = None,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        amount_off: Optional[int] = None,
        percent_off: Optional[float] = None,
        max_redemptions: Optional[int] = None,
        redeem_by: Optional[int] = None,
        applies_to: Optional[Dict[str, List[str]]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Stripeクーポンを作成する (エンドポイントのスキーマに合わせて修正)
        """
        try:
            coupon_params = {
                'duration': duration,
            }
            
            # 割引タイプに基づいてパラメータを設定 (amount_off と percent_off を直接使用)
            if percent_off is not None:
                if not 0 < percent_off <= 100:
                    raise ValueError("Percentage discount must be between 0 and 100.")
                coupon_params['percent_off'] = percent_off
            elif amount_off is not None:
                if amount_off <= 0:
                     raise ValueError("Fixed amount discount must be positive.")
                if not currency:
                    raise ValueError("Currency is required when amount_off is set.")
                coupon_params['amount_off'] = amount_off # JPYは円単位の整数
                coupon_params['currency'] = currency.lower()
            else:
                 raise ValueError("Either percent_off or amount_off must be provided.")

            # リピート期間を設定（durationが'repeating'の場合のみ必要）
            if duration == 'repeating':
                 if not duration_in_months:
                     raise ValueError("duration_in_months is required when duration is repeating.")
                 coupon_params['duration_in_months'] = duration_in_months
            elif duration_in_months is not None:
                # duration が repeating でない場合は duration_in_months を無視するかエラーにする
                logger.warning("duration_in_months provided but duration is not 'repeating'. Ignoring.")
                # または raise ValueError("duration_in_months can only be set when duration is repeating.")

            # 名前があれば設定
            if name:
                coupon_params['name'] = name
                
            # メタデータがあれば設定
            if metadata:
                coupon_params['metadata'] = metadata

            # 最大利用回数があれば設定
            if max_redemptions is not None:
                 if max_redemptions <= 0:
                      raise ValueError("max_redemptions must be positive.")
                 coupon_params['max_redemptions'] = max_redemptions
            
            # 有効期限があれば設定
            if redeem_by is not None:
                 coupon_params['redeem_by'] = redeem_by
                 
            # 適用対象商品があれば設定
            if applies_to is not None:
                coupon_params['applies_to'] = applies_to

            # kwargs を追加
            coupon_params.update(kwargs)
                
            logger.info(f"Stripe Coupon 作成実行パラメータ: {coupon_params}")
            coupon = stripe.Coupon.create(**coupon_params)
            logger.info(f"Stripe Coupon 作成成功: {coupon.id}")
            return coupon
        except ValueError as ve: # 設定値のバリデーションエラー
            logger.error(f"Stripe Coupon 作成パラメータエラー: {ve}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(ve)
            )
        except stripe.error.StripeError as e: # Stripe APIエラー
            logger.error(f"Stripe Coupon 作成 API エラー: {e.user_message or e}")
            raise HTTPException(
                status_code=e.http_status or status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=e.user_message or "Stripe API Error during coupon creation"
            )
        except Exception as e: # その他の予期せぬエラー
            logger.exception(f"Stripe Coupon 作成中に予期せぬエラー: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected error during coupon creation"
            )

    @staticmethod
    def create_promotion_code(
        coupon_id: str,
        code: Optional[str] = None,
        max_redemptions: Optional[int] = None,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[stripe.PromotionCode]:
        """
        Stripe Promotion Codeを作成する。
        """
        try:
            promotion_params = {
                'coupon': coupon_id,
            }
            if code:
                promotion_params['code'] = code
            if max_redemptions is not None and max_redemptions > 0:
                promotion_params['max_redemptions'] = max_redemptions
            if expires_at:
                 # naive datetime を aware UTC に変換してUnixタイムスタンプにする
                aware_expires_at = expires_at.replace(tzinfo=timezone.utc)
                promotion_params['expires_at'] = int(aware_expires_at.timestamp())
            if metadata:
                promotion_params['metadata'] = metadata

            logger.info(f"Stripe Promotion Code 作成パラメータ: {promotion_params}")
            promotion_code = stripe.PromotionCode.create(**promotion_params)
            logger.info(f"Stripe Promotion Code 作成成功: {promotion_code.id} (Coupon: {coupon_id}, Code: {promotion_code.code})")
            return promotion_code

        except stripe.error.StripeError as e:
            logger.error(f"Stripe Promotion Code 作成失敗 (Coupon: {coupon_id}, Code Attempt: {code}): {e}", exc_info=True)
            # コード重複エラー (resource_already_exists) のハンドリング
            if isinstance(e, stripe.error.InvalidRequestError) and e.code == 'resource_already_exists':
                 raise HTTPException(
                     status_code=status.HTTP_409_CONFLICT,
                     detail=f"Promotion Code '{code}' は既に存在します。"
                 )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Stripe Promotion Codeの作成に失敗しました: {e}"
            )
        except Exception as e:
            logger.error(f"Stripe Promotion Code 作成中に予期せぬエラー (Coupon: {coupon_id}, Code Attempt: {code}): {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Stripe Promotion Code作成中に予期せぬエラーが発生しました。"
            )

    @staticmethod
    def archive_promotion_code(promotion_code_id: str) -> Optional[stripe.PromotionCode]:
        """
        指定されたStripe Promotion Codeを無効化（active=Falseに更新）する。
        """
        try:
            promotion_code = stripe.PromotionCode.modify(promotion_code_id, active=False)
            logger.info(f"Stripe Promotion Code {promotion_code_id} (Code: {promotion_code.code}) を無効化しました。")
            return promotion_code
        except stripe.error.InvalidRequestError as e:
            if "No such promotion_code" in str(e):
                logger.warning(f"無効化しようとしたStripe Promotion Code {promotion_code_id} が見つかりません。")
                return None
            logger.error(f"Stripe Promotion Code ({promotion_code_id}) の無効化中にAPIエラー: {e}", exc_info=True)
            # 必要に応じてエラーを raise する
            # raise HTTPException(...)
            return None
        except Exception as e:
            logger.error(f"Stripe Promotion Code ({promotion_code_id}) の無効化中に予期せぬエラー: {e}", exc_info=True)
            # raise HTTPException(...)
            return None

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
            # --- Log received metadata ---
            logger.debug(f"Received metadata for product {product_id}: {metadata}")
            if metadata is not None: # If metadata is an empty dict {}, it will be sent to Stripe to clear existing metadata.
                params['metadata'] = metadata
            # --- End log ---

            if not params:
                 logger.warning(f"Stripe Product ({product_id}) の更新パラメータが指定されていません。")
                 # 更新するものがない場合はそのまま商品情報を返す
                 return StripeService.get_product(product_id)

            # --- Log parameters being sent to Stripe ---
            logger.debug(f"Calling stripe.Product.modify for {product_id} with params: {params}")
            # --- End log ---

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

    @staticmethod
    def create_stripe_coupon(
        campaign_code_db: CampaignCode, # DBに保存するCampaignCodeオブジェクトを受け取る
        discount_type_db: Any # 関連するDiscountTypeオブジェクトも受け取る  <- DiscountTypeをAnyに変更
    ) -> Optional[stripe.Coupon]:
        """
        データベースのキャンペーンコード情報に基づいてStripe Couponを作成する。
        """
        try:
            coupon_params = {
                "name": f"{campaign_code_db.code} ({campaign_code_db.description or ''})"[:40], # descriptionがNoneの場合も考慮
                "duration": "once", # 多くのキャンペーンコードは一度きりの適用
                "metadata": {
                    "campaign_code_id": str(campaign_code_db.id),
                    "campaign_code": campaign_code_db.code
                }
            }


            # 有効期限 (redeem_by) を設定 (StripeはUnixタイムスタンプ)
            if campaign_code_db.valid_until:
                 # naive datetime を aware UTC に変換
                aware_valid_until = campaign_code_db.valid_until.replace(tzinfo=timezone.utc)
                coupon_params["redeem_by"] = int(aware_valid_until.timestamp())

            # 最大利用回数 (max_redemptions) を設定
            if campaign_code_db.max_uses is not None and campaign_code_db.max_uses > 0:
                coupon_params["max_redemptions"] = campaign_code_db.max_uses

            logger.info(f"Stripe Coupon 作成パラメータ: {coupon_params}")
            coupon = stripe.Coupon.create(**coupon_params)
            logger.info(f"Stripe Coupon 作成成功: {coupon.id} for CampaignCode: {campaign_code_db.code}")
            return coupon

        except stripe.error.StripeError as e:
            logger.error(f"Stripe Coupon 作成失敗 (Code: {campaign_code_db.code}): {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Stripe Couponの作成に失敗しました: {e}"
            )
        except ValueError as ve:
            logger.error(f"Stripe Coupon 作成パラメータエラー (Code: {campaign_code_db.code}): {ve}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"キャンペーンコードのパラメータが不正です: {ve}"
            )
        except Exception as e:
            logger.error(f"Stripe Coupon 作成中に予期せぬエラー (Code: {campaign_code_db.code}): {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Stripe Coupon作成中に予期せぬエラーが発生しました。"
            )

    @staticmethod
    def archive_stripe_coupon(coupon_id: str) -> Optional[stripe.Coupon]:
        """
        指定されたStripe Couponを無効化（アーカイブ）する。
        """
        try:
            coupon = stripe.Coupon.modify(coupon_id, active=False)
            logger.info(f"Stripe Coupon {coupon_id} を無効化しました。")
            # Stripe API v2022-08-01 以降、modify で active=False は非推奨。
            # delete を使うのが一般的だが、Coupon オブジェクトの削除はできない。
            # 代わりに、update で metadata や name を変更して「無効」を示すか、
            # Promotion Code を使っている場合はそれを無効化する。
            # ここでは modify(active=False) を残すが、将来的に見直しが必要になる可能性あり。
            # または、単にログを残すだけにする。
            # coupon = stripe.Coupon.delete(coupon_id) # これはエラーになる
            return coupon
        except stripe.error.InvalidRequestError as e:
             if "No such coupon" in str(e):
                 logger.warning(f"無効化しようとしたStripe Coupon {coupon_id} が見つかりません。")
                 return None # 見つからない場合はNoneを返す
             logger.error(f"Stripe Coupon ({coupon_id}) の無効化中にAPIエラー: {e}", exc_info=True)
             # エラーを無視して処理を続けるか、例外を発生させるか選択
             # raise HTTPException(...) # 必要なら例外を発生
             return None # ここではNoneを返す
        except Exception as e:
             logger.error(f"Stripe Coupon ({coupon_id}) の無効化中に予期せぬエラー: {e}", exc_info=True)
             # raise HTTPException(...) # 必要なら例外を発生
             return None # ここではNoneを返す 

    @staticmethod
    def list_coupons(
        limit: int = 10,
        created: Optional[Dict[str, int]] = None,
        starting_after: Optional[str] = None,
        ending_before: Optional[str] = None,
        **kwargs: Any # 他のStripeパラメータを許容する場合
    ) -> List[Dict[str, Any]]:
        """Stripe Coupon のリストを取得する"""
        try:
            list_params = {
                'limit': limit,
                'expand': ['data.applies_to'] # applies_to フィールドを展開して商品情報を取得
            }
            if created:
                list_params['created'] = created
            if starting_after:
                list_params['starting_after'] = starting_after
            if ending_before:
                list_params['ending_before'] = ending_before
            
            # kwargs を追加して他のフィルタリングオプションをサポート
            list_params.update(kwargs)

            coupons = stripe.Coupon.list(**list_params)
            logger.info(f"Stripe Coupon リスト取得成功: {len(coupons.data)} 件")
            return coupons.data
        except stripe.error.StripeError as e:
            logger.error(f"Stripe Coupon リスト取得 API エラー: {e.user_message}")
            raise # エンドポイント側でHTTPExceptionに変換するため、ここではStripeErrorを再raise
        except Exception as e:
            logger.exception(f"Stripe Coupon リスト取得中に予期せぬエラー: {e}")
            raise # 同様にエンドポイント側で処理

    @staticmethod
    def retrieve_coupon(coupon_id: str) -> Dict[str, Any]:
        """
        指定されたIDのStripe Couponを取得する
        """
        try:
            coupon = stripe.Coupon.retrieve(coupon_id, expand=['applies_to'])
            logger.info(f"Stripe Coupon 取得成功: {coupon.id}")
            return coupon
        except stripe.error.InvalidRequestError as e:
            if "No such coupon" in str(e):
                 logger.warning(f"Stripe Coupon {coupon_id} が見つかりません。")
                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Coupon {coupon_id} not found")
            logger.error(f"Stripe Coupon ({coupon_id}) 取得 API エラー: {e.user_message}")
            raise HTTPException(status_code=e.http_status or status.HTTP_400_BAD_REQUEST, detail=e.user_message or "Stripe API Error")
        except stripe.error.StripeError as e:
            logger.error(f"Stripe Coupon ({coupon_id}) 取得 API エラー: {e.user_message}")
            raise HTTPException(status_code=e.http_status or status.HTTP_400_BAD_REQUEST, detail=e.user_message or "Stripe API Error")
        except Exception as e:
            logger.exception(f"Stripe Coupon ({coupon_id}) 取得中に予期せぬエラー: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during coupon retrieval")

    @staticmethod
    def update_coupon(
        coupon_id: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        **kwargs: Any # 他の更新可能パラメータを許容する場合
    ) -> Dict[str, Any]:
        """Stripe Coupon を更新する (主に name と metadata)"""
        try:
            update_params = {}
            if name is not None:
                update_params['name'] = name
            if metadata is not None:
                update_params['metadata'] = metadata
            
            # kwargs を追加して他の更新をサポート (注意: Stripeが許可するフィールドのみ)
            update_params.update(kwargs)

            if not update_params:
                logger.warning(f"Stripe Coupon ({coupon_id}) の更新パラメータが指定されていません。")
                # 更新するものがない場合はそのままクーポン情報を返す (retrieve を呼ぶ)
                return StripeService.retrieve_coupon(coupon_id)

            updated_coupon = stripe.Coupon.modify(coupon_id, **update_params)
            logger.info(f"Stripe Coupon 更新成功: {updated_coupon.id}")
            return updated_coupon
        except stripe.error.InvalidRequestError as e:
            if "No such coupon" in str(e):
                 logger.warning(f"更新しようとした Stripe Coupon {coupon_id} が見つかりません。")
                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Coupon {coupon_id} not found")
            logger.error(f"Stripe Coupon ({coupon_id}) 更新 API エラー: {e.user_message}")
            raise HTTPException(status_code=e.http_status or status.HTTP_400_BAD_REQUEST, detail=e.user_message or "Stripe API Error")
        except stripe.error.StripeError as e:
            logger.error(f"Stripe Coupon ({coupon_id}) 更新 API エラー: {e.user_message}")
            raise HTTPException(status_code=e.http_status or status.HTTP_400_BAD_REQUEST, detail=e.user_message or "Stripe API Error")
        except Exception as e:
            logger.exception(f"Stripe Coupon ({coupon_id}) 更新中に予期せぬエラー: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during coupon update")

    @staticmethod
    def delete_coupon(coupon_id: str) -> None:
        """Stripe Coupon を削除する"""
        try:
            stripe.Coupon.delete(coupon_id)
            logger.info(f"Stripe Coupon 削除成功: {coupon_id}")
            # 成功時は何も返さない (void)
        except stripe.error.InvalidRequestError as e:
            # 削除しようとしたクーポンが存在しない場合
            if "No such coupon" in str(e):
                 logger.warning(f"削除しようとしたStripe Coupon {coupon_id} が見つかりません。")
                 # すでに存在しない場合は成功とみなすか、エラーにするかは要件による
                 # ここでは Not Found を raise する
                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Coupon {coupon_id} not found")
            # クーポンが現在サブスクリプションなどで利用中の場合など、削除できないケース
            # Stripe API のエラーメッセージに基づいて詳細なハンドリングが可能
            logger.error(f"Stripe Coupon ({coupon_id}) 削除 API エラー: {e.user_message}")
            raise HTTPException(status_code=e.http_status or status.HTTP_400_BAD_REQUEST, detail=e.user_message or "Stripe API Error")
        except stripe.error.StripeError as e:
            logger.error(f"Stripe Coupon ({coupon_id}) 削除 API エラー: {e.user_message}")
            raise HTTPException(status_code=e.http_status or status.HTTP_400_BAD_REQUEST, detail=e.user_message or "Stripe API Error")
        except Exception as e:
            logger.exception(f"Stripe Coupon ({coupon_id}) 削除中に予期せぬエラー: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during coupon deletion") 