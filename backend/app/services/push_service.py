import json
import logging
from typing import Dict, Any
from pywebpush import webpush, WebPushException
from app.core.config import settings
from app.models.push_subscription import PushSubscription

logger = logging.getLogger(__name__)

class PushService:
    @staticmethod
    async def send_push_notification(
        subscription: PushSubscription,
        title: str,
        message: str,
        data: Dict[str, Any] = None
    ) -> bool:
        """
        プッシュ通知を送信する
        
        Args:
            subscription: プッシュ通知のサブスクリプション
            title: 通知のタイトル
            message: 通知のメッセージ
            data: 追加データ
            
        Returns:
            bool: 送信が成功したかどうか
        """
        try:
            payload = {
                "title": title,
                "message": message,
                "data": data or {}
            }
            
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {
                        "p256dh": subscription.p256dh_key,
                        "auth": subscription.auth_token
                    }
                },
                data=json.dumps(payload),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={
                    "sub": f"mailto:{settings.SMTP_USER}"
                }
            )
            return True
            
        except WebPushException as e:
            logger.error(f"プッシュ通知送信エラー: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"予期せぬエラー: {str(e)}")
            return False 