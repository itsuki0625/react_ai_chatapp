from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_async_db
from typing import Any
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.crud import crud_user
from app.crud.token import add_token_to_blacklist, is_token_blacklisted, remove_expired_tokens
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
from datetime import datetime, timedelta, date
from app.schemas.user import UserResponse, UserSettingsResponse, UserCreate
from app.crud import subscription as crud_subscription
from app.models.subscription import Subscription
from app.schemas.subscription import SubscriptionResponse
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from app.models.notification_setting import NotificationSetting

router = APIRouter()

# ログレベルを DEBUG に設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    try:
        logger.debug(f"ログイン試行: {form_data.username}")
        
        # ユーザー認証 (get_user_by_email はリレーションをロードしない)
        authenticated_user = await crud_user.get_user_by_email(db, email=form_data.username)
        
        # --- デバッグログ追加 ---
        if authenticated_user:
            logger.debug(f"ユーザー発見: {authenticated_user.email}, DBハッシュ: {authenticated_user.hashed_password}")
            password_match = verify_password(form_data.password, authenticated_user.hashed_password)
            logger.debug(f"パスワード検証結果 (verify_password): {password_match}")
        else:
            logger.debug(f"ユーザーが見つかりません: {form_data.username}")
            password_match = False # ユーザーがいなければ検証は False
        # --- デバッグログ追加ここまで ---
            
        if not authenticated_user or not password_match: # デバッグ用に検証結果変数を使用
            logger.warning(f"認証失敗: {form_data.username}")
            if authenticated_user: # ユーザーが存在する場合のみ失敗を記録
                 await crud_user.record_login_attempt(db=db, user_id=authenticated_user.id, success=False)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="メールアドレスまたはパスワードが正しくありません",
            )
            
        logger.debug(f"認証成功: {form_data.username}")
        
        # ★ 認証成功後、リレーションを含むユーザー情報を再取得
        # 新しいDBセッションで最新データを確実に取得
        await db.expire_all()  # セッションキャッシュをクリア
        user = await crud_user.get_user(db, user_id=authenticated_user.id)
        if not user: # 再取得に失敗した場合 (通常は起こらないはず)
            logger.error(f"認証成功ユーザー {authenticated_user.id} の情報再取得に失敗しました。")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ユーザー情報の取得に失敗しました。",
            )
        logger.info(f"User authenticated and re-fetched (with cache clear): {user.id if user else 'USER_NOT_FOUND_POST_AUTH'}")

        # 成功記録
        try:
            logger.info(f"Calling record_login_attempt for user_id: {user.id}")
            await crud_user.record_login_attempt(db=db, user_id=user.id, success=True)
            logger.info(f"Successfully called record_login_attempt for user_id: {user.id}")
        except Exception as e_record_login:
            logger.error(f"Error calling record_login_attempt for user_id: {user.id}: {e_record_login}", exc_info=True)
        
        # リクエストヘッダーの確認
        logger.debug(f"リクエストヘッダー: {{request.headers}}")

        # プライマリロールを取得 (Eager Loadingされた user オブジェクトを使用)
        primary_user_role = next((ur for ur in user.user_roles if ur.is_primary), None)
        
        if not primary_user_role:
            logger.error(f"ユーザー {form_data.username} にプライマリロールが設定されていません")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ユーザーロールの設定に問題があります",
            )
        
        # ★ デバッグ用: ロール情報をログ出力
        logger.info(f"ログイン時のロール情報 - ユーザー: {user.email}, ロールID: {primary_user_role.role_id}, ロール名: {primary_user_role.role.name}")
        
        # ロール権限を取得 (Eager Loadingされているはず)
        role_permissions = [rp.permission.name for rp in primary_user_role.role.role_permissions if rp.is_granted]
        
        # ★ デバッグ用: 権限情報をログ出力
        logger.info(f"ログイン時の権限情報 - ユーザー: {user.email}, 権限数: {len(role_permissions)}, 権限: {role_permissions}")
        
        # ★ デバッグ用: 全ロール情報を出力
        logger.info(f"ログイン時の全ロール情報 - ユーザー: {user.email}")
        for ur in user.user_roles:
            logger.info(f"  - ロール: {ur.role.name}, プライマリ: {ur.is_primary}, ID: {ur.role_id}")
        
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
        # primary_user_role と role_permissions はこのスコープで利用可能と仮定
        if not primary_user_role or not hasattr(primary_user_role, 'role') or not primary_user_role.role:
             logger.error(f"User {user.email} primary role object is missing or invalid.")
             # 適切なエラー処理 (例: HTTPException) をここで行うか、デフォルトロールを設定
             primary_role_name = "不明" # フォールバック
        else:
             primary_role_name = primary_user_role.role.name

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            # ★ 修正: rolesにはプライマリロール名（文字列）を設定
            "roles": [primary_role_name], # next-auth側が配列を期待している場合、配列に入れる
            # "role": primary_role_name, # 単一文字列の場合
            # ★ 修正: permissions クレームを追加して権限リストを設定
            "permissions": role_permissions,
            "name": user.full_name, # ユーザー名をトークンに追加
            "status": user.status.value if user.status else None # ステータスも追加
        }
        
        access_token = create_access_token(
            data=token_data, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}, expires_delta=refresh_token_expires
        )

        # レスポンスをLoginResponseモデルに合わせて返す
        user_response_data = {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": primary_user_role.role.name, # ロール名を返す
            "status": user.status.value if user.status else None, # status を追加 (Enum の場合は .value)
            "grade": user.grade, # ★ grade を追加
            "prefecture": user.prefecture # ★ prefecture を追加
        }

        return LoginResponse(
            user=user_response_data, # 更新された辞書を使用
            token=Token(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=int(access_token_expires.total_seconds())
            )
        )
    except Exception as e:
        logger.error(f"ログインエラー: {str(e)}")
        logger.exception("Login error details:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    ログアウト処理。セッションをクリアし、現在のアクセストークンをブラックリストに追加します。
    """
    try:
        # Authorization ヘッダーからトークンを取得
        auth_header = request.headers.get("Authorization")
        token_blacklisted = False # トークンがブラックリストに追加されたかのフラグ

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")

            # トークンをデコード
            payload = decode_token(token)
            if payload and "jti" in payload and "exp" in payload and "sub" in payload: # 'sub' の存在も確認
                try:
                    # --- 修正: トークンからユーザーIDを取得 ---
                    user_uuid = uuid.UUID(payload["sub"])

                    # user_uuid が None でない場合のみブラックリストに追加 (UUID変換成功時)
                    await add_token_to_blacklist(
                        db=db,
                        token_jti=payload["jti"],
                        user_id=user_uuid, # トークンから取得したUUID型を渡す
                        expires_at=datetime.fromtimestamp(payload["exp"]),
                        reason=TokenBlacklistReason.LOGOUT
                    )
                    logger.info(f"トークン {payload['jti']} をブラックリストに追加しました (User: {user_uuid})")
                    token_blacklisted = True
                except ValueError:
                     logger.error(f"トークンから取得したユーザーID '{payload['sub']}' が無効なUUID形式です。")
                except Exception as e_blacklist: # ブラックリスト追加時のエラーハンドリング
                     logger.error(f"トークンのブラックリスト追加中にエラーが発生しました: {e_blacklist}")
            else:
                 logger.warning("デコードされたトークンに必要な情報 (jti, exp, sub) が不足しています。")

        # トークンがブラックリストに追加されなかった場合（例：ヘッダーがない、デコード失敗）でも警告を出す
        if not token_blacklisted:
             logger.warning("有効なBearerトークンが見つからなかったか、ブラックリストへの追加に失敗したため、トークンは無効化されていません。")

        # 定期的に期限切れのトークンをクリーンアップ
        # 本番環境では、スケジュールタスクで実行することを推奨
        try:
            deleted_count = await remove_expired_tokens(db)
            logger.info(f"{deleted_count} 件の期限切れトークンを削除しました")
        except Exception as e:
            logger.error(f"期限切れトークンの削除に失敗しました: {str(e)}")

        # セッションをクリア (これは維持)
        request.session.clear()

        return {"message": "正常にログアウトしました"}
    except Exception as e:
        logger.error(f"ログアウトエラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    現在の認証済みユーザー情報を取得
    """
    logger.debug(f"/me エンドポイント: ユーザー {current_user.email} の情報を取得します。")

    # current_user オブジェクトから直接情報を取得
    # get_current_user が User オブジェクトを返すため、チェックは不要

    # プライマリロールと権限を取得 (認証ミドルウェアと同様のロジック)
    primary_user_role = next((ur for ur in current_user.user_roles if ur.is_primary), None)
    role_permissions = []
    role_name = "不明" # デフォルト値
    if primary_user_role and primary_user_role.role:
        role_name = primary_user_role.role.name
        if primary_user_role.role.role_permissions:
             role_permissions = [
                 rp.permission.name for rp in primary_user_role.role.role_permissions if rp.is_granted
             ]
    else:
        logger.warning(f"ユーザー {current_user.email} のプライマリロールが見つからないか、ロール情報が不完全です。")
        # ロールが見つからない場合のエラーハンドリングが必要であれば追加

    logger.debug(f"/me エンドポイント 成功: user_id={current_user.id}, email={current_user.email}, role={role_name}, permissions={role_permissions}")

    # UserResponse スキーマに合わせてレスポンスを構築
    # UserResponse スキーマが role 名や permissions を持つように調整が必要な場合がある
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        status=current_user.status,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        # UserResponse スキーマに合わせて role や permissions を追加・調整
        role=role_name, # 例: プライマリロール名
        # permissions=role_permissions # 例: 権限リスト (スキーマにあれば)
        # 必要に応じて他のフィールドも追加
        is_verified=current_user.is_verified
    )

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
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    新規ユーザー登録
    """
    try:
        print("user_data : ", user_data)
        # メールアドレスの重複チェック
        existing_user = await crud_user.get_user_by_email(db, email=user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # パスワードのハッシュ化
        hashed_password = get_password_hash(user_data.password)
        
        # ユーザーの作成 (UserCreate スキーマを使用して呼び出し)
        user_create_schema = UserCreate(
            email=user_data.email,
            password=user_data.password, # ハッシュ化前のパスワードを渡す (create_user内でハッシュ化されるため)
            full_name=user_data.full_name
            # 必要に応じて role や status も設定 (UserCreate の定義による)
            # role=user_data.role, 
            # status=user_data.status,
        )
        user = await crud_user.create_user(
            db=db,
            user_in=user_create_schema # UserCreate オブジェクトを渡す
        )
        print("user : ", user)
        
        # セッションにユーザー情報を保存
        request.session["user_id"] = str(user.id)
        request.session["email"] = user.email
        # 正しくロールと権限を取得する
        primary_user_role = next((ur for ur in user.user_roles if ur.is_primary), None)
        role_permissions = []
        role_name = "不明" # デフォルト
        if primary_user_role and primary_user_role.role:
            role_name = primary_user_role.role.name
            # role_permissions 属性は Role モデルで定義されている関連プロパティを想定
            if hasattr(primary_user_role.role, 'role_permissions'): 
                role_permissions = [rp.permission.name for rp in primary_user_role.role.role_permissions if rp.is_granted]
            else:
                 logger.warning(f"Role object for {role_name} does not have expected 'role_permissions' attribute.")

        request.session["role"] = role_permissions # セッションには権限リストを保存
        print("request.session : ", request.session)
        
        return {
            "message": "User created successfully",
            "user": {
                "email": user.email,
                "full_name": user.full_name,
                "role": role_name # レスポンスにはロール名を返す
            }
        }
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/user-settings", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    現在のユーザーの設定情報とサブスクリプション情報を取得
    """
    logger.info(f"ユーザー設定取得リクエスト 開始: {current_user.email}")
    try:
        # 通知設定を取得
        stmt = select(NotificationSetting).filter(NotificationSetting.user_id == current_user.id)
        result = await db.execute(stmt)
        notification_settings = result.scalars().all()

        # 通知設定をマッピング (初期化を少し変更)
        default_quiet_hours = {"start": None, "end": None}
        notification_map = {
            "SYSTEM_ANNOUNCEMENT": {"enabled": True, "quiet_hours": default_quiet_hours.copy()},
            "CHAT_MESSAGE": {"enabled": True, "quiet_hours": default_quiet_hours.copy()},
            "DOCUMENT_DEADLINE": {"enabled": True, "quiet_hours": default_quiet_hours.copy()}
        }

        system_announcement_setting = None
        for setting in notification_settings:
            # quiet_hours の処理を改善
            current_quiet_hours = default_quiet_hours.copy()
            if setting.quiet_hours_start:
                current_quiet_hours["start"] = setting.quiet_hours_start.strftime("%H:%M")
            if setting.quiet_hours_end:
                current_quiet_hours["end"] = setting.quiet_hours_end.strftime("%H:%M")
            
            notification_map[setting.notification_type] = {
                "enabled": setting.email_enabled or setting.push_enabled or setting.in_app_enabled,
                "quiet_hours": current_quiet_hours
            }
            if setting.notification_type == "SYSTEM_ANNOUNCEMENT":
                system_announcement_setting = setting # SYSTEM_ANNOUNCEMENT の設定を保持

        # Fetch subscription
        logger.info("Subscription 取得開始")
        stmt = select(Subscription).filter(Subscription.user_id == current_user.id, Subscription.is_active == True)
        result = await db.execute(stmt)
        subscription = result.scalars().first()
        logger.info(f"Subscription 取得完了: {subscription.id if subscription else 'None'}")

        # Prepare response data
        logger.info("レスポンスデータ準備開始")
        sub_data = None
        if subscription:
            try:
                sub_response_obj = SubscriptionResponse.from_orm(subscription)
                logger.info(f"SubscriptionResponse.from_orm 成功")
                sub_data = sub_response_obj.dict()
                logger.info(f"Subscription データ変換 (.dict()) 完了")
            except Exception as conversion_error:
                logger.error(f"SubscriptionResponse 変換エラー: {str(conversion_error)}", exc_info=True)
                raise HTTPException(status_code=500, detail="Subscription data conversion failed.")

        # quiet_hours_start と quiet_hours_end を SYSTEM_ANNOUNCEMENT の設定から取得
        # フロントエンドが空文字列を期待する場合に備えて、None の場合は空文字列にする
        quiet_hours_start_str = "" 
        quiet_hours_end_str = ""

        if system_announcement_setting and system_announcement_setting.quiet_hours_start:
            quiet_hours_start_str = system_announcement_setting.quiet_hours_start.strftime("%H:%M")
        
        if system_announcement_setting and system_announcement_setting.quiet_hours_end:
            quiet_hours_end_str = system_announcement_setting.quiet_hours_end.strftime("%H:%M")
        
        # email_notifications と browser_notifications は、SYSTEM_ANNOUNCEMENT の設定に基づいて決定する
        # (あるいは、全般的な設定として別途フラグを持つか、要件に応じて変更)
        email_notifications_enabled = False
        browser_notifications_enabled = False
        if system_announcement_setting:
            email_notifications_enabled = system_announcement_setting.email_enabled
            browser_notifications_enabled = system_announcement_setting.push_enabled
        # もし system_announcement_setting がない場合でも、他の通知タイプの設定から集約するロジックが必要ならここに追加
        # 例: email_notifications_enabled = any(s.email_enabled for s in notification_settings)

        settings_response_data = {
            "email": current_user.email,
            "full_name": current_user.full_name,
            "profile_image_url": current_user.profile_image_url,
            "email_notifications": email_notifications_enabled,
            "browser_notifications": browser_notifications_enabled,
            "system_notifications": notification_map["SYSTEM_ANNOUNCEMENT"]["enabled"],
            "chat_notifications": notification_map["CHAT_MESSAGE"]["enabled"],
            "document_notifications": notification_map["DOCUMENT_DEADLINE"]["enabled"],
            "quiet_hours_start": quiet_hours_start_str,
            "quiet_hours_end": quiet_hours_end_str,
            "theme": current_user.theme or "light",
            "subscription": sub_data
        }
        logger.info("レスポンス基本データ準備完了")

        # Create final response model instance
        settings_response = UserSettingsResponse(**settings_response_data)
        logger.info("UserSettingsResponse インスタンス作成完了")

        return settings_response
    except AttributeError as ae:
        logger.error(f"属性エラー発生: {str(ae)}", exc_info=True)
        if "'AsyncSession' object has no attribute 'query'" in str(ae):
            logger.error("--> 同期クエリが呼び出された可能性が高いです。コードを確認してください。")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ユーザー設定の取得中に属性エラーが発生しました。"
        )
    except Exception as e:
        logger.error(f"その他のユーザー設定取得エラー: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ユーザー設定の取得中に予期せぬエラーが発生しました。"
        )

@router.put("/user-settings", response_model=dict)
async def update_user_settings(
    request: Request,
    settings_data: dict,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    ユーザー設定を更新
    """
    try:
        user = current_user

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません"
            )
        
        # 名前の更新
        if "name" in settings_data:
            user.name = settings_data["name"]
        
        # 通知設定の更新
        notification_types = {
            "systemNotifications": "SYSTEM_ANNOUNCEMENT",
            "chatNotifications": "CHAT_MESSAGE",
            "documentNotifications": "DOCUMENT_DEADLINE"
        }

        for setting_key, notification_type in notification_types.items():
            if setting_key in settings_data:
                # 通知設定テーブルから該当する設定を取得または作成
                stmt = select(NotificationSetting).filter(
                    NotificationSetting.user_id == user.id,
                    NotificationSetting.notification_type == notification_type
                )
                result = await db.execute(stmt)
                notification_setting = result.scalars().first()
                
                if not notification_setting:
                    notification_setting = NotificationSetting(
                        id=uuid.uuid4(),
                        user_id=user.id,
                        notification_type=notification_type,
                        email_enabled=settings_data.get("emailNotifications", True),
                        push_enabled=settings_data.get("browserNotifications", False),
                        in_app_enabled=True
                    )
                    db.add(notification_setting)
                else:
                    notification_setting.email_enabled = settings_data.get("emailNotifications", True)
                    notification_setting.push_enabled = settings_data.get("browserNotifications", False)
                    notification_setting.in_app_enabled = True

        # 静かな時間帯の設定
        if "quietHoursStart" in settings_data or "quietHoursEnd" in settings_data or \
           settings_data.get("quietHoursStart") is None or settings_data.get("quietHoursEnd") is None: # Allow unsetting via null

            # Ensure notification_type is defined, using SYSTEM_ANNOUNCEMENT as a default or general type for quiet hours.
            # This might need adjustment if quiet hours can be set per notification type.
            target_notification_type = "SYSTEM_ANNOUNCEMENT" 

            stmt = select(NotificationSetting).filter(
                NotificationSetting.user_id == user.id,
                NotificationSetting.notification_type == target_notification_type
            )
            result = await db.execute(stmt)
            notification_setting = result.scalars().first()
            
            if not notification_setting:
                # If no specific setting exists, create one. 
                # This assumes quiet hours are global or tied to a default type.
                # Adjust email/push/in_app enabled flags as per application logic for new settings.
                notification_setting = NotificationSetting(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    notification_type=target_notification_type,
                    # Default booleans for a new setting, adjust as needed
                    email_enabled=settings_data.get("emailNotifications", True), 
                    push_enabled=settings_data.get("browserNotifications", False),
                    in_app_enabled=True 
                )
                db.add(notification_setting)
            
            dummy_date = date.min # Use a fixed, minimal date for date part.
            
            if "quietHoursStart" in settings_data:
                if settings_data["quietHoursStart"]:
                    try:
                        time_obj = datetime.strptime(settings_data["quietHoursStart"], "%H:%M").time()
                        notification_setting.quiet_hours_start = datetime.combine(dummy_date, time_obj)
                    except ValueError:
                        # Handle invalid time format string if necessary
                        notification_setting.quiet_hours_start = None 
                        logger.warning(f"Invalid format for quietHoursStart: {settings_data['quietHoursStart']}")
                else: # Handles empty string by setting to None
                    notification_setting.quiet_hours_start = None
            
            if "quietHoursEnd" in settings_data:
                if settings_data["quietHoursEnd"]:
                    try:
                        time_obj = datetime.strptime(settings_data["quietHoursEnd"], "%H:%M").time()
                        notification_setting.quiet_hours_end = datetime.combine(dummy_date, time_obj)
                    except ValueError:
                        # Handle invalid time format string
                        notification_setting.quiet_hours_end = None
                        logger.warning(f"Invalid format for quietHoursEnd: {settings_data['quietHoursEnd']}")
                else: # Handles empty string by setting to None
                    notification_setting.quiet_hours_end = None
        
        # テーマの更新
        if "theme" in settings_data:
            user.theme = settings_data["theme"]
        
        await db.commit()
        
        # レスポンスに更新後の情報を反映
        return {
            "message": "設定を更新しました",
            "email": user.email,
            "name": user.name,
            "emailNotifications": settings_data.get("emailNotifications", True),
            "browserNotifications": settings_data.get("browserNotifications", False),
            "systemNotifications": settings_data.get("systemNotifications", True),
            "chatNotifications": settings_data.get("chatNotifications", True),
            "documentNotifications": settings_data.get("documentNotifications", True),
            "quietHoursStart": settings_data.get("quietHoursStart"),
            "quietHoursEnd": settings_data.get("quietHoursEnd"),
            "theme": settings_data.get("theme", "light")
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"ユーザー設定更新エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/delete-account", response_model=dict)
async def delete_account(
    request: Request,
    db: AsyncSession = Depends(get_async_db)
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
        
        user_uuid_str = request.session["user_id"]
        try:
             user_uuid = uuid.UUID(user_uuid_str)
        except ValueError:
             logger.error(f"セッション内のユーザーIDが無効な形式です: {user_uuid_str}")
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="無効なセッション情報です")

        user = await crud_user.get_user(db, user_uuid)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません"
            )
        
        removed_user = await crud_user.remove_user(db, user_id=user_uuid)
        if not removed_user:
             logger.error(f"ユーザー削除処理に失敗しました: User ID {user_uuid}")
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="アカウント削除処理中にエラーが発生しました")

        request.session.clear()

        return {
            "message": "アカウントが正常に削除されました"
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"アカウント削除エラー: {str(e)}")
        logger.exception("Account deletion error details:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="アカウント削除中にエラーが発生しました。"
        )

@router.post("/change-password", response_model=dict)
async def change_password(
    request: Request,
    password_data: dict,
    db: AsyncSession = Depends(get_async_db)
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
        user = await crud_user.get_user(db, user_id)
        
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
                    await add_token_to_blacklist(
                        db=db,
                        token_jti=payload["jti"],
                        user_id=str(user.id),
                        expires_at=datetime.fromtimestamp(payload.get("exp")),
                        reason=TokenBlacklistReason.PASSWORD_CHANGE
                    )
                except Exception as e:
                    logger.error(f"トークンブラックリスト登録エラー: {str(e)}")
        
        await db.commit()
        
        return {
            "message": "パスワードが正常に変更されました"
        }
    except HTTPException:
        # 既知のHTTPExceptionはそのまま再発生
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"パスワード変更エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/refresh-token", response_model=dict)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    アクセストークンをリフレッシュトークンを使用して更新します。
    """
    try:
        # リフレッシュトークンをデコード
        payload = decode_token(refresh_data.refresh_token)
        if not payload or "sub" not in payload or "jti" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無効なリフレッシュトークンです",
            )

        user_id = uuid.UUID(payload["sub"])
        token_jti = payload["jti"]
        expires_at = datetime.fromtimestamp(payload.get("exp")) # 有効期限取得

        # トークンがブラックリストに登録されているか確認
        if await is_token_blacklisted(db, token_jti=token_jti):
             logger.error(f"リフレッシュトークンエラー: 401: このトークンは無効化されています (is_token_blacklisted check)") # ★ エラーログ追加
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="このトークンは無効化されています", # ★ エラーメッセージ修正
            )

        # ユーザーが存在するか確認
        user = await crud_user.get_user(db, user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="ユーザーが見つかりません",
            )

        # --- ★ 修正: ブラックリスト追加処理を try...except で囲む ---
        try:
            # 古いリフレッシュトークンをブラックリストに追加
            await add_token_to_blacklist(
                db=db,
                token_jti=token_jti,
                user_id=user_id,
                expires_at=expires_at,
                reason=TokenBlacklistReason.MANUAL_REVOCATION # REFRESHED が適切かも
            )
            logger.info(f"使用済みリフレッシュトークン {token_jti} をブラックリストに追加しました")
        except IntegrityError: # sqlalchemy.exc.IntegrityError をインポートする必要がある場合あり
            # すでにブラックリストに存在する場合 (UniqueViolation)
            logger.warning(f"リフレッシュトークン {token_jti} はすでにブラックリストに存在します。")
            # ここで 401 エラーを発生させる (トークンは既に使用済み)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="このトークンは既に使用されているか無効化されています",
            )
        except Exception as e_blacklist:
             # その他のDBエラー
             logger.error(f"トークン {token_jti} のブラックリスト追加中に予期せぬDBエラー: {e_blacklist}")
             raise HTTPException(
                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                 detail="トークンの無効化処理中にエラーが発生しました。"
             )
        # --- ★ 修正ここまで ---

        # 新しいアクセストークンを生成
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        # ★ get_userでロードしたユーザー情報を使用
        primary_user_role = next((ur for ur in user.user_roles if ur.is_primary), None)
        if not primary_user_role or not primary_user_role.role:
             logger.error(f"User {user.email} primary role object is missing or invalid.")
             primary_role_name = "不明"
             role_permissions = [] # 権限も空にする
        else:
             primary_role_name = primary_user_role.role.name
             role_permissions = [rp.permission.name for rp in primary_user_role.role.role_permissions if rp.is_granted]

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "roles": [primary_role_name],
            "permissions": role_permissions,
            "name": user.full_name,
            "status": user.status.value if user.status else None
        }
        new_access_token = create_access_token(
            data=token_data, expires_delta=access_token_expires
        )

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds())
        }

    except HTTPException as http_exc: # 内部で発生したHTTPExceptionはそのまま再raise
        logger.error(f"リフレッシュトークン処理中のHTTPエラー: {http_exc.status_code}: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"リフレッシュトークン処理中に予期せぬエラー: {str(e)}")
        logger.exception("Refresh token error details:") # ★ スタックトレースも記録
        # ★ 予期せぬエラーのレスポンス
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="トークンのリフレッシュ中に予期せぬエラーが発生しました。"
            # detail=f"{type(e).__name__}: {str(e)}" # デバッグ用により詳細な情報を返すことも可能
        )

@router.post("/verify-email", response_model=dict)
async def verify_email(
    verification_data: EmailVerificationRequest,
    db: AsyncSession = Depends(get_async_db)
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
        user = await crud_user.get_user_by_email(db, email=email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません"
            )
        
        # ユーザーのメール検証ステータスを更新
        user.is_verified = True
        await db.commit()
        
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
    db: AsyncSession = Depends(get_async_db)
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
        user = await crud_user.get_user(db, user_id)
        
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
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    パスワードリセットリンクを送信
    """
    try:
        # メールアドレスからユーザーを検索
        user = await crud_user.get_user_by_email(db, email=forgot_data.email)
        
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
    db: AsyncSession = Depends(get_async_db)
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
        user = await crud_user.get_user_by_email(db, email=email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません"
            )
        
        # パスワードをハッシュ化して更新
        hashed_password = get_password_hash(reset_data.new_password)
        user.hashed_password = hashed_password
        await db.commit()
        
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
    db: AsyncSession = Depends(get_async_db)
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
        user = await crud_user.get_user(db, user_id)
        
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
    db: AsyncSession = Depends(get_async_db)
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
        user = await crud_user.get_user(db, user_id)
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
        await db.commit()
        
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
    db: AsyncSession = Depends(get_async_db)
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
        user = await crud_user.get_user(db, user_id)
        
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
        await db.commit()
        
        return {"message": "二要素認証が無効化されました"}
    except Exception as e:
        logger.error(f"2FA無効化エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 