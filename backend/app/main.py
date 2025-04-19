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
    admin
)
from app.middleware.auth import AuthMiddleware
import logging
from fastapi import APIRouter
from app.database.database import Base, engine

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Study Support API",
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
    max_age=3600,  # 1時間
    same_site="lax",  # CSRF対策
    https_only=False,  # 開発環境ではFalse
)

# 3. CORSミドルウェア（最初に実行される）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # 開発環境
        "https://yourdomain.com",  # 本番環境（必要に応じて変更）
    ],
    allow_credentials=True,  # 認証情報を許可
    allow_methods=["*"],  # すべてのHTTPメソッドを許可
    allow_headers=["*"],  # すべてのヘッダーを許可
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

app.include_router(api_router, prefix="/api/v1")

# APIルーターの設定後に追加
for route in app.routes:
    logger.info(f"Registered route: {route.path}")

# データベースモデルの作成
# Base.metadata.create_all(bind=engine)  # Alembicを使用する場合はコメントアウト

@app.get("/")
def read_root():
    return {"message": "Welcome to the API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)