from fastapi import Request, HTTPException, status
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # 認証が不要なパスをスキップ
        if request.url.path in [
            "/api/v1/auth/login",
            "/api/v1/auth/logout",
            "/api/v1/auth/signup",
            "/docs",
            "/openapi.json",
            # "/api/v1/chat/stream",
            # "/api/v1/chat/sessions",
            # "/api/v1/chat/sessions/{session_id}/messages"
        ]:
            return await call_next(request)

        try:
            # セッションの確認（修正）
            if not hasattr(request, "session"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="セッションが見つかりません"
                )

            if "user_id" not in request.session:
                if request.url.path.startswith("/api/"):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="認証が必要です"
                    )

            response = await call_next(request)
            return response

        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            ) 