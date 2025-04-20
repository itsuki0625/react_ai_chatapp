from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Any
from app.core.security import verify_password, get_password_hash
from app.crud.user import get_user_by_email, create_user, get_user
from app.api.deps import get_db
from app.schemas.auth import LoginResponse, SignUpRequest
from app.api.deps import get_current_user, User
from fastapi.responses import JSONResponse
import logging

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
        logger.debug(f"リクエストヘッダー: {request.headers}")
        
        # ユーザーのロールが文字列の場合はリストに変換
        role_permissions = user.role.permissions
        if isinstance(role_permissions, str):
            role_permissions = [role_permissions]
        
        # セッション情報をクリア
        request.session.clear()
        
        # セッションにユーザー情報を保存
        request.session["user_id"] = str(user.id)
        request.session["email"] = user.email
        request.session["role"] = role_permissions
        
        # 現在のセッション情報をログ出力
        logger.debug(f"セッション情報: {dict(request.session)}")
        
        # セッションミドルウェアがクッキー設定を自動的に行うので、
        # カスタムのクッキー設定は削除
        
        # レスポンスヘッダー設定
        response.headers["X-Auth-Status"] = "success"

        logger.debug(f"ログイン完了: {form_data.username}")
        
        return {
            "email": user.email,
            "full_name": user.full_name,
            "role": role_permissions  # リスト形式で返す
        }
    except Exception as e:
        logger.error(f"ログインエラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=dict)
async def read_users_me(
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """
    現在のユーザー情報を取得
    """
    logger.debug(f"セッション情報確認: {dict(request.session)}")
    logger.debug(f"クッキー情報確認: {request.cookies}")
    
    # セッションにユーザーIDがない場合、デモユーザーを返す（開発用）
    if "user_id" not in request.session:
        if "session" in request.cookies:
            # クッキーからセッション情報を復元する試み（デバッグ用）
            logger.debug("クッキーからセッション復元を試みます")
            return {
                "user_id": "demo_user_id",
                "email": "demo@example.com",
                "role": ["user"]
            }
        else:
            # 本番環境では401エラーを返す
            logger.error("認証されていないユーザーからのリクエスト")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="認証が必要です"
            )
    
    # ユーザーIDからデータベースで最新情報を取得
    user_id = request.session["user_id"]
    user = get_user(db, user_id)
    
    if not user:
        logger.error(f"ユーザーID {user_id} が見つかりません")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )
    
    # roleがリスト形式であることを確認
    role_permissions = user.role.permissions
    if isinstance(role_permissions, str):
        role_permissions = [role_permissions]
    
    return {
        "user_id": str(user.id),
        "email": user.email,
        "role": role_permissions
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