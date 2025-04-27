import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import logging
from datetime import datetime
from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def send_email(to_email: str, subject: str, html_content: str, plain_content: str = None):
    """
    メール送信の共通処理
    """
    try:
        # 設定からSMTP情報を取得
        smtp_server = settings.SMTP_SERVER
        smtp_port = settings.SMTP_PORT
        smtp_user = settings.SMTP_USER
        smtp_password = settings.SMTP_PASSWORD
        from_email = settings.FROM_EMAIL
        
        # メッセージの作成
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = from_email
        message["To"] = to_email
        
        # プレーンテキスト版（指定がなければHTMLから生成）
        if plain_content is None:
            # 簡易的なHTMLからテキスト変換（実際のプロジェクトではより洗練された方法を使用すべき）
            plain_content = html_content.replace("<br>", "\n").replace("<p>", "").replace("</p>", "\n\n")
        
        # テキストパートとHTMLパートを追加
        text_part = MIMEText(plain_content, "plain", "utf-8")
        html_part = MIMEText(html_content, "html", "utf-8")
        message.attach(text_part)
        message.attach(html_part)
        
        # 開発環境ではメール送信をログに記録するだけ
        if settings.ENVIRONMENT == "development":
            logger.info(f"[DEV MODE] メール送信 - 宛先: {to_email}, 件名: {subject}")
            logger.info(f"[DEV MODE] 内容: {plain_content}")
            return True
        
        # 本番環境では実際にメールを送信
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(message)
            
        logger.info(f"メール送信成功 - 宛先: {to_email}, 件名: {subject}")
        return True
    
    except Exception as e:
        logger.error(f"メール送信エラー: {str(e)}")
        return False

def send_verification_email(email: str, name: str):
    """
    メールアドレス検証リンクを送信
    """
    from app.core.security import create_access_token
    from datetime import timedelta
    
    # 24時間有効な検証トークンを生成
    token = create_access_token(
        data={"email": email, "type": "email_verification"},
        expires_delta=timedelta(hours=24)
    )
    
    # 検証リンクの作成
    verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    
    # メールの内容
    subject = "【SmartAO】メールアドレスの確認"
    html_content = f"""
    <p>{name}様</p>
    
    <p>SmartAOにご登録いただき、ありがとうございます。</p>
    
    <p>以下のリンクをクリックして、メールアドレスの確認を完了してください。</p>
    
    <p><a href="{verification_link}">{verification_link}</a></p>
    
    <p>このリンクは24時間有効です。期限が切れた場合は、ログイン後に再送信をリクエストしてください。</p>
    
    <p>このメールに心当たりがない場合は、無視していただいて問題ありません。</p>
    
    <p>----<br>
    SmartAO チーム<br>
    お問い合わせ: support@smartao.example.com
    </p>
    """
    
    # メールの送信
    send_email(email, subject, html_content)

def send_password_reset_email(email: str, name: str, token: str):
    """
    パスワードリセットリンクを送信
    """
    # リセットリンクの作成
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    # メールの内容
    subject = "【SmartAO】パスワードリセットのご案内"
    html_content = f"""
    <p>{name}様</p>
    
    <p>SmartAOのパスワードリセットをリクエストいただきました。</p>
    
    <p>以下のリンクをクリックして、新しいパスワードを設定してください。</p>
    
    <p><a href="{reset_link}">{reset_link}</a></p>
    
    <p>このリンクは24時間有効です。</p>
    
    <p>このリクエストに心当たりがない場合は、このメールを無視してください。アカウントのパスワードは変更されません。</p>
    
    <p>----<br>
    SmartAO チーム<br>
    お問い合わせ: support@smartao.example.com
    </p>
    """
    
    # メールの送信
    send_email(email, subject, html_content)

def send_welcome_email(email: str, name: str):
    """
    新規登録完了後のウェルカムメールを送信
    """
    # メールの内容
    subject = "【SmartAO】ご登録ありがとうございます"
    html_content = f"""
    <p>{name}様</p>
    
    <p>SmartAOへのご登録が完了しました。</p>
    
    <p>SmartAOでは、以下のような機能をご利用いただけます：</p>
    
    <ul>
        <li>AIを活用した自己分析と志望校マッチング</li>
        <li>志望理由書作成サポート</li>
        <li>総合型選抜・学校推薦型選抜の対策</li>
        <li>効率的な学習計画の立案</li>
    </ul>
    
    <p>ご不明な点がございましたら、お気軽にお問い合わせください。</p>
    
    <p>----<br>
    SmartAO チーム<br>
    お問い合わせ: support@smartao.example.com
    </p>
    """
    
    # メールの送信
    send_email(email, subject, html_content)

def send_notification_email(email: str, name: str, subject: str, message: str):
    """
    通知メールを送信
    """
    # メールの内容
    html_content = f"""
    <p>{name}様</p>
    
    <p>{message}</p>
    
    <p>----<br>
    SmartAO チーム<br>
    お問い合わせ: support@smartao.example.com
    </p>
    """
    
    # メールの送信
    send_email(email, subject, html_content) 