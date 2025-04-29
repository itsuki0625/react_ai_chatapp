from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from sqlalchemy.engine import make_url
import ssl # ★ 追加: sslモジュールをインポート

# SQLAlchemyエンジンの作成
engine = create_engine(settings.DATABASE_URL)

# ★ 追加: CA証明書のパス (Dockerfileでコピーしたパス)
CA_CERT_PATH = "/app/certs/ap-northeast-1-bundle.pem"

# ★ 追加: SSLコンテキストを作成し、CA証明書をロード
ssl_context = ssl.create_default_context(cafile=CA_CERT_PATH)
# 必要に応じてホスト名検証を設定 (より厳格にする場合)
# ssl_context.check_hostname = True
# ssl_context.verify_mode = ssl.CERT_REQUIRED

# 非同期エンジン用のURLを組み立て
url_obj = make_url(settings.ASYNC_DATABASE_URL)
# ドライバ名を設定 (sslmodeはここでは設定しない)
url_obj = url_obj.set(drivername="postgresql+asyncpg")
# ★ 削除: DSNへのsslmode=requireの追加を削除
# query = dict(url_obj.query)
# query["sslmode"] = "require"
# url_obj = url_obj.set(query=query)

# 非同期エンジンを作成 (connect_argsでSSLContextを指定)
async_engine = create_async_engine(
    url_obj,
    echo=True,
    # ★ 変更: connect_argsにはsslコンテキストのみを指定
    connect_args={
        "ssl": ssl_context,
        # "sslmode": "verify-ca" # ← この行を削除またはコメントアウト
    }
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