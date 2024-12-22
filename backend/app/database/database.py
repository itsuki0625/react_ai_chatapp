from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from core.config import settings
from typing import Generator

# エンジンの作成
engine = create_engine(settings.DATABASE_URL)

# セッションファクトリの作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    データベースセッションの依存性注入用のジェネレータ
    
    Yields:
        Session: SQLAlchemyのセッションインスタンス
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# データベース初期化用の関数
def init_db() -> None:
    """
    データベースの初期化を行う
    マイグレーション実行時やテスト時に使用
    """
    from models import Base  # 循環インポートを避けるためにここでインポート
    Base.metadata.create_all(bind=engine) 