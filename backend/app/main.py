from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings
from app.api.v1.endpoints import chat, auth, statement, application, university, admission, content
from app.middleware.auth import AuthMiddleware
import logging

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # 全HTTPメソッドを許可
    allow_headers=["*"],  # 全ヘッダーを許可
)

# ルーターの登録
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(
    chat.router,
    prefix="/api/v1",
    tags=["chat"]
)
app.include_router(
    statement.router,
    prefix="/api/v1/statements",
    tags=["statements"]
)
app.include_router(
    application.router,
    prefix="/api/v1/applications",
    tags=["applications"]
)
app.include_router(
    university.router,
    prefix="/api/v1/universities",
    tags=["universities"]
)
app.include_router(
    admission.router,
    prefix="/api/v1/admission-methods",
    tags=["admission-methods"]
)
app.include_router(
    content.router,
    prefix="/api/v1/contents",
    tags=["contents"]
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)