import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database.database import get_async_db
from app.models.subscription import PaymentHistory
from app.models.user import User
from app.crud import user as crud_user
from app.services.email_service import email_service

logger = logging.getLogger(__name__)

async def send_3ds_reminder_for_pending_payments():
    """
    24時間以上認証待ちの3Dセキュア決済にリマインダーメールを送信
    """
    async for db in get_async_db():
        try:
            # 24時間前の時刻を計算
            threshold_time = datetime.utcnow() - timedelta(hours=24)
            
            # 24時間以上前に作成されたrequires_actionステータスの決済を取得
            result = await db.execute(
                select(PaymentHistory, User.email, User.display_name)
                .join(User, PaymentHistory.user_id == User.id)
                .where(
                    and_(
                        PaymentHistory.status == 'requires_action',
                        PaymentHistory.payment_date <= threshold_time,
                        PaymentHistory.created_at <= threshold_time
                    )
                )
            )
            
            pending_payments = result.fetchall()
            
            if not pending_payments:
                logger.info("24時間以上認証待ちの決済は見つかりませんでした")
                return
            
            logger.info(f"{len(pending_payments)}件の認証待ち決済にリマインダーを送信します")
            
            # 各決済にリマインダーメールを送信
            for payment_history, user_email, user_display_name in pending_payments:
                try:
                    user_name = user_display_name or user_email.split('@')[0]
                    
                    await email_service.send_3ds_reminder_notification(
                        user_email=user_email,
                        user_name=user_name,
                        amount=payment_history.amount,
                        currency=payment_history.currency,
                        payment_intent_id=payment_history.stripe_payment_intent_id
                    )
                    
                    logger.info(f"3DSリマインダー送信完了: {user_email} (PaymentIntent: {payment_history.stripe_payment_intent_id})")
                    
                    # リマインダー送信後、ステータスを更新（オプション：重複送信防止）
                    # payment_history.reminder_sent = True
                    # await db.commit()
                    
                except Exception as e_individual:
                    logger.error(f"個別リマインダー送信失敗: {user_email} - {e_individual}", exc_info=True)
                    continue
            
            logger.info(f"3DSリマインダーバッチ処理完了: {len(pending_payments)}件処理")
            
        except Exception as e:
            logger.error(f"3DSリマインダーバッチ処理中にエラー: {e}", exc_info=True)
        finally:
            await db.close()

async def send_admin_payment_alerts_if_needed():
    """
    決済統計をチェックして、必要であれば管理者にアラートを送信
    """
    async for db in get_async_db():
        try:
            from datetime import datetime, timedelta
            from sqlalchemy import func, case
            
            # 過去1時間の統計を取得
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            result = await db.execute(
                select(
                    func.count(PaymentHistory.id).label('total'),
                    func.sum(
                        case(
                            (PaymentHistory.status.in_(['failed', 'canceled']), 1),
                            else_=0
                        )
                    ).label('failed'),
                    func.sum(
                        case(
                            (PaymentHistory.status == 'requires_action', 1),
                            else_=0
                        )
                    ).label('requires_action')
                )
                .where(PaymentHistory.payment_date >= one_hour_ago)
            )
            
            stats = result.fetchone()
            total_payments = stats.total or 0
            failed_payments = stats.failed or 0
            requires_action_count = stats.requires_action or 0
            
            alerts_to_send = []
            
            # 高失敗率アラート
            if total_payments >= 5:
                failure_rate = (failed_payments / total_payments) * 100
                if failure_rate > 20:
                    severity = "high" if failure_rate > 50 else "medium"
                    alerts_to_send.append({
                        "type": "high_failure_rate",
                        "message": f"過去1時間の決済失敗率が{failure_rate:.1f}%と高くなっています",
                        "severity": severity,
                        "stats": {
                            "total_payments": total_payments,
                            "failed_payments": failed_payments,
                            "failure_rate": f"{failure_rate:.1f}%"
                        }
                    })
            
            # 多数の3DS認証待ちアラート
            if requires_action_count > 10:
                alerts_to_send.append({
                    "type": "multiple_3d_secure_pending",
                    "message": f"3Dセキュア認証待ちの決済が{requires_action_count}件あります",
                    "severity": "medium",
                    "stats": {
                        "requires_action_count": requires_action_count,
                        "total_payments": total_payments
                    }
                })
            
            # アラート送信
            for alert in alerts_to_send:
                try:
                    await email_service.send_admin_payment_alert(
                        alert_type=alert["type"],
                        message=alert["message"],
                        severity=alert["severity"],
                        stats=alert["stats"]
                    )
                    logger.info(f"管理者アラート送信完了: {alert['type']}")
                except Exception as e_alert:
                    logger.error(f"管理者アラート送信失敗: {alert['type']} - {e_alert}", exc_info=True)
            
            if not alerts_to_send:
                logger.info("送信すべき管理者アラートはありませんでした")
            
        except Exception as e:
            logger.error(f"管理者アラートチェック中にエラー: {e}", exc_info=True)
        finally:
            await db.close()

# メイン実行関数
async def run_payment_reminder_tasks():
    """
    決済関連の定期タスクを実行
    """
    logger.info("決済リマインダータスク開始")
    
    # 3DSリマインダー送信
    await send_3ds_reminder_for_pending_payments()
    
    # 管理者アラート送信
    await send_admin_payment_alerts_if_needed()
    
    logger.info("決済リマインダータスク完了")

if __name__ == "__main__":
    asyncio.run(run_payment_reminder_tasks()) 