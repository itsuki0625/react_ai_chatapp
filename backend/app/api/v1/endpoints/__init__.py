from fastapi import APIRouter

# 各エンドポイントモジュールからルーターをインポート
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.subscription import router as subscription_router
from app.api.v1.endpoints.admission import router as admission_router
from app.api.v1.endpoints.application import router as application_router
from app.api.v1.endpoints.statement import router as statement_router
from app.api.v1.endpoints.university import router as university_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.chat import router as chat_router
from app.api.v1.endpoints.content import router as content_router
from app.api.v1.endpoints.quiz import router as quiz_router
from app.api.v1.endpoints.roles import router as roles_router
from app.api.v1.endpoints.study_plans import router as study_plans_router
from app.api.v1.endpoints.communication import router as communication_router

# 各ルーターをエクスポート
__all__ = [
    "admin_router",
    "subscription_router",
    "admission_router",
    "application_router",
    "statement_router",
    "university_router",
    "auth_router",
    "chat_router",
    "content_router",
    "quiz_router",
    "roles_router",
    "study_plans_router",
    "communication_router",
]
