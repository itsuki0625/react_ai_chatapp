import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.notification_setting import NotificationSetting
from app.models.user import User
from app.models.enums import NotificationType
from app.services.email import send_notification_email
from app.core.config import settings
from app.services.push_service import PushService
from app.models.in_app_notification import InAppNotification
from sqlalchemy.orm import Session
from app.models.push_subscription import PushSubscription
from app.schemas.notification import NotificationCreate

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    async def send_notification(
        db: AsyncSession,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        ユーザーに通知を送信する
        
        Args:
            db: データベースセッション
            user_id: 通知を受け取るユーザーのID
            notification_type: 通知の種類
            title: 通知のタイトル
            message: 通知のメッセージ
            metadata: 通知に関連する追加データ
            
        Returns:
            bool: 通知の送信が成功したかどうか
        """
        try:
            # ユーザーの通知設定を取得
            stmt = select(NotificationSetting).filter(
                NotificationSetting.user_id == user_id,
                NotificationSetting.notification_type == notification_type
            )
            result = await db.execute(stmt)
            notification_setting = result.scalars().first()
            
            if not notification_setting:
                logger.warning(f"ユーザー {user_id} の通知設定が見つかりません")
                return False
            
            # 静かな時間帯のチェック
            current_time = datetime.now().time()
            if notification_setting.quiet_hours_start and notification_setting.quiet_hours_end:
                if notification_setting.quiet_hours_start <= current_time <= notification_setting.quiet_hours_end:
                    logger.info(f"ユーザー {user_id} の静かな時間帯のため、通知を送信しません")
                    return False
            
            # メール通知の送信
            if notification_setting.email_enabled:
                user = await db.get(User, user_id)
                if user:
                    send_notification_email(
                        email=user.email,
                        name=user.full_name,
                        subject=title,
                        message=message
                    )
            
            # プッシュ通知の送信
            if notification_setting.push_enabled:
                stmt = select(PushSubscription).filter(
                    PushSubscription.user_id == user_id
                )
                result = await db.execute(stmt)
                subscriptions = result.scalars().all()
                
                for subscription in subscriptions:
                    await PushService.send_push_notification(
                        subscription=subscription,
                        title=title,
                        message=message,
                        data=metadata
                    )
            
            # アプリ内通知の保存
            if notification_setting.in_app_enabled:
                db_notification = InAppNotification(
                    user_id=user_id,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    metadata=metadata
                )
                db.add(db_notification)
                await db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"通知送信エラー: {str(e)}")
            return False
    
    @staticmethod
    async def send_bulk_notification(
        db: AsyncSession,
        user_ids: List[str],
        notification_type: NotificationType,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        複数のユーザーに一括で通知を送信する
        
        Args:
            db: データベースセッション
            user_ids: 通知を受け取るユーザーIDのリスト
            notification_type: 通知の種類
            title: 通知のタイトル
            message: 通知のメッセージ
            metadata: 通知に関連する追加データ
            
        Returns:
            Dict[str, bool]: ユーザーIDをキーとし、送信結果（成功/失敗）を値とする辞書
        """
        results = {}
        for user_id in user_ids:
            success = await NotificationService.send_notification(
                db=db,
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                metadata=metadata
            )
            results[user_id] = success
        return results 