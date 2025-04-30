from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from sqlalchemy.engine import make_url
import ssl
import os                        # パス操作用に復活
import logging                   # ★ 追加

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG) # 必要に応じてデバッグレベルを設定 (main.py等で設定推奨)

# --- グローバル変数としてSSLコンテキストを保持 ---
_global_ssl_context = None

def get_ssl_context() -> ssl.SSLContext | None:
    """SSLコンテキストを取得または初期化する"""
    global _global_ssl_context
    logger.debug("get_ssl_context called.") # ★ デバッグログ追加
    # デバッグ: ENVIRONMENT と certs ディレクトリを確認
    logger.debug(f"ENVIRONMENT in get_ssl_context: {settings.ENVIRONMENT}")
    certs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "certs"))
    try:
        logger.debug(f"Certificates directory listing: {os.listdir(certs_dir)}")
    except Exception as e:
        logger.error(f"Failed to list certs directory {certs_dir}: {e}")
    if _global_ssl_context is None:
        logger.info("SSL context is None, initializing from local cert.")
        # 環境ごとに証明書ファイルを切り替え
        cert_filename = f"rds-ca-{settings.ENVIRONMENT}-bundle.pem"
        # プロジェクトルートの certs ディレクトリを参照
        cert_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "certs", cert_filename)
        )
        logger.debug(f"Computed cert_path: {cert_path}")
        if os.path.exists(cert_path):
            try:
                logger.info(f"Creating SSL context using local CA cert: {cert_path}")
                _global_ssl_context = ssl.create_default_context(cafile=cert_path)
                logger.info("SSL context created successfully.")
            except ssl.SSLError as e:
                logger.error(f"SSL Error creating SSL context from {cert_path}", exc_info=True)
            except Exception:
                logger.exception("Unexpected error during SSL context creation")
        else:
            logger.warning(f"Local CA cert not found at {cert_path}, SSL context cannot be created.")
    else:
        logger.debug("Returning existing SSL context.") # ★ デバッグログ追加
    return _global_ssl_context

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
# ステージング／本番環境のみSSLコンテキストを使用
if settings.ENVIRONMENT in ("stg", "production"):
    logger.info("Initializing SSL context for environment: {settings.ENVIRONMENT}")
    db_ssl_context = get_ssl_context()
    logger.info(f"Result of get_ssl_context: {'SSLContext object' if db_ssl_context else 'None'}")
else:
    db_ssl_context = None
    logger.info(f"Skipping SSL context in development environment: {settings.ENVIRONMENT}")

async_engine_kwargs = {
    "echo": settings.ENVIRONMENT != "production",
}
logger.debug(f"db_ssl_context before engine kwargs: {db_ssl_context}")
if db_ssl_context:
    async_engine_kwargs["connect_args"] = {"ssl": db_ssl_context}
    logger.info("SSL context obtained. Adding 'ssl' to async_engine connect_args.") # ★ INFOログ追加
else:
    logger.warning("SSL context not available. Async engine will be created without specific SSL connect_args.") # ★ ログレベル変更

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
    from app.models.models import Base # モデルのインポートパス確認
    logger.info("Initializing database tables (if they don't exist)...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialization check complete.")
    except Exception as e:
        logger.exception("Error during database initialization")
        raise e 