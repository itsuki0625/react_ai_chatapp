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
            "/docs",
            "/openapi.json"
        ]:
            return await call_next(request)

        try:
            # セッションからユーザー情報を確認
            if "session" not in request.scope:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session not found"
                )

            if "user_id" not in request.session:
                if request.url.path.startswith("/api/"):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Not authenticated"
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