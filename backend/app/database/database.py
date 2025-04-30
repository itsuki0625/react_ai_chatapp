from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from sqlalchemy.engine import make_url
import ssl
import os                        # パス操作用に復活
import logging                   # ★ 追加
from sqlalchemy import event  # DB接続/プールイベント用

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG) # ★ DEBUGログ有効化 (main.py で設定される想定)
# logger.setLevel(logging.DEBUG) # 必要に応じてデバッグレベルを設定 (main.py等で設定推奨)

# --- SQLAlchemyエンジンの作成 ---

logger.info("Configuring database engines...") # ★ INFOログ追加

# 同期エンジン
engine = create_engine(settings.DATABASE_URL)
logger.info(f"Sync engine configured for URL: {settings.DATABASE_URL}") # ★ INFOログ追加

# 非同期エンジン用のURLを組み立て
url_obj = make_url(settings.ASYNC_DATABASE_URL)
url_obj = url_obj.set(drivername="postgresql+asyncpg")
logger.info(f"Async engine base URL object created: {url_obj}") # ★ INFOログ追加

# 非同期エンジンを作成 (connect_argsでSSLContextを指定)
logger.info("Determining SSL context for async engine...")

# SSLContextを取得
# db_ssl_context = get_ssl_context() # SSL検証無効化のためコメントアウト
# logger.info(f"Result of get_ssl_context: {'SSLContext object' if db_ssl_context else 'None'}")

async_engine_kwargs = {
    "echo": settings.ENVIRONMENT != "production",
}

# SSLContext があれば connect_args に設定
# if db_ssl_context: # SSL検証無効化のためコメントアウト
#     async_engine_kwargs["connect_args"] = {"ssl": db_ssl_context}
#     logger.info("SSLContext obtained. Adding it to async_engine connect_args.")
# else:
#     logger.info(f"SSLContext not available or not required for environment {settings.ENVIRONMENT}. Creating engine without explicit SSL context.")
logger.warning("Skipping SSL context/verification for DB connection based on current configuration.")

logger.debug(f"Final async_engine_kwargs: {async_engine_kwargs}")
logger.info(f"Creating async engine with URL: {url_obj} and kwargs: {async_engine_kwargs}") # ★ INFOログ追加 (kwargs全体を出力)
try:
    async_engine = create_async_engine(
        url_obj,
        **async_engine_kwargs
    )
    logger.info("Async engine created successfully.") # ★ INFOログ追加
except Exception as e:
    logger.exception("Failed to create async engine") # ★ 例外ログ追加
    # 必要ならここでアプリケーションを終了させるなどの処理を追加
    raise

# --- DB接続イベントのログ設定 ---
@event.listens_for(async_engine.sync_engine, "connect")
def log_dbapi_connect(dbapi_connection, connection_record):
    logger.debug(f"[DB CONNECT] New DBAPI connection: {connection_record}")

@event.listens_for(async_engine.sync_engine.pool, "checkout")
def log_dbapi_checkout(dbapi_connection, connection_record, connection_proxy):
    logger.debug(f"[DB POOL CHECKOUT] Pool checkout: {connection_record}")

# --- セッションファクトリ、Base、get_db, get_async_db, init_db は変更なし ---

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
logger.info("Session factories configured.") # ★ INFOログ追加

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db() -> AsyncSession:
    logger.debug("Async DB session requested.") # ★ デバッグログ追加
    async with AsyncSessionLocal() as session:
        logger.debug(f"Async DB session {id(session)} acquired.") # ★ デバッグログ追加 (セッションID)
        try:
            yield session
            await session.commit()
            logger.debug(f"Async DB session {id(session)} committed.") # ★ デバッグログ追加
        except Exception as e:
            logger.exception(f"Error during async database session {id(session)}")
            await session.rollback()
            logger.warning(f"Async DB session {id(session)} rolled back.") # ★ 警告ログ追加
            raise e
        finally:
            await session.close()
            logger.debug(f"Async DB session {id(session)} closed.") # ★ デバッグログ追加

def init_db() -> None:
    """
    データベースの初期化を行う
    マイグレーション実行時やテスト時に使用
    """
    # この関数は同期エンジンを使用しているため、SSL設定の影響は限定的
    from app.models.base import Base # モデルのインポートパス確認
    logger.info("Initializing database tables (if they don't exist)...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialization check complete.")
    except Exception as e:
        logger.exception("Error during database initialization")
        raise e 