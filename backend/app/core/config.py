from pydantic_settings import BaseSettings
from typing import List, ClassVar, Optional
import os
from dotenv import load_dotenv
import openai

load_dotenv()

# クラスの外で instruction.md を読み込む
def load_instruction() -> str:
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        instruction_path = os.path.join(base_dir, 'app', 'core', 'instruction.md')
        
        with open(instruction_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"instruction.md が見つかりません。検索パス: {instruction_path}")
        return ""
    except Exception as e:
        print(f"インストラクションファイルの読み込み中にエラーが発生しました: {str(e)}")
        return ""

class Settings(BaseSettings):
    # アプリケーション設定
    PROJECT_NAME: str = "Study Support API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # セキュリティ設定
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # データベース設定
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@db:5432/app_db"
    )
    
    # OpenAI設定
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")  # 小文字のプロパティも追加
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # Stripe設定
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    # Application Settings
    INSTRUCTION: str = load_instruction()

    # JWT設定
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # 15分
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30    # 30日
    
    # Redis設定（トークンブラックリスト、レート制限など）
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # メール設定
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.example.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@smartao.example.com")
    
    # 2FA設定
    TOTP_ISSUER: str = "SmartAO"
    
    # レート制限設定
    RATE_LIMIT_LOGIN: int = 5   # 15分間に5回までのログイン試行
    RATE_LIMIT_SIGNUP: int = 3  # 1時間に3回までのサインアップ
    RATE_LIMIT_2FA: int = 10    # 15分間に10回までの2FA試行

    # Session settings
    SESSION_COOKIE_NAME: str = "session"
    SESSION_MAX_AGE: int = 3600  # 1時間
    SESSION_SECURE: bool = False  # 開発環境ではFalse、本番環境ではTrue

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# OpenAI APIキーの設定
openai.api_key = settings.OPENAI_API_KEY
