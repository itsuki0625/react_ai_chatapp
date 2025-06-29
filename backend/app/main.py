from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings
from app.api.v1 import api_router as v1_api_router
from app.middleware.auth import AuthMiddleware
import logging
from app.database.database import Base, engine
from fastapi import BackgroundTasks
from app.crud.token import remove_expired_tokens
import asyncio
import time
import os  # CA証明書確認用
from contextlib import asynccontextmanager
from fastapi.responses import Response


# --- ロギング設定 --- 
# 基本設定 (アプリケーション全体のデフォルトレベル)
log_level_str = os.getenv("LOG_LEVEL", "DEBUG").upper()
log_level = getattr(logging, log_level_str, logging.DEBUG)

logging.basicConfig(
    level=log_level,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
)

# boto3/botocore のログレベルを INFO に設定して詳細ログを抑制
logging.getLogger("boto3").setLevel(logging.INFO)
logging.getLogger("botocore").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)

# SQLAlchemyのエンジンログレベルをWARNINGに設定してINFOログを抑制
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# httpcore/openai のログレベルを INFO に設定して詳細ログを抑制
logging.getLogger("httpcore").setLevel(logging.INFO)
logging.getLogger("httpcore.http11").setLevel(logging.WARNING)  # HTTP/1.1の詳細ログを更に抑制
logging.getLogger("openai").setLevel(logging.INFO)
logging.getLogger("openai._base_client").setLevel(logging.WARNING)  # OpenAIクライアントの詳細ログを抑制
logging.getLogger("httpx").setLevel(logging.INFO)

# アプリケーション内部のログレベル調整
logging.getLogger("app.database.database").setLevel(logging.INFO)  # データベース関連のDEBUGログを抑制
logging.getLogger("app.middleware.auth").setLevel(logging.DEBUG)  # 認証ミドルウェアのDEBUGログを有効化（一時的）
logging.getLogger("app.api.deps").setLevel(logging.INFO)  # API依存関係のDEBUGログを抑制
logging.getLogger("app.api.v1.endpoints.chat").setLevel(logging.INFO)  # チャットエンドポイントのDEBUGログを抑制

# アプリケーション自体のロガー取得
logger = logging.getLogger(__name__)
# --- ロギング設定ここまで ---

# 期限切れトークンのクリーンアップ
async def cleanup_expired_tokens():
    """
    期限切れのブラックリストトークンを定期的に削除
    """
    while True:
        try:
            from app.database.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                removed = await remove_expired_tokens(db)
                logger.info(f"期限切れトークンのクリーンアップ: {removed}件削除")
        except Exception as e:
            logger.error(f"トークンクリーンアップエラー: {str(e)}")
        
        # 1時間に1回実行（本番環境では調整が必要）
        await asyncio.sleep(3600)  # 1時間 = 3600秒

# アプリケーションのライフサイクル管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時の処理
    # 期限切れトークンのクリーンアップタスク
    cleanup_task = asyncio.create_task(cleanup_expired_tokens())
    logger.info("バックグラウンド期限切れトークンクリーンアップタスクを開始しました")
    
    yield
    
    # 終了時の処理
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        logger.info("バックグラウンドタスクが正常に終了しました")

app = FastAPI(
    title="SmartAO API",
    description="志望校管理と志望理由書作成支援のためのAPI",
    version="1.0.0",
    docs_url="/api/v1/docs",  
    lifespan=lifespan
)

# CORS対応のためのオリジンリスト
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # ローカル開発環境（フロントエンド - 旧ポート）
    "http://localhost:3001",  # ローカル開発環境（代替ポート）
    "http://localhost:3030",  # ローカル開発環境（フロントエンド - 新ポート）
    "http://localhost:5050",  # ローカルAPIサーバー
    "http://127.0.0.1:3000",  # 代替ローカル開発環境（旧ポート）
    "http://127.0.0.1:3001",  # 代替ローカル開発環境
    "http://127.0.0.1:3030",  # 代替ローカル開発環境（新ポート）
    "http://backend:5050",    # Docker内部通信
    "http://frontend:3000",   # Docker内部通信（旧ポート）
    "http://frontend:3030",   # Docker内部通信（新ポート）
    "http://host.docker.internal:3000",  # Docker -> ホスト接続（旧ポート）
    "http://host.docker.internal:3001",  # Docker -> ホスト接続
    "http://host.docker.internal:3030",  # Docker -> ホスト接続（新ポート）
    "http://host.docker.internal:5050",  # Docker -> ホスト接続
    "https://yourdomain.com",  # 本番環境（必要に応じて変更）
    "https://stg.smartao.jp", # ステージング環境フロントエンド
    "https://stg-api.smartao.jp", # ステージング環境API（追加）
    "https://api.smartao.jp", # 本番環境API
    "https://app.smartao.jp", # 本番環境フロントエンド
    "https://smartao.jp",     # 本番環境メインドメイン
]

# CORS設定をログ出力
logger.info(f"CORS許可オリジン: {ALLOWED_ORIGINS}")

# ミドルウェアの順序が重要：（後に追加されたものが先に実行される）
# 1. CORSミドルウェア（最初に実行される）
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,  # 認証情報を許可
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # 明示的なメソッド指定
    allow_headers=[
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-CSRF-Token",
        "X-Auth-Status",
        "X-Request-Info",  # デバッグ用ヘッダーを追加
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],  # 具体的なヘッダー指定
    expose_headers=["Set-Cookie", "X-Auth-Status"],  # 公開するヘッダー
    max_age=3600,  # プリフライトリクエストのキャッシュ時間
)

# 2. セッションミドルウェア（認証の前に実行される）
app.add_middleware(
    SessionMiddleware, 
    secret_key=settings.SECRET_KEY,
    session_cookie="session",
    max_age=86400,  # 24時間
    same_site="lax",  # CSRF対策
    https_only=False,  # 開発環境ではFalse
    path="/"  # クッキーのパスを明示的に設定
)

# 2.5. デバッグ用リクエスト/レスポンスログミドルウェア
@app.middleware("http")
async def debug_request_response(request: Request, call_next):
    origin = request.headers.get("origin")
    
    # リクエスト情報をログ出力
    if request.method == "POST" and "chat/sessions" in str(request.url):
        logger.info(f"🔍 POST リクエスト詳細:")
        logger.info(f"  URL: {request.url}")
        logger.info(f"  Origin: {origin}")
        logger.info(f"  Method: {request.method}")
        logger.info(f"  Headers: {dict(request.headers)}")
    
    # レスポンスを取得
    response = await call_next(request)
    
    # レスポンス情報をログ出力
    if request.method == "POST" and "chat/sessions" in str(request.url):
        logger.info(f"🔍 POST レスポンス詳細:")
        logger.info(f"  Status: {response.status_code}")
        logger.info(f"  Headers: {dict(response.headers)}")
        logger.info(f"  Origin: {origin}")
        
        # CORS関連ヘッダーを特に確認
        cors_headers = {
            key: value for key, value in response.headers.items() 
            if key.lower().startswith('access-control')
        }
        logger.info(f"  CORS Headers: {cors_headers}")
    
    return response

# 3. 認証ミドルウェア（最後に実行される）
app.add_middleware(AuthMiddleware)

# グローバル例外ハンドラー（CORSヘッダーを含むエラーレスポンス）
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全ての例外をキャッチしてCORSヘッダーを含むエラーレスポンスを返す
    """
    logger.error(f"グローバル例外ハンドラー: {request.url.path} - {str(exc)}", exc_info=True)
    
    # オリジンを取得してCORSヘッダーを設定
    origin = request.headers.get("origin")
    
    cors_headers = {}
    if origin and origin in ALLOWED_ORIGINS:
        cors_headers.update({
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, X-CSRF-Token, X-Auth-Status, X-Request-Info, Origin, Access-Control-Request-Method, Access-Control-Request-Headers",
            "Vary": "Origin"
        })
    
    # HTTPExceptionの場合は元のステータスコードを保持
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=cors_headers
        )
    
    # その他の例外は500エラーとして返す
    return JSONResponse(
        status_code=500,
        content={"detail": "内部サーバーエラーが発生しました"},
        headers=cors_headers
    )

# 修正: v1 の集約ルーターを /api/v1 プレフィックスで追加
app.include_router(v1_api_router, prefix="/api/v1")

# カスタムOPTIONSハンドラーを完全に削除し、CORSMiddlewareに任せる

# APIルーターの設定後に追加
for route in app.routes:
    logger.info(f"Registered route: {route.path}")

# データベースモデルの作成
# Base.metadata.create_all(bind=engine)  # Alembicを使用する場合はコメントアウト

@app.get("/")
def read_root():
    return {"message": "Welcome to the API"}

# ヘルスチェックエンドポイント（認証なしでアクセス可能）
@app.get("/health")
def health_check():
    """
    ELB/ALBのヘルスチェック用エンドポイント
    データベース接続などの簡易チェックを行い、サービスの状態を返す
    """
    try:
        # ここに必要なヘルスチェックロジックを追加できます
        # 例: データベース接続の確認など
        return {
            "status": "healthy",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"ヘルスチェックエラー: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)