from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import ssl

# SQLAlchemyエンジンの作成
engine = create_engine(settings.DATABASE_URL)
# 非同期pg用のSSLコンテキストを生成
ssl_context = ssl.create_default_context()
# ASYNC_DATABASE_URLからsslmodeクエリを除外して接続
async_url = settings.ASYNC_DATABASE_URL.split("?", 1)[0]
async_engine = create_async_engine(
    async_url,
    echo=True,
    connect_args={"ssl": ssl_context},
)

# セッションファクトリの作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# モデルのベースクラス
Base = declarative_base()

# データベースセッションを取得する関数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 追加: 非同期データベースセッションを取得する関数
async def get_async_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

# データベース初期化用の関数
def init_db() -> None:
    """
    データベースの初期化を行う
    マイグレーション実行時やテスト時に使用
    """
    from models import Base  # 循環インポートを避けるためにここでインポート
    Base.metadata.create_all(bind=engine) 