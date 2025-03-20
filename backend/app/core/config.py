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

def get_database_url() -> str:
    """
    環境変数に基づいて適切なデータベースURLを返す
    """
    connection_type = os.getenv("CONNECTION_TYPE", "local")
    
    if connection_type == "rds":
        # AWS RDS接続用のURL
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        db_name = os.getenv("DB_NAME")
        return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    else:
        # ローカルDB接続用のURL
        host = os.getenv("DB_HOST", "db")
        port = os.getenv("DB_PORT", "5432")
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "postgres")
        db_name = os.getenv("DB_NAME", "postgres")
        return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = get_database_url()
    
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

# OpenAI APIキーの設定
openai.api_key = settings.OPENAI_API_KEY
