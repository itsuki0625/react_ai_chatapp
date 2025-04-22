import logging
from fastapi import Request, HTTPException, status
from typing import Optional, Dict, Any, List
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response, JSONResponse
import json
from app.database.database import SessionLocal
from app.crud.user import get_user, get_user_by_email
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload, selectinload
from app.models.user import User, UserRole, Role, RolePermission, Permission
from app.core.security import decode_token
from jose import JWTError

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
]

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # リクエストパスをログに記録
        logger.debug(f"リクエストパス: {request.url.path}")
        logger.debug(f"リクエストヘッダー: {request.headers}")
        logger.debug(f"リクエストクッキー: {request.cookies}")

        # 認証不要パスのチェック
        if any(request.url.path.startswith(path) for path in NO_AUTH_PATHS):
            logger.debug(f"認証スキップパス: {request.url.path}")
            return await call_next(request)

        user_id_from_token = None
        token_payload = None
        auth_header = request.headers.get("Authorization")

        # Authorization ヘッダーからトークンを検証
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            try:
                token_payload = decode_token(token)
                if token_payload:
                    user_id_from_token = token_payload.get("sub")
                    # TODO: ブラックリストチェックをここで行うか検討
                    # with get_db_session() as db:
                    #     if is_token_blacklisted(db, token_payload.get("jti")):
                    #         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
                    logger.debug(f"認証トークンからユーザーID取得: {user_id_from_token}")
                else:
                    logger.warning("無効な認証トークン")
            except JWTError as e:
                logger.error(f"JWTエラー: {str(e)}")
            except Exception as e:
                logger.error(f"トークンデコード中の予期せぬエラー: {str(e)}")

        # セッション情報を確認
        session_user_id = request.session.get("user_id")
        logger.debug(f"セッション詳細: {dict(request.session)}")

        # 認証処理
        authenticated = False
        if session_user_id:
            # セッション情報がある場合 -> 信頼する
            # TODO: セッションの有効期限チェックや再検証ロジックが必要な場合がある
            authenticated = True
            logger.debug(f"セッション認証成功: {session_user_id}")
        elif user_id_from_token:
            # セッションがなく、有効なトークンがある場合 -> セッションを再構築
            logger.debug(f"Authorizationヘッダーからユーザー情報を設定: {user_id_from_token}")
            try:
                with SessionLocal() as db: # Use context manager for session
                    # ユーザー情報を取得 (ロールと権限も一緒にロード)
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
                        primary_user_role = next((ur for ur in user.user_roles if ur.is_primary), None)
                        if primary_user_role and primary_user_role.role:
                            role_permissions = [
                                rp.permission.name
                                for rp in primary_user_role.role.role_permissions
                                if rp.is_granted
                            ]
                            request.session["user_id"] = str(user.id)
                            request.session["email"] = user.email
                            request.session["role"] = role_permissions # Use permission names
                            authenticated = True
                            logger.debug(f"DBからユーザー情報を取得しセッション設定: {user.email}, Roles: {role_permissions}")
                        else:
                            logger.warning(f"ユーザーID: {user_id_from_token} のプライマリロールが見つかりません")
                            # 認証失敗として扱うか、エラーとするか要検討
                    else:
                        logger.warning(f"ユーザーID: {user_id_from_token} のユーザーが見つかりません")
            except SQLAlchemyError as e:
                logger.error(f"データベースエラー: {str(e)}")
            except Exception as e:
                 logger.error(f"セッション再構築中の予期せぬエラー: {str(e)}")

        # 認証チェック
        if not authenticated:
            logger.error(f"認証失敗: {request.url.path}")
            # JSONレスポンスを返すように変更
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "認証が必要です"}
            )

        # 認証成功、次の処理へ
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"認証ミドルウェアの後続処理でエラー: {str(e)}")
            # エラー発生時もJSONレスポンスを返す
            detail_message = str(e)
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            if isinstance(e, HTTPException):
                detail_message = e.detail
                status_code = e.status_code
            
            return JSONResponse(
                status_code=status_code,
                content={"detail": detail_message}
            )

        # レスポンスヘッダーのログ出力
        logger.debug(f"レスポンスヘッダー: {response.headers}")
        
        # CORS対応のための追加ヘッダー（開発環境のみ）
        if request.headers.get("origin") and "localhost" in request.headers.get("origin", ""):
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin")
        
        return response 