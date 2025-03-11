from pydantic_settings import BaseSettings
from typing import List
import os
import openai
import logging

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_instruction() -> str:
    instruction_path = os.path.join(os.path.dirname(__file__), "instruction.txt")
    if os.path.exists(instruction_path):
        with open(instruction_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

class Settings(BaseSettings):
    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "postgres")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "postgres")

    @property
    def DATABASE_URL(self) -> str:
        url = f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        # SSL要件を一時的に無効化
        url += "?sslmode=disable"
        logger.info(f"Connecting to database at: {self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}")
        return url
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.40.*:3000",
    ]
    
    # Application Settings
    INSTRUCTION: str = load_instruction()

    # JWT設定
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Session settings
    SESSION_COOKIE_NAME: str = "session"
    SESSION_MAX_AGE: int = 3600  # 1時間
    SESSION_SECURE: bool = False  # 開発環境ではFalse、本番環境ではTrue

    class Config:
        env_file = ".env"

settings = Settings()

# 設定値のログ出力
logger.info(f"Database Host: {settings.DB_HOST}")
logger.info(f"Database Port: {settings.DB_PORT}")
logger.info(f"Database Name: {settings.DB_NAME}")

# OpenAI APIキーの設定
openai.api_key = settings.OPENAI_API_KEY
