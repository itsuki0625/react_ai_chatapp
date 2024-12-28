from pydantic_settings import BaseSettings
from typing import List, ClassVar
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
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
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

# OpenAI APIキーの設定
openai.api_key = settings.OPENAI_API_KEY
