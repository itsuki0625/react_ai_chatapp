import logging
from fastapi import Request, HTTPException, status
from typing import Optional, Dict, Any, List
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
import json
from app.database.database import SessionLocal
from app.crud.user import get_user, get_user_by_email
from sqlalchemy.exc import SQLAlchemyError

# try-catchブロックでJWTの例外処理を追加
try:
    import jwt
    from jwt import PyJWTError
except ImportError:
    import warnings
    warnings.warn("PyJWTがインストールされていません。pip install PyJWTを実行してください。")
    # フォールバックとして最小限の機能を提供
    jwt = None
    PyJWTError = Exception

# ロガーの設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # リクエストパスをログに記録
        logger.debug(f"リクエストパス: {request.url.path}")
        logger.debug(f"リクエストヘッダー: {request.headers}")
        
        # 認証が不要なパスをスキップ
        if request.url.path in [
            "/api/v1/auth/login",
            "/api/v1/auth/logout",
            "/api/v1/auth/signup",
            "/api/v1/docs",
            "/openapi.json",
            "/api/v1/subscriptions/stripe-plans",  # 公開プラン情報
            "/api/v1/subscriptions/verify-campaign-code",  # キャンペーンコード検証（オプショナル認証）
            "/",  # ルートパス
            # NextAuth が使用するパス
            "/api/auth/session",
            "/api/auth/csrf",
            "/api/auth/signout",
            "/api/auth/callback",
            # "/api/v1/chat/stream",
            # "/api/v1/chat/sessions",
            # "/api/v1/chat/sessions/{session_id}/messages"
        ]:
            logger.debug(f"認証スキップパス: {request.url.path}")
            return await call_next(request)

        try:
            # クッキーの確認
            cookies = request.cookies
            logger.debug(f"リクエストクッキー: {cookies}")
            
            # Authorizationヘッダーからトークンを抽出
            auth_header = request.headers.get("Authorization")
            user_id_from_token = None
            
            if auth_header and auth_header.startswith("Bearer "):
                # Authorization: Bearer <token> 形式からトークンを取得
                token = auth_header.replace("Bearer ", "")
                user_id_from_token = token  # トークンがユーザーIDの場合
                logger.debug(f"認証トークンからユーザーID取得: {user_id_from_token}")
            
            # セッションがない場合は作成
            if not hasattr(request, "session"):
                request.session = {}
            
            # セッション内容を詳細にログ出力
            try:
                session_data = dict(request.session) if hasattr(request, "session") else {}
                logger.debug(f"セッション詳細: {json.dumps(session_data, ensure_ascii=False)}")
            except Exception as e:
                logger.error(f"セッションのログ出力中にエラー: {str(e)}")
            
            # NextAuth.jsのセッショントークンとセッションヘッダーをチェック
            next_auth_token = cookies.get("next-auth.session-token")
            session_token_header = request.headers.get("X-Session-Token")
            
            # NextAuthのセッションが存在し、X-Session-Tokenヘッダーが設定されている場合は信頼する
            if next_auth_token and session_token_header == "true" and "user_id" not in request.session:
                logger.debug("NextAuth.jsセッションとX-Session-Tokenヘッダーを検出しました")
                
                # フロントエンドからのリクエストにユーザーIDを含める場合
                user_email = request.headers.get("X-User-Email")
                if user_email:
                    try:
                        db = SessionLocal()
                        try:
                            user = get_user_by_email(db, email=user_email)
                            if user:
                                request.session["user_id"] = str(user.id)
                                request.session["email"] = user.email
                                role_permissions = user.role.permissions
                                if isinstance(role_permissions, str):
                                    role_permissions = [role_permissions]
                                request.session["role"] = role_permissions
                                logger.info(f"X-User-Emailヘッダーからユーザー認証に成功しました: {user_email}")
                            else:
                                # メールから見つからない場合は仮のユーザーIDを設定
                                logger.warning(f"メールアドレス {user_email} のユーザーが見つかりません")
                                request.session["user_id"] = "temporary_user_id"
                                request.session["email"] = user_email
                                request.session["role"] = ["user"]
                        finally:
                            db.close()
                    except Exception as e:
                        logger.error(f"X-User-Email処理エラー: {str(e)}")
                else:
                    # NextAuthのセッションが存在し、X-Session-Tokenが設定されているが、
                    # X-User-Emailがない場合はデモユーザーとして扱う
                    logger.debug("NextAuthセッションからデモユーザーとして処理します")
                    request.session["user_id"] = "demo_user_id"
                    request.session["email"] = "demo@example.com"
                    request.session["role"] = ["user"]
            
            # Authorization ヘッダーからユーザーIDを設定（セッションより優先）
            if user_id_from_token:
                if "user_id" not in request.session or request.session["user_id"] != user_id_from_token:
                    logger.debug(f"Authorizationヘッダーからユーザー情報を設定: {user_id_from_token}")
                    
                    # データベースからユーザー情報を取得
                    try:
                        db = SessionLocal()
                        user = get_user(db, user_id_from_token)
                        
                        if user:
                            request.session["user_id"] = str(user.id)
                            request.session["email"] = user.email
                            # ロールはリスト形式で保存
                            role_permissions = user.role.permissions
                            if isinstance(role_permissions, str):
                                role_permissions = [role_permissions]
                            request.session["role"] = role_permissions
                            logger.debug(f"DBからユーザー情報を取得しました: {user.email}")
                        else:
                            logger.warning(f"ユーザーID: {user_id_from_token} のユーザーが見つかりません")
                            # トークンが無効な場合でも、一時的に識別可能にするためにuser_idだけはセットする
                            request.session["user_id"] = user_id_from_token
                    except SQLAlchemyError as e:
                        logger.error(f"データベースエラー: {str(e)}")
                    finally:
                        db.close()
            
            # /me エンドポイント用の特別な処理
            if request.url.path.startswith("/api/v1/auth/me"):
                if "user_id" not in request.session:
                    if user_id_from_token:
                        # Authorizationヘッダーからの情報を既に設定済み
                        pass
                    elif "session" in cookies:
                        logger.debug("クッキーからセッション情報を復元しようとしています")
                        # セッション情報を仮設定（デモ用）
                        request.session["user_id"] = "demo_user_id"
                        request.session["email"] = "demo@example.com"
                        request.session["role"] = ["user"]
                    else:
                        # 認証情報がない場合はエラー
                        logger.error("認証情報が見つかりません")
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="認証が必要です"
                        )
            
            # APIエンドポイントの場合は認証を必須にする
            elif request.url.path.startswith("/api/") and "user_id" not in request.session:
                logger.warning("user_idがセッションにありません")
                # 認証が必要なAPIパスでセッションがない場合はエラー
                if not request.url.path.startswith("/api/v1/auth/") and not request.url.path.startswith("/api/auth/"):
                    logger.error(f"保護されたAPIパス {request.url.path} へのアクセスが認証なしで拒否されました")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="認証が必要です"
                    )

            # 次のミドルウェアまたはエンドポイントを呼び出す
            response = await call_next(request)
            
            # レスポンスヘッダーのログ出力
            logger.debug(f"レスポンスヘッダー: {response.headers}")
            
            # CORS対応のための追加ヘッダー（開発環境のみ）
            if request.headers.get("origin") and "localhost" in request.headers.get("origin", ""):
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin")
            
            return response

        except Exception as e:
            logger.error(f"認証ミドルウェアエラー: {str(e)}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            ) 