from pydantic_settings import BaseSettings
from typing import List, ClassVar, Optional
import os
from dotenv import load_dotenv
import openai
from urllib.parse import urlparse, urlunparse

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
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # セキュリティ設定
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    AUTH_SECRET: str = os.getenv("AUTH_SECRET", "default-auth-secret")
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://smartao.jp", "https://stg.smartao.jp"]
    
    # データベース設定
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@db:5432/app_db"
    )
    
    # 追加: 非同期データベースURL
    ASYNC_DATABASE_URL: Optional[str] = None

    # --- AWS 設定 --- 
    AWS_REGION: str = os.getenv("AWS_REGION", "ap-northeast-1")
    AWS_S3_ICON_BUCKET_NAME: str = os.getenv("AWS_S3_ICON_BUCKET_NAME", "your-icon-bucket-name")
    # 必要であればエンドポイントURLも設定
    # AWS_S3_ENDPOINT_URL: Optional[str] = os.getenv("AWS_S3_ENDPOINT_URL") 
    # --- AWS 設定ここまで ---

    def __init__(self, **values):
        super().__init__(**values)
        # DATABASE_URL から ASYNC_DATABASE_URL を生成 (修正)
        if self.DATABASE_URL:
            parsed_url = urlparse(self.DATABASE_URL)
            if parsed_url.scheme == "postgresql":
                # スキームを 'postgresql+asyncpg' に変更
                # クエリパラメータはそのまま保持する
                async_parsed_url = parsed_url._replace(scheme="postgresql+asyncpg")
                self.ASYNC_DATABASE_URL = urlunparse(async_parsed_url)
            elif parsed_url.scheme == "postgresql+asyncpg":
                 # すでに非同期URLの場合はそのまま使う
                 self.ASYNC_DATABASE_URL = self.DATABASE_URL
            else:
                print(f"Warning: Unsupported database scheme for async: {parsed_url.scheme}")
                self.ASYNC_DATABASE_URL = None # または適切なデフォルト値
        else:
             self.ASYNC_DATABASE_URL = None

    # OpenAI設定
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Stripe設定
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    # Application Settings
    INSTRUCTION: str = load_instruction()

    # JWT設定
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 240  # 4時間（240分）に変更 - ロール変更時の待機時間を短縮
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30    # 30日
    JWT_ALGORITHM: str = "HS512" # JWTアルゴリズムを追加
    
    # メール設定
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@smartao.jp")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@smartao.jp")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# OpenAI APIキーの設定
openai.api_key = settings.OPENAI_API_KEY
