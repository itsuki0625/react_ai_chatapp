from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings
from app.api.v1.endpoints import (
    auth,
    chat,
    university,
    admission,
    application,
    statement,
    content,
    subscription,
    admin,
    quiz,
    roles,
    study_plans,
    communication
)
from app.middleware.auth import AuthMiddleware
import logging
from fastapi import APIRouter
from app.database.database import Base, engine
from fastapi.background import BackgroundTasks
from app.crud.token import remove_expired_tokens
from sqlalchemy.orm import Session
from contextlib import contextmanager
import asyncio
import time

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# データベースセッションコンテキスト
@contextmanager
def get_db_session():
    """
    データベースセッションのコンテキストマネージャー
    """
    from app.database.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 期限切れトークンのクリーンアップ
async def cleanup_expired_tokens():
    """
    期限切れのブラックリストトークンを定期的に削除
    """
    while True:
        try:
            with get_db_session() as db:
                removed = remove_expired_tokens(db)
                logger.info(f"期限切れトークンのクリーンアップ: {removed}件削除")
        except Exception as e:
            logger.error(f"トークンクリーンアップエラー: {str(e)}")
        
        # 1時間に1回実行（本番環境では調整が必要）
        await asyncio.sleep(3600)  # 1時間 = 3600秒

app = FastAPI(
    title="SmartAO API",
    description="志望校管理と志望理由書作成支援のためのAPI",
    version="1.0.0",
    docs_url="/api/v1/docs",  
)

# ミドルウェアの順序が重要：
# 1. 認証ミドルウェア（最後に実行される）
app.add_middleware(AuthMiddleware)

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

# 3. CORSミドルウェア（最初に実行される）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # ローカル開発環境
        "http://localhost:5050",  # ローカルAPIサーバー
        "http://backend:5050",    # Docker内部通信
        "http://frontend:3000",   # Docker内部通信
        "http://127.0.0.1:3000",  # 代替ローカル開発環境
        "http://host.docker.internal:3000",  # Docker -> ホスト接続
        "http://host.docker.internal:5050",  # Docker -> ホスト接続
        "https://yourdomain.com",  # 本番環境（必要に応じて変更）
        # すべてのオリジンを許可 - 開発時のみ使用
        "*"
    ],
    allow_credentials=True,  # 認証情報を許可
    allow_methods=["*"],  # すべてのHTTPメソッドを許可
    allow_headers=["*"],  # すべてのヘッダーを許可
    expose_headers=["Set-Cookie", "X-Auth-Status"],  # 公開するヘッダー
)

# APIルーターの設定
api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(university.router, prefix="/universities", tags=["universities"])
api_router.include_router(admission.router, prefix="/admission", tags=["admission"])
api_router.include_router(application.router, prefix="/applications", tags=["applications"])
api_router.include_router(statement.router, prefix="/statements", tags=["statements"])
api_router.include_router(content.router, prefix="/contents", tags=["contents"])
api_router.include_router(subscription.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(quiz.router, prefix="/quizzes", tags=["quizzes"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(study_plans.router, prefix="/study-plans", tags=["study-plans"])
api_router.include_router(communication.router, prefix="/communication", tags=["communication"])

app.include_router(api_router, prefix="/api/v1")

# APIルーターの設定後に追加
for route in app.routes:
    logger.info(f"Registered route: {route.path}")

# データベースモデルの作成
# Base.metadata.create_all(bind=engine)  # Alembicを使用する場合はコメントアウト

# 起動時にバックグラウンドタスクを開始
@app.on_event("startup")
async def startup_event():
    # 期限切れトークンのクリーンアップタスク
    asyncio.create_task(cleanup_expired_tokens())
    logger.info("バックグラウンド期限切れトークンクリーンアップタスクを開始しました")

@app.get("/")
def read_root():
    return {"message": "Welcome to the API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)