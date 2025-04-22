from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Any
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.crud.user import get_user_by_email, create_user, get_user
from app.crud.token import add_token_to_blacklist, is_token_blacklisted, remove_expired_tokens
from app.api.deps import get_db
from app.schemas.auth import (
    LoginResponse, SignUpRequest, EmailVerificationRequest, 
    ForgotPasswordRequest, ResetPasswordRequest,
    TwoFactorSetupResponse, TwoFactorVerifyRequest, RefreshTokenRequest,
    Token
)
from app.api.deps import get_current_user, User
from app.services.email import send_verification_email, send_password_reset_email
from app.models.enums import TokenBlacklistReason
import uuid
import pyotp
import qrcode
import io
import base64
from fastapi.responses import JSONResponse
import logging
from datetime import datetime, timedelta

router = APIRouter()

# ログレベルを DEBUG に設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    try:
        logger.debug(f"ログイン試行: {form_data.username}")
        
        # ユーザー認証
        user = get_user_by_email(db, email=form_data.username)
        if not user or not verify_password(form_data.password, user.hashed_password):
            logger.warning(f"認証失敗: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="メールアドレスまたはパスワードが正しくありません",
            )
            
        logger.debug(f"認証成功: {form_data.username}")
        
        # リクエストヘッダーの確認
        logger.debug(f"リクエストヘッダー: {{request.headers}}")

        # プライマリロールを取得
        primary_user_role = next((ur for ur in user.user_roles if ur.is_primary), None)
        
        if not primary_user_role:
            logger.error(f"ユーザー {form_data.username} にプライマリロールが設定されていません")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ユーザーロールの設定に問題があります",
            )
        
        # ロール権限を取得
        # RolePermission をロードしておく必要がある場合がある
        # 例: db.options(joinedload(User.user_roles).joinedload(UserRole.role).joinedload(Role.role_permissions))
        #    .filter(User.email == form_data.username).first()
        role_permissions = [rp.permission.name for rp in primary_user_role.role.role_permissions if rp.is_granted]
        
        # セッション情報をクリア
        request.session.clear()
        
        # セッションにユーザー情報を保存
        request.session["user_id"] = str(user.id)
        request.session["email"] = user.email
        request.session["role"] = role_permissions # 権限名のリストを保存
        
        # 現在のセッション情報をログ出力
        logger.debug(f"セッション情報: {{dict(request.session)}}")
        
        # セッションミドルウェアがクッキー設定を自動的に行うので、
        # カスタムのクッキー設定は削除
        
        # レスポンスヘッダー設定
        response.headers["X-Auth-Status"] = "success"

        logger.debug(f"ログイン完了: {form_data.username}")
        
        # トークン生成 (アクセストークンとリフレッシュトークン)
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        # トークンに含めるデータ (ユーザーIDとロール/権限情報)
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "roles": role_permissions,  # ロール名ではなく権限名のリスト
            "name": user.full_name # ユーザー名をトークンに追加
        }
        
        access_token = create_access_token(
            data=token_data, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}, expires_delta=refresh_token_expires
        )

        # レスポンスをLoginResponseモデルに合わせて返す
        return LoginResponse(
            user={
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": role_permissions # 権限名のリストを返す
            },
            token=Token(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=int(access_token_expires.total_seconds())
            )
        )
    except Exception as e:
        logger.error(f"ログインエラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/logout")
async def logout(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    ログアウト処理。セッションをクリアし、現在のアクセストークンをブラックリストに追加します。
    """
    try:
        # ユーザーIDを取得
        user_id = request.session.get("user_id")
        
        # Authorization ヘッダーからトークンを取得
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            
            # トークンをデコード
            payload = decode_token(token)
            if payload and "jti" in payload and "exp" in payload:
                # トークンをブラックリストに追加
                add_token_to_blacklist(
                    db=db,
                    token_jti=payload["jti"],
                    user_id=user_id,
                    expires_at=datetime.fromtimestamp(payload["exp"]),
                    reason=TokenBlacklistReason.LOGOUT
                )
                logger.info(f"トークン {payload['jti']} をブラックリストに追加しました")
        
        # 定期的に期限切れのトークンをクリーンアップ
        # 本番環境では、スケジュールタスクで実行することを推奨
        try:
            deleted_count = remove_expired_tokens(db)
            logger.info(f"{deleted_count} 件の期限切れトークンを削除しました")
        except Exception as e:
            logger.error(f"期限切れトークンの削除に失敗しました: {str(e)}")
        
        # セッションをクリア
        request.session.clear()
        
        return {"message": "正常にログアウトしました"}
    except Exception as e:
        logger.error(f"ログアウトエラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/me", response_model=dict)
async def read_users_me(
    request: Request,
    # db: Session = Depends(get_db) # DBアクセスは不要になる可能性
) -> Any:
    """
    現在のユーザー情報を取得 (セッション情報から)
    """
    logger.debug(f"/me エンドポイント セッション情報確認: {dict(request.session)}")
    logger.debug(f"/me エンドポイント クッキー情報確認: {request.cookies}")

    # セッションにユーザー情報があるか確認
    user_id = request.session.get("user_id")
    email = request.session.get("email")
    # セッションからロール情報（権限リスト）を取得
    role_permissions = request.session.get("role")

    if not user_id or not email or not role_permissions:
        # 認証ミドルウェアを通過しているはずなので、基本的にはここには来ない想定
        logger.error("認証されているはずのユーザーのセッション情報が不完全です")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="セッション情報が無効です。再ログインしてください。"
        )

    # role_permissions がリストであることを確認（念のため）
    if not isinstance(role_permissions, list):
        logger.warning(f"セッション内のロール情報がリスト形式ではありません: {role_permissions}")
        # リスト形式でなければエラーとするか、デフォルト値を設定するか検討
        # ここではエラーとする例
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="セッション内のユーザーロール形式が無効です。"
        )

    logger.debug(f"/me エンドポイント 成功: user_id={user_id}, email={email}, roles={role_permissions}")

    # セッション情報をレスポンスとして返す
    return {
        "id": user_id, # フロントエンドの期待に合わせてキー名を 'id' に変更
        "email": email,
        "role": role_permissions # 権限名のリストを返す
        # "full_name" はセッションにないので、必要なら別途取得するか、
        # ログイン時やミドルウェアでセッションに追加する
    }

@router.get("/test-auth", response_model=dict)
async def test_auth(current_user: User = Depends(get_current_user)):
    """
    認証テスト用エンドポイント
    """
    return {
        "message": "認証成功",
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role.name
        }
    }

@router.post("/signup", response_model=dict)
async def signup(
    request: Request,
    user_data: SignUpRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    新規ユーザー登録
    """
    try:
        print("user_data : ", user_data)
        # メールアドレスの重複チェック
        existing_user = get_user_by_email(db, email=user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # パスワードのハッシュ化
        hashed_password = get_password_hash(user_data.password)
        
        # ユーザーの作成
        user = create_user(
            db=db,
            email=user_data.email,
            password=hashed_password,
            full_name=user_data.name,
        )
        print("user : ", user)
        
        # セッションにユーザー情報を保存
        request.session["user_id"] = str(user.id)
        request.session["email"] = user.email
        request.session["role"] = user.role.permissions
        print("request.session : ", request.session)
        
        return {
            "message": "User created successfully",
            "user": {
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.permissions
            }
        }
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/user-settings", response_model=dict)
async def get_user_settings(
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """
    現在のユーザーの設定情報を取得
    """
    try:
        if "user_id" not in request.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="認証が必要です"
            )
        
        user_id = request.session["user_id"]
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません"
            )
        
        # ユーザー設定情報を取得
        # Note: 実際のプロジェクトでは、別のテーブルに設定情報を持たせることも検討
        return {
            "email": user.email,
            "full_name": user.full_name,
            "email_notifications": True,  # デフォルト値
            "browser_notifications": False,  # デフォルト値
            "theme": "light"  # デフォルト値
        }
    except Exception as e:
        logger.error(f"ユーザー設定取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/user-settings", response_model=dict)
async def update_user_settings(
    request: Request,
    settings_data: dict,
    db: Session = Depends(get_db)
) -> Any:
    """
    ユーザー設定を更新
    """
    try:
        if "user_id" not in request.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="認証が必要です"
            )
        
        user_id = request.session["user_id"]
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません"
            )
        
        # 名前の更新
        if "full_name" in settings_data:
            user.full_name = settings_data["full_name"]
        
        # TODO: 他の設定（通知設定など）は別テーブルで管理することを検討
        
        db.commit()
        
        return {
            "message": "設定を更新しました",
            "email": user.email,
            "full_name": user.full_name
        }
    except Exception as e:
        db.rollback()
        logger.error(f"ユーザー設定更新エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/delete-account", response_model=dict)
async def delete_account(
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """
    現在のユーザーアカウントを削除
    """
    try:
        if "user_id" not in request.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="認証が必要です"
            )
        
        user_id = request.session["user_id"]
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません"
            )
        
        # 関連するデータの削除（カスケード削除が設定されていない場合は手動で行う）
        # 例: db.query(関連テーブル).filter(関連テーブル.user_id == user_id).delete()
        
        # ユーザーの削除
        db.delete(user)
        db.commit()
        
        # セッションをクリア
        request.session.clear()
        
        return {
            "message": "アカウントが正常に削除されました"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"アカウント削除エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/change-password", response_model=dict)
async def change_password(
    request: Request,
    password_data: dict,
    db: Session = Depends(get_db)
) -> Any:
    """
    ユーザーのパスワードを変更
    """
    try:
        if "user_id" not in request.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="認証が必要です"
            )
        
        # 必須フィールドの確認
        if "current_password" not in password_data or "new_password" not in password_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="現在のパスワードと新しいパスワードが必要です"
            )
        
        # 新しいパスワードの検証
        if len(password_data["new_password"]) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="パスワードは8文字以上である必要があります"
            )
        
        # ユーザーの取得
        user_id = request.session["user_id"]
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません"
            )
        
        # 現在のパスワードを検証
        if not verify_password(password_data["current_password"], user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="現在のパスワードが正しくありません"
            )
        
        # 新しいパスワードのハッシュ化と保存
        hashed_password = get_password_hash(password_data["new_password"])
        user.hashed_password = hashed_password
        
        # ユーザーのすべてのアクティブトークンを無効化するためのコード
        # AuthorizationヘッダーからトークンJTIを取得
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            payload = decode_token(token)
            if payload and "jti" in payload:
                # 現在のトークンをブラックリストに追加
                try:
                    add_token_to_blacklist(
                        db=db,
                        token_jti=payload["jti"],
                        user_id=str(user.id),
                        expires_at=datetime.fromtimestamp(payload.get("exp")),
                        reason=TokenBlacklistReason.PASSWORD_CHANGE
                    )
                except Exception as e:
                    logger.error(f"トークンブラックリスト登録エラー: {str(e)}")
        
        db.commit()
        
        return {
            "message": "パスワードが正常に変更されました"
        }
    except HTTPException:
        # 既知のHTTPExceptionはそのまま再発生
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"パスワード変更エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/refresh-token", response_model=dict)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    リフレッシュトークンを使用して新しいアクセストークンを取得
    """
    try:
        # リフレッシュトークンを検証
        payload = decode_token(refresh_data.refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無効なリフレッシュトークンです"
            )
        
        # トークンからユーザー情報を取得
        user_id = payload.get("sub")
        jti = payload.get("jti")
        
        if not user_id or not jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="トークンの形式が不正です"
            )
        
        # ブラックリストのチェック
        if is_token_blacklisted(db, jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="このトークンは無効化されています"
            )
        
        # ユーザーの存在確認
        user = get_user(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません"
            )
        
        # 新しいトークンペアを生成
        access_token = create_access_token(data={"sub": str(user.id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # 古いリフレッシュトークンをブラックリストに追加
        try:
            add_token_to_blacklist(
                db=db,
                token_jti=jti,
                user_id=user_id,
                expires_at=datetime.fromtimestamp(payload.get("exp")),
                reason=TokenBlacklistReason.MANUAL_REVOCATION
            )
            logger.info(f"使用済みリフレッシュトークン {jti} をブラックリストに追加しました")
        except Exception as e:
            logger.error(f"リフレッシュトークンのブラックリスト登録に失敗: {str(e)}")
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"リフレッシュトークンエラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/verify-email", response_model=dict)
async def verify_email(
    verification_data: EmailVerificationRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    メールアドレス検証トークンを検証
    """
    try:
        # トークンを検証
        payload = decode_token(verification_data.token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無効なトークンです"
            )
        
        # トークンタイプとメールアドレスを確認
        if payload.get("type") != "email_verification":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不正なトークンタイプです"
            )
        
        email = payload.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="トークンにメールアドレスが含まれていません"
            )
        
        # ユーザーを取得
        user = get_user_by_email(db, email=email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません"
            )
        
        # ユーザーのメール検証ステータスを更新
        user.is_verified = True
        db.commit()
        
        return {"message": "メールアドレスが検証されました"}
    except Exception as e:
        logger.error(f"メール検証エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/resend-verification", response_model=dict)
async def resend_verification(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Any:
    """
    メール検証リンクを再送信
    """
    try:
        # セッションからユーザーIDを取得
        if "user_id" not in request.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="認証が必要です"
            )
        
        user_id = request.session["user_id"]
        user = get_user(db, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません"
            )
        
        # すでに検証済みの場合
        if user.is_verified:
            return {"message": "メールアドレスはすでに検証済みです"}
        
        # 検証メールを送信
        background_tasks.add_task(
            send_verification_email,
            user.email,
            user.full_name
        )
        
        return {"message": "検証メールを再送信しました"}
    except Exception as e:
        logger.error(f"検証メール再送信エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/forgot-password", response_model=dict)
async def forgot_password(
    forgot_data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Any:
    """
    パスワードリセットリンクを送信
    """
    try:
        # メールアドレスからユーザーを検索
        user = get_user_by_email(db, email=forgot_data.email)
        
        # セキュリティ上、ユーザーが存在しない場合でも同じメッセージを返す
        if not user:
            return {"message": "パスワードリセットリンクを送信しました（該当するアカウントが存在する場合）"}
        
        # パスワードリセットトークンを生成（24時間有効）
        reset_token = create_access_token(
            data={
                "sub": str(user.id),
                "type": "password_reset",
                "email": user.email
            },
            expires_delta=timedelta(hours=24)
        )
        
        # パスワードリセットメールを送信
        background_tasks.add_task(
            send_password_reset_email,
            user.email,
            user.full_name,
            reset_token
        )
        
        return {"message": "パスワードリセットリンクを送信しました"}
    except Exception as e:
        logger.error(f"パスワードリセットメール送信エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/reset-password", response_model=dict)
async def reset_password(
    reset_data: ResetPasswordRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    パスワードをリセット
    """
    try:
        # トークンを検証
        payload = decode_token(reset_data.token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無効なトークンです"
            )
        
        # トークンタイプとメールアドレスを確認
        if payload.get("type") != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不正なトークンタイプです"
            )
        
        email = payload.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="トークンにメールアドレスが含まれていません"
            )
        
        # ユーザーを取得
        user = get_user_by_email(db, email=email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません"
            )
        
        # パスワードをハッシュ化して更新
        hashed_password = get_password_hash(reset_data.new_password)
        user.hashed_password = hashed_password
        db.commit()
        
        return {"message": "パスワードがリセットされました"}
    except Exception as e:
        logger.error(f"パスワードリセットエラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/setup-2fa", response_model=TwoFactorSetupResponse)
async def setup_2fa(
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """
    二要素認証のセットアップ
    """
    try:
        # セッションからユーザーIDを取得
        if "user_id" not in request.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="認証が必要です"
            )
        
        user_id = request.session["user_id"]
        user = get_user(db, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません"
            )
        
        # すでに二要素認証が有効な場合
        if user.is_2fa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="二要素認証はすでに有効です"
            )
        
        # 新しいTOTPシークレットを生成
        totp_secret = pyotp.random_base32()
        
        # シークレットをセッションに一時保存（検証後にDBに保存）
        request.session["temp_2fa_secret"] = totp_secret
        
        # QRコード用のプロビジョニングURIを生成
        provisioning_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(
            name=user.email,
            issuer_name="SmartAO"
        )
        
        return {
            "provisioning_uri": provisioning_uri,
            "secret": totp_secret
        }
    except Exception as e:
        logger.error(f"2FAセットアップエラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/verify-2fa", response_model=dict)
async def verify_2fa(
    request: Request,
    verify_data: TwoFactorVerifyRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    二要素認証の検証・有効化
    """
    try:
        # セッションからユーザーIDを取得
        if "user_id" not in request.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="認証が必要です"
            )
        
        # 一時保存したシークレットを取得
        if "temp_2fa_secret" not in request.session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FAのセットアップが完了していません"
            )
        
        user_id = request.session["user_id"]
        user = get_user(db, user_id)
        totp_secret = request.session["temp_2fa_secret"]
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません"
            )
        
        # TOTPコードを検証
        totp = pyotp.TOTP(totp_secret)
        if not totp.verify(verify_data.totp_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無効なTOTPコードです"
            )
        
        # 検証成功したらユーザーに2FAを有効化
        user.is_2fa_enabled = True
        user.totp_secret = totp_secret
        db.commit()
        
        # 一時保存したシークレットをセッションから削除
        del request.session["temp_2fa_secret"]
        
        return {"message": "二要素認証が有効化されました"}
    except Exception as e:
        logger.error(f"2FA検証エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/disable-2fa", response_model=dict)
async def disable_2fa(
    request: Request,
    verify_data: TwoFactorVerifyRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    二要素認証の無効化
    """
    try:
        # セッションからユーザーIDを取得
        if "user_id" not in request.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="認証が必要です"
            )
        
        user_id = request.session["user_id"]
        user = get_user(db, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません"
            )
        
        # 2FAが有効でない場合
        if not user.is_2fa_enabled or not user.totp_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="二要素認証は有効になっていません"
            )
        
        # 現在のTOTPシークレットでコードを検証
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(verify_data.totp_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無効なTOTPコードです"
            )
        
        # 二要素認証を無効化
        user.is_2fa_enabled = False
        user.totp_secret = None
        db.commit()
        
        return {"message": "二要素認証が無効化されました"}
    except Exception as e:
        logger.error(f"2FA無効化エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 