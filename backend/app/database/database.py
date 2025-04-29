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

# --- S3からの証明書ダウンロード関数 ---
def download_ca_cert_from_s3() -> str | None:
    """S3からCA証明書をダウンロードし、ローカル一時ファイルのパスを返す"""
    # 環境変数からアカウントIDを取得 (ECSタスク定義で設定が必要)
    aws_account_id = os.getenv("AWS_ACCOUNT_ID")
    if not aws_account_id:
        logger.error("AWS_ACCOUNT_ID environment variable is not set.")
        return None

    s3_bucket_name = f"{settings.ENVIRONMENT}-rds-ca-certs-{aws_account_id}"
    s3_object_key = f"certs/rds-ca-{settings.ENVIRONMENT}-bundle.pem"
    # コンテナ内の書き込み可能な一時パス
    local_cert_path = "/tmp/rds-ca-bundle.pem"

    logger.info(f"Attempting to download CA cert from s3://{s3_bucket_name}/{s3_object_key} to {local_cert_path}")

    # すでにファイルが存在する場合は再利用 (コンテナ再起動時の効率化)
    if os.path.exists(local_cert_path):
        logger.info(f"CA cert already exists locally at {local_cert_path}, reusing.")
        # TODO: ファイルの有効期限や更新チェックが必要な場合はここに追加
        return local_cert_path

    try:
        # ECSタスクロールから認証情報を取得することを期待
        s3 = boto3.client('s3')
        s3.download_file(s3_bucket_name, s3_object_key, local_cert_path)
        logger.info(f"Successfully downloaded CA cert to {local_cert_path}")
        return local_cert_path
    except NoCredentialsError:
        logger.error("AWS credentials not found. Ensure ECS task role has S3 read permissions (s3:GetObject) for s3://%s/%s", s3_bucket_name, s3_object_key)
        return None
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            logger.error(f"CA cert object not found in S3: s3://{s3_bucket_name}/{s3_object_key}")
        elif e.response['Error']['Code'] == '403':
             logger.error(f"Access denied when trying to download CA cert from S3. Check permissions for s3://{s3_bucket_name}/{s3_object_key}")
        else:
            logger.error(f"Error downloading CA cert from S3: {e}")
        return None
    except Exception as e:
         logger.exception(f"An unexpected error occurred during CA cert download: {e}") # スタックトレースも出力
         return None

# --- グローバル変数としてSSLコンテキストを保持 ---
_global_ssl_context = None

def get_ssl_context() -> ssl.SSLContext | None:
    """SSLコンテキストを取得または初期化する"""
    global _global_ssl_context
    if _global_ssl_context is None:
        local_cert_path = download_ca_cert_from_s3()
        if local_cert_path and os.path.exists(local_cert_path):
             try:
                logger.info(f"Creating SSL context using CA cert: {local_cert_path}")
                _global_ssl_context = ssl.create_default_context(cafile=local_cert_path)
                # オプション: ホスト名検証など
                # _global_ssl_context.check_hostname = True
                # _global_ssl_context.verify_mode = ssl.CERT_REQUIRED
                logger.info("SSL context created successfully.")
             except ssl.SSLError as e:
                 logger.error(f"Error creating SSL context from {local_cert_path}: {e}")
             except Exception as e:
                 logger.exception(f"Unexpected error during SSL context creation: {e}")
        else:
            logger.warning("Failed to obtain CA cert, SSL context cannot be created.")
    return _global_ssl_context

# --- SQLAlchemyエンジンの作成 ---

# 同期エンジン (必要であればこちらもSSL設定を追加)
engine = create_engine(settings.DATABASE_URL)

# 非同期エンジン用のURLを組み立て
url_obj = make_url(settings.ASYNC_DATABASE_URL)
url_obj = url_obj.set(drivername="postgresql+asyncpg")

# 非同期エンジンを作成 (connect_argsでSSLContextを指定)
# アプリケーション起動時にSSLコンテキストを準備
db_ssl_context = get_ssl_context()

async_engine_kwargs = {
    "echo": settings.ENVIRONMENT != "production", # 本番以外でSQLを出力 (例)
}
if db_ssl_context:
    async_engine_kwargs["connect_args"] = {"ssl": db_ssl_context}
    logger.info("Async engine configured with SSL context.")
else:
    # SSLコンテキストが取得できなかった場合
    logger.warning("SSL context not available for async engine. Database connection might be insecure or fail if SSL is required by the server.")
    # ここでエラーにするか、検証なしモード(非推奨)にするかは要件次第
    # raise RuntimeError("Failed to initialize database SSL context")
    # async_engine_kwargs["connect_args"] = {"ssl": "require"} # 検証スキップ (非推奨)

async_engine = create_async_engine(
    url_obj,
    **async_engine_kwargs
)

# --- セッションファクトリ、Base、get_db, get_async_db, init_db は変更なし ---

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.exception("Error during async database session") # エラーログ追加
            await session.rollback()
            raise e
        finally:
            await session.close()

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