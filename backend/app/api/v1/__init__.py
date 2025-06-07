from fastapi import APIRouter

# メインのv1ルーターを作成
api_router = APIRouter()

# 各エンドポイントルーターをインポート
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
from app.api.v1.endpoints.permissions import router as permissions_router
from app.api.v1.endpoints.roles import router as roles_router
from app.api.v1.endpoints.desired_schools import router as desired_schools_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.content_category import router as content_category_router
from app.api.v1.endpoints.notifications import router as notifications_router
from app.api.v1.endpoints.push import router as push_router
from app.api.v1.endpoints.in_app_notification import router as in_app_notification_router
from app.api.v1.endpoints.admin_notifications import router as admin_notifications_router

# 各ルーターをメインルーターに追加
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(subscription_router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(admission_router, prefix="/admissions", tags=["admissions"])
api_router.include_router(application_router, prefix="/applications", tags=["applications"])
api_router.include_router(statement_router, prefix="/statements", tags=["statements"])
api_router.include_router(university_router, prefix="/universities", tags=["universities"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(content_router, prefix="/contents", tags=["content"])
api_router.include_router(content_category_router, prefix="/content-categories", tags=["content-categories"])
api_router.include_router(quiz_router, prefix="/quizzes", tags=["quizzes"])
api_router.include_router(permissions_router, prefix="/permissions", tags=["permissions"])
api_router.include_router(roles_router, prefix="/roles", tags=["roles"])
api_router.include_router(desired_schools_router, prefix="/desired-schools", tags=["desired-schools"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
api_router.include_router(push_router, prefix="/push", tags=["push"])
api_router.include_router(in_app_notification_router, prefix="/in-app-notifications", tags=["in-app-notifications"])
api_router.include_router(admin_notifications_router, prefix="/admin/notification-settings", tags=["admin-notification-settings"])

