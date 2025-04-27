import logging
import os
from fastapi import Request, HTTPException, status
from typing import Optional, Dict, Any, List
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response, JSONResponse
import json
from app.database.database import SessionLocal
from app.crud.user import get_user
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload, selectinload
from app.models.user import User, UserRole, Role, RolePermission, Permission
from jose import jwt, jwe, JWTError
from datetime import datetime, timezone
from app.core.security import derived_key, JWT_ALGORITHM

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
]

# --- JWEトークンをデコードするヘルパー関数 ---
async def decode_nextauth_token(token: str) -> Optional[Dict[str, Any]]:
    """
    NextAuthのJWEトークンをデコード・検証する。
    """
    decrypted_token_bytes = None
    try:
        # JWEを復号
        decrypted_token_bytes = jwe.decrypt(token, derived_key)
        logger.debug("JWE decryption successful.") # デバッグログ追加
    except Exception as e: # JWE関連のエラーを包括的に捕捉
        logger.error(f"JWE decryption error: {str(e)} (Error type: {type(e).__name__})")
        return None

    if not decrypted_token_bytes:
        return None

    try:
        # 復号された中身 (JWT) をデコード・検証
        payload = jwt.decode(
            decrypted_token_bytes.decode('utf-8'),
            derived_key, # JWEと同じ導出キーを使用
            algorithms=[JWT_ALGORITHM] # HS512 アルゴリズムを使用
        )
        logger.debug("JWT decoding successful.") # デバッグログ追加

        # 有効期限 (exp) のチェック
        if "exp" in payload and datetime.fromtimestamp(payload["exp"], timezone.utc) < datetime.now(timezone.utc):
             logger.warning("Token has expired")
             return None
        return payload
    except JWTError as e: # JWTのデコード/検証エラーは JWTError で捕捉
        logger.error(f"JWT decoding/validation error: {str(e)}")
        return None
    except Exception as e: # その他の予期せぬエラー
        logger.error(f"Unexpected error during JWT decoding: {str(e)}")
        return None

# JWT デコード用のヘルパー (decode_nextauth_token とは別)
def decode_bearer_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(
            token,
            derived_key, # security.py からインポートしたキーを使用
            algorithms=[JWT_ALGORITHM]
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
        logger.debug(f"リクエストクッキー: {request.cookies}") # ヘッダーログは冗長なので削除

        # 認証不要パスのチェック
        if any(request.url.path.startswith(path) for path in NO_AUTH_PATHS):
            logger.debug(f"認証スキップパス: {request.url.path}")
            return await call_next(request)

        user = None
        token_payload = None
        session_token = request.cookies.get("next-auth.session-token") # NextAuthのCookie名

        if session_token:
            logger.debug("next-auth.session-token Cookie found. Attempting to decode...")
            token_payload = await decode_nextauth_token(session_token)

            if token_payload:
                user_id_from_token = token_payload.get("sub") # NextAuthはsubにIDを入れる
                logger.debug(f"Decoded token payload: {token_payload}")
                if user_id_from_token:
                    logger.debug(f"ユーザーIDをトークンから取得: {user_id_from_token}")
                    try:
                        with SessionLocal() as db:
                            user = (
                                db.query(User)
                                .options(
                                    selectinload(User.user_roles)
                                    .selectinload(UserRole.role)
                                    .selectinload(Role.role_permissions)
                                    .selectinload(RolePermission.permission)
                                )
                                .filter(User.id == user_id_from_token)
                                .first()
                            )
                            if user:
                                logger.debug(f"DBからユーザー情報を取得: {user.email}")
                            else:
                                logger.warning(f"トークンのユーザーID ({user_id_from_token}) がDBに見つかりません。")
                    except SQLAlchemyError as e:
                        logger.error(f"ユーザー情報取得中のデータベースエラー: {str(e)}")
                        user = None # エラー時は認証失敗とする
                    except Exception as e:
                         logger.error(f"ユーザー情報取得中の予期せぬエラー: {str(e)}")
                         user = None # エラー時は認証失敗とする
                else:
                    logger.warning("トークンペイロードにユーザーID (sub) が含まれていません。")
            else:
                logger.warning("無効な next-auth.session-token Cookie")
        else:
            logger.debug("next-auth.session-token Cookie not found. Checking Authorization header...")

        # --- 追加: Cookie認証失敗時に Bearer トークンを試す ---
        if not user:
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
                        try:
                             with SessionLocal() as db:
                                user = (
                                    db.query(User)
                                    .options(
                                        selectinload(User.user_roles)
                                        .selectinload(UserRole.role)
                                        .selectinload(Role.role_permissions)
                                        .selectinload(RolePermission.permission)
                                    )
                                    .filter(User.id == user_id_from_bearer)
                                    .first()
                                )
                                if user:
                                    logger.debug(f"DBからユーザー情報を取得 (Bearer): {user.email}")
                                else:
                                    logger.warning(f"BearerトークンのユーザーID ({user_id_from_bearer}) がDBに見つかりません。")
                        except SQLAlchemyError as e:
                            logger.error(f"ユーザー情報取得中のデータベースエラー (Bearer): {str(e)}")
                        except Exception as e:
                            logger.error(f"ユーザー情報取得中の予期せぬエラー (Bearer): {str(e)}")
                    else:
                        logger.warning("BearerトークンペイロードにユーザーID (sub) が含まれていません。")
                else:
                    logger.warning("無効な Bearer token")
            else:
                logger.debug("Authorization Bearer header not found.")

        # 認証チェック
        if user:
            request.state.user_id = user.id # Userオブジェクトの代わりにユーザーIDを格納
            logger.debug(f"認証成功: User ID {user.id}, Email: {user.email}")
            try:
                response = await call_next(request)
                return response
            except Exception as e:
                # エラー発生時のデバッグログは一旦コメントアウト（必要なら戻す）
                # user_in_state = getattr(request.state, "user", "Not Set")
                logger.error(f"認証ミドルウェアの後続処理でエラー: {str(e)}")
                # logger.error(f"エラー発生時の request.state.user: {user_in_state}")
                # logger.error(f"エラー発生時の request.state.user の型: {type(user_in_state)}")
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
            # 認証失敗
            logger.error(f"認証失敗: {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "認証が必要です"}
            )

        # レスポンスヘッダーのログ出力
        logger.debug(f"レスポンスヘッダー: {response.headers}")
        
        return response 