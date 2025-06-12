# backend/app/services/email_service.py

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """
    決済関連のメール通知サービス
    """
    
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.executor = ThreadPoolExecutor(max_workers=3)
    
    def _send_email_sync(
        self,
        to_emails: List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """
        同期的にメールを送信する内部メソッド
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            
            # テキスト版とHTML版を追加
            if text_body:
                part1 = MIMEText(text_body, 'plain', 'utf-8')
                msg.attach(part1)
            
            part2 = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(part2)
            
            # SMTP接続してメール送信
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"メール送信成功: {to_emails} - {subject}")
            return True
            
        except Exception as e:
            logger.error(f"メール送信失敗: {to_emails} - {subject}: {e}", exc_info=True)
            return False
    
    async def send_email_async(
        self,
        to_emails: List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """
        非同期でメールを送信
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._send_email_sync,
            to_emails,
            subject,
            html_body,
            text_body
        )
    
    # ---------- 決済成功通知 ----------
    
    async def send_payment_success_notification(
        self,
        user_email: str,
        user_name: str,
        amount: int,
        currency: str,
        payment_intent_id: str,
        subscription_name: Optional[str] = None
    ) -> bool:
        """
        決済成功通知メールを送信
        """
        amount_formatted = f"¥{amount:,}" if currency.upper() == 'JPY' else f"{currency.upper()} {amount/100:,.2f}"
        
        subject = "決済が完了しました - Study Support App"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                .success-badge {{ background: #10B981; color: white; padding: 8px 16px; border-radius: 4px; display: inline-block; }}
                .details {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>決済完了のお知らせ</h1>
                </div>
                <div class="content">
                    <p>こんにちは、{user_name}様</p>
                    
                    <div class="success-badge">✓ 決済が正常に完了しました</div>
                    
                    <div class="details">
                        <h3>決済詳細</h3>
                        <p><strong>金額:</strong> {amount_formatted}</p>
                        {f'<p><strong>プラン:</strong> {subscription_name}</p>' if subscription_name else ''}
                        <p><strong>決済ID:</strong> {payment_intent_id}</p>
                        <p><strong>決済日時:</strong> {datetime.now().strftime('%Y年%m月%d日 %H:%M')}</p>
                    </div>
                    
                    <p>サービスをお楽しみください。ご不明な点がございましたら、お気軽にお問い合わせください。</p>
                </div>
                <div class="footer">
                    <p>Study Support App チーム</p>
                    <p>このメールに返信しないでください。</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        決済完了のお知らせ
        
        こんにちは、{user_name}様
        
        決済が正常に完了しました。
        
        決済詳細:
        - 金額: {amount_formatted}
        {f'- プラン: {subscription_name}' if subscription_name else ''}
        - 決済ID: {payment_intent_id}
        - 決済日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}
        
        サービスをお楽しみください。
        
        Study Support App チーム
        """
        
        return await self.send_email_async([user_email], subject, html_body, text_body)
    
    # ---------- 決済失敗通知 ----------
    
    async def send_payment_failed_notification(
        self,
        user_email: str,
        user_name: str,
        amount: int,
        currency: str,
        payment_intent_id: str,
        failure_reason: Optional[str] = None
    ) -> bool:
        """
        決済失敗通知メールを送信
        """
        amount_formatted = f"¥{amount:,}" if currency.upper() == 'JPY' else f"{currency.upper()} {amount/100:,.2f}"
        
        subject = "決済でエラーが発生しました - Study Support App"
        
        failure_message = failure_reason if failure_reason else "決済処理中にエラーが発生しました"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #EF4444; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                .error-badge {{ background: #EF4444; color: white; padding: 8px 16px; border-radius: 4px; display: inline-block; }}
                .details {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .retry-btn {{ background: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>決済エラーのお知らせ</h1>
                </div>
                <div class="content">
                    <p>こんにちは、{user_name}様</p>
                    
                    <div class="error-badge">⚠ 決済でエラーが発生しました</div>
                    
                    <div class="details">
                        <h3>エラー詳細</h3>
                        <p><strong>金額:</strong> {amount_formatted}</p>
                        <p><strong>エラー内容:</strong> {failure_message}</p>
                        <p><strong>決済ID:</strong> {payment_intent_id}</p>
                        <p><strong>発生日時:</strong> {datetime.now().strftime('%Y年%m月%d日 %H:%M')}</p>
                    </div>
                    
                    <p>申し訳ございませんが、決済が完了できませんでした。以下をご確認ください：</p>
                    <ul>
                        <li>カード情報が正確に入力されているか</li>
                        <li>カードの有効期限が切れていないか</li>
                        <li>カードの利用限度額を超えていないか</li>
                    </ul>
                    
                    <a href="{settings.FRONTEND_URL}/subscription" class="retry-btn">再度お試しください</a>
                    
                    <p>問題が解決しない場合は、お問い合わせフォームからご連絡ください。</p>
                </div>
                <div class="footer">
                    <p>Study Support App チーム</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        決済エラーのお知らせ
        
        こんにちは、{user_name}様
        
        申し訳ございませんが、決済でエラーが発生しました。
        
        エラー詳細:
        - 金額: {amount_formatted}
        - エラー内容: {failure_message}
        - 決済ID: {payment_intent_id}
        - 発生日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}
        
        以下をご確認の上、再度お試しください：
        - カード情報が正確に入力されているか
        - カードの有効期限が切れていないか
        - カードの利用限度額を超えていないか
        
        問題が解決しない場合は、お問い合わせください。
        
        Study Support App チーム
        """
        
        return await self.send_email_async([user_email], subject, html_body, text_body)
    
    # ---------- 3Dセキュア認証リマインダー ----------
    
    async def send_3ds_reminder_notification(
        self,
        user_email: str,
        user_name: str,
        amount: int,
        currency: str,
        payment_intent_id: str
    ) -> bool:
        """
        3Dセキュア認証リマインダーメールを送信
        """
        amount_formatted = f"¥{amount:,}" if currency.upper() == 'JPY' else f"{currency.upper()} {amount/100:,.2f}"
        
        subject = "3Dセキュア認証が必要です - Study Support App"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #F59E0B; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                .warning-badge {{ background: #F59E0B; color: white; padding: 8px 16px; border-radius: 4px; display: inline-block; }}
                .details {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .auth-btn {{ background: #10B981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>認証が必要です</h1>
                </div>
                <div class="content">
                    <p>こんにちは、{user_name}様</p>
                    
                    <div class="warning-badge">🔐 3Dセキュア認証が必要です</div>
                    
                    <div class="details">
                        <h3>認証待ちの決済</h3>
                        <p><strong>金額:</strong> {amount_formatted}</p>
                        <p><strong>決済ID:</strong> {payment_intent_id}</p>
                        <p><strong>認証開始日時:</strong> {datetime.now().strftime('%Y年%m月%d日 %H:%M')}</p>
                    </div>
                    
                    <p>お客様の決済を完了するために、カード会社での3Dセキュア認証が必要です。</p>
                    <p>認証を完了しないと決済がキャンセルされる場合があります。</p>
                    
                    <a href="{settings.FRONTEND_URL}/subscription/payment-status/{payment_intent_id}" class="auth-btn">認証を完了する</a>
                    
                    <p><small>※ 24時間以内に認証を完了してください。</small></p>
                </div>
                <div class="footer">
                    <p>Study Support App チーム</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        3Dセキュア認証が必要です
        
        こんにちは、{user_name}様
        
        お客様の決済を完了するために、カード会社での3Dセキュア認証が必要です。
        
        認証待ちの決済:
        - 金額: {amount_formatted}
        - 決済ID: {payment_intent_id}
        - 認証開始日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}
        
        認証を完了しないと決済がキャンセルされる場合があります。
        24時間以内に認証を完了してください。
        
        認証URL: {settings.FRONTEND_URL}/subscription/payment-status/{payment_intent_id}
        
        Study Support App チーム
        """
        
        return await self.send_email_async([user_email], subject, html_body, text_body)
    
    # ---------- 管理者向けアラート ----------
    
    async def send_admin_payment_alert(
        self,
        alert_type: str,
        message: str,
        severity: str,
        stats: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        管理者向け決済アラートメールを送信
        """
        admin_emails = [settings.ADMIN_EMAIL] if hasattr(settings, 'ADMIN_EMAIL') else []
        if not admin_emails:
            logger.warning("管理者メールアドレスが設定されていません")
            return False
        
        severity_colors = {
            'high': '#EF4444',
            'medium': '#F59E0B',
            'low': '#10B981'
        }
        
        subject = f"[{severity.upper()}] 決済アラート - Study Support App"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: {severity_colors.get(severity, '#6B7280')}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .alert-badge {{ background: {severity_colors.get(severity, '#6B7280')}; color: white; padding: 8px 16px; border-radius: 4px; display: inline-block; }}
                .stats {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>決済システムアラート</h1>
                </div>
                <div class="content">
                    <div class="alert-badge">{severity.upper()} - {alert_type}</div>
                    
                    <h3>アラート内容</h3>
                    <p>{message}</p>
                    
                    {f'''
                    <div class="stats">
                        <h4>統計情報</h4>
                        <ul>
                            {"".join([f"<li><strong>{key}:</strong> {value}</li>" for key, value in stats.items()])}
                        </ul>
                    </div>
                    ''' if stats else ''}
                    
                    <p><strong>発生日時:</strong> {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
                    
                    <p>必要に応じて決済システムの状況を確認してください。</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        決済システムアラート
        
        {severity.upper()} - {alert_type}
        
        アラート内容:
        {message}
        
        {f'''
        統計情報:
        {chr(10).join([f"- {key}: {value}" for key, value in stats.items()])}
        ''' if stats else ''}
        
        発生日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
        
        必要に応じて決済システムの状況を確認してください。
        """
        
        return await self.send_email_async(admin_emails, subject, html_body, text_body)

# シングルトンインスタンス
email_service = EmailService() 