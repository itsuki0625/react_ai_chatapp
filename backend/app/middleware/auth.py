import logging
import os
from fastapi import Request, HTTPException, status
from typing import Optional, Dict, Any, List
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response, JSONResponse
import json
from app.database.database import SessionLocal, AsyncSessionLocal
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import select
from app.models.user import User, UserRole, Role, RolePermission, Permission
from jose import jwt, jwe, JWTError
from datetime import datetime, timezone
from app.core.security import derived_key
from app.core.config import settings
import uuid

# ロガーの設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Define paths that do not require authentication
NO_AUTH_PATHS = [
    "/api/v1/docs",
    "/api/v1/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/signup",
    "/api/v1/auth/refresh-token",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password",
    "/api/v1/auth/verify-email",
    "/api/v1/auth/resend-verification",
    "/api/v1/subscriptions/stripe-plans",
    "/api/v1/subscriptions/webhook",
    "/api/auth/session",
]

# --- JWEトークンをデコードするヘルパー関数 --- << 削除
# async def decode_nextauth_token(token: str) -> Optional[Dict[str, Any]]:
#     ...
#     return None

# JWT デコード用のヘルパー (decode_nextauth_token とは別)
def decode_bearer_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(
            token,
            derived_key, # security.py からインポートしたキーを使用
            algorithms=[settings.JWT_ALGORITHM]
        )
        # 有効期限チェック
        if "exp" in payload and datetime.fromtimestamp(payload["exp"], timezone.utc) < datetime.now(timezone.utc):
             logger.warning("Bearer token has expired")
             return None
        return payload
    except JWTError as e:
        logger.error(f"Bearer token decoding/validation error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during Bearer token decoding: {str(e)}")
        return None

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        logger.debug(f"リクエストパス: {request.url.path}")

        # 認証不要パスのチェック
        if any(request.url.path.startswith(path) for path in NO_AUTH_PATHS):
            logger.debug(f"認証スキップパス: {request.url.path}")
            return await call_next(request)

        user = None
        # token_payload = None # Cookie関連なので削除
        # session_token = request.cookies.get("next-auth.session-token") # Cookie関連なので削除

        # --- Try Cookie Auth First (Using Async DB) --- << 削除
        # if session_token:
        #     logger.debug("next-auth.session-token Cookie found. Attempting to decode...")
        #     token_payload = await decode_nextauth_token(session_token)
        #     ...
        # else:
        #     logger.debug("next-auth.session-token Cookie not found. Checking Authorization header...")

        # --- Try Bearer Token --- # 削除: if not user: の条件も不要になる
        # if not user:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            bearer_token = auth_header.split(" ")[1]
            logger.debug("Bearer token found. Attempting to decode...")
            bearer_payload = decode_bearer_token(bearer_token)

            if bearer_payload:
                user_id_from_bearer = bearer_payload.get("sub")
                logger.debug(f"Decoded Bearer token payload: {bearer_payload}")
                if user_id_from_bearer:
                    logger.debug(f"ユーザーIDをBearerトークンから取得: {user_id_from_bearer}")
                    # Use async session directly
                    async with AsyncSessionLocal() as db:
                        try:
                            try:
                                user_uuid = uuid.UUID(user_id_from_bearer)
                            except ValueError:
                                logger.warning(f"Invalid UUID format in bearer token: {user_id_from_bearer}")
                                user_uuid = None

                            if user_uuid:
                                # Execute the async query
                                result = await db.execute(
                                    select(User)
                                    .options(
                                        selectinload(User.user_roles)
                                        .selectinload(UserRole.role)
                                        .selectinload(Role.role_permissions)
                                        .selectinload(RolePermission.permission)
                                    )
                                    .filter(User.id == user_uuid)
                                )
                                user = result.scalars().first()

                            if user:
                                logger.debug(f"DBからユーザー情報を取得 (Bearer): {user.email}")
                            else:
                                logger.warning(f"BearerトークンのユーザーID ({user_id_from_bearer}) がDBに見つかりません。")
                        except SQLAlchemyError as e:
                            logger.error(f"ユーザー情報取得中のデータベースエラー (Bearer): {e}")
                            user = None # Ensure user is None on DB error
                        except Exception as e:
                            logger.error(f"ユーザー情報取得中の予期せぬエラー (Bearer): {e}")
                            user = None # Ensure user is None on other errors
                else:
                    logger.warning("BearerトークンペイロードにユーザーID (sub) が含まれていません。")
            else:
                logger.warning("無効な Bearer token")
        else:
            logger.debug("Authorization Bearer header not found.")

        # --- Final Authentication Check and State Setting --- #
        if user:
            request.state.user_id = str(user.id) # Set user_id as string
            logger.debug(f"認証成功: User ID {request.state.user_id}, Email: {user.email}")
            try:
                response = await call_next(request)
                return response
            except Exception as e:
                logger.error(f"認証ミドルウェアの後続処理でエラー: {str(e)}", exc_info=True)
                detail_message = str(e)
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                if isinstance(e, HTTPException):
                    detail_message = e.detail
                    status_code = e.status_code
                return JSONResponse(
                    status_code=status_code,
                    content={"detail": detail_message}
                )
        else:
            logger.error(f"認証失敗: {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "認証が必要です"},
                headers={"WWW-Authenticate": "Bearer"} # Add header for 401
            )

        # レスポンスヘッダーのログ出力
        logger.debug(f"レスポンスヘッダー: {response.headers}")
        
        return response 