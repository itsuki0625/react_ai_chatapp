from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv
import openai

load_dotenv()

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:80",
    ]
    
    # Application Settings
    INSTRUCTION: str = ""
    try:
        with open('./instruction.md', 'r', encoding='utf-8') as f:
            INSTRUCTION = f.read()
    except FileNotFoundError:
        pass

    # JWT設定
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()

# OpenAI APIキーの設定
openai.api_key = settings.OPENAI_API_KEY

settings = Settings() 