from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from sqlalchemy.engine import make_url
import ssl
import boto3                     # ★ 追加
import os                        # ★ 追加
import logging                   # ★ 追加
from botocore.exceptions import NoCredentialsError, ClientError # ★ 追加

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG) # 必要に応じてデバッグレベルを設定 (main.py等で設定推奨)

# --- S3からの証明書ダウンロード関数 ---
def download_ca_cert_from_s3() -> str | None:
    """S3からCA証明書をダウンロードし、ローカル一時ファイルのパスを返す"""
    # 環境変数からアカウントIDを取得 (ECSタスク定義で設定が必要)
    aws_account_id = os.getenv("AWS_ACCOUNT_ID")
    if not aws_account_id:
        logger.error("AWS_ACCOUNT_ID environment variable is not set.")
        return None
    logger.debug(f"Using AWS_ACCOUNT_ID: {aws_account_id}") # ★ デバッグログ追加

    s3_bucket_name = f"{settings.ENVIRONMENT}-rds-ca-certs-{aws_account_id}"
    s3_object_key = f"certs/rds-ca-{settings.ENVIRONMENT}-bundle.pem"
    local_cert_path = "/tmp/rds-ca-bundle.pem"

    logger.info(f"Attempting to download CA cert from s3://{s3_bucket_name}/{s3_object_key} to {local_cert_path}")

    if os.path.exists(local_cert_path):
        logger.info(f"CA cert already exists locally at {local_cert_path}, reusing.")
        return local_cert_path

    try:
        s3 = boto3.client('s3')
        logger.debug("S3 client created.") # ★ デバッグログ追加
        s3.download_file(s3_bucket_name, s3_object_key, local_cert_path)
        logger.info(f"Successfully downloaded CA cert to {local_cert_path}")
        return local_cert_path
    except NoCredentialsError:
        logger.error("AWS credentials not found...", exc_info=True) # ★ exc_info追加
        return None
    except ClientError as e:
        logger.error(f"S3 ClientError downloading CA cert...", exc_info=True) # ★ exc_info追加
        if e.response['Error']['Code'] == '404':
             logger.error(f"CA cert object not found in S3: s3://{s3_bucket_name}/{s3_object_key}")
        elif e.response['Error']['Code'] == '403':
              logger.error(f"Access denied when trying to download CA cert from S3. Check permissions for s3://{s3_bucket_name}/{s3_object_key}")
        else:
             logger.error(f"Error downloading CA cert from S3: {e}")
        return None
    except Exception as e:
         logger.exception(f"An unexpected error occurred during CA cert download.") # ★ メッセージ調整
         return None

# --- グローバル変数としてSSLコンテキストを保持 ---
_global_ssl_context = None

def get_ssl_context() -> ssl.SSLContext | None:
    """SSLコンテキストを取得または初期化する"""
    global _global_ssl_context
    logger.debug("get_ssl_context called.") # ★ デバッグログ追加
    if _global_ssl_context is None:
        logger.info("SSL context is None, attempting to initialize.") # ★ INFOログ追加
        local_cert_path = download_ca_cert_from_s3()
        if local_cert_path and os.path.exists(local_cert_path):
             try:
                logger.info(f"Creating SSL context using CA cert: {local_cert_path}")
                _global_ssl_context = ssl.create_default_context(cafile=local_cert_path)
                logger.info("SSL context created successfully.")
             except ssl.SSLError as e:
                 logger.error(f"SSL Error creating SSL context from {local_cert_path}", exc_info=True) # ★ exc_info追加
             except Exception as e:
                 logger.exception(f"Unexpected error during SSL context creation") # ★ メッセージ調整
        else:
            logger.warning("Failed to obtain CA cert, SSL context cannot be created.")
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
logger.info("Attempting to get/initialize SSL context for async engine...") # ★ INFOログ追加
db_ssl_context = get_ssl_context()
logger.info(f"Result of get_ssl_context: {'SSLContext object' if db_ssl_context else 'None'}") # ★ INFOログ追加

async_engine_kwargs = {
    "echo": settings.ENVIRONMENT != "production",
}
if db_ssl_context:
    async_engine_kwargs["connect_args"] = {"ssl": db_ssl_context}
    logger.info("SSL context obtained. Adding 'ssl' to async_engine connect_args.") # ★ INFOログ追加
else:
    logger.warning("SSL context not available. Async engine will be created without specific SSL connect_args.") # ★ ログレベル変更

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