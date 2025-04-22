from sqlalchemy.orm import Session
from app.models.user import User, Role, UserEmailVerification, UserTwoFactorAuth, UserLoginInfo
from app.models.enums import AccountLockReason
from uuid import UUID
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import uuid

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user(db: Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def create_user(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: str,
    role_name: str = "生徒",
    school_id: UUID | None = None,
    is_active: bool = True,
    is_verified: bool = False
) -> User:
    """
    新規ユーザーを作成する

    Args:
        db: データベースセッション
        email: メールアドレス
        password: ハッシュ化されたパスワード
        full_name: フルネーム
        role_name: ロール名
        school_id: 学校ID（オプション）
        is_active: アクティブユーザーかどうか
        is_verified: メール検証済みかどうか

    Returns:
        作成されたユーザーオブジェクト
    """
    role_id = get_role_id(db, role_name)
    try:
        # ユーザーを作成
        user = User(
            id=uuid.uuid4(),
            email=email,
            hashed_password=password,
            full_name=full_name,
            role_id=role_id,
            school_id=school_id,
            is_active=is_active,
            is_verified=is_verified,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(user)
        db.flush()  # IDを取得するためにflush
        
        # メール検証レコードを作成
        email_verification = UserEmailVerification(
            id=uuid.uuid4(),
            user_id=user.id,
            email_verified=is_verified,
            email_verification_sent_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(email_verification)
        
        # ログイン情報レコードを作成
        login_info = UserLoginInfo(
            id=uuid.uuid4(),
            user_id=user.id,
            failed_login_attempts=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(login_info)
        
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        print(f"Error creating user: {str(e)}")  # エラーログを追加
        raise

# role_idを取得する
def get_role_id(db: Session, role_name: str) -> UUID:
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise ValueError(f"Role with name '{role_name}' not found")
    return role.id

def update_user(
    db: Session,
    *,
    user_id: str,
    update_data: Dict[str, Any]
) -> Optional[User]:
    """
    ユーザー情報を更新する

    Args:
        db: データベースセッション
        user_id: 更新するユーザーのID
        update_data: 更新するデータのディクショナリ

    Returns:
        更新されたユーザーオブジェクト、ユーザーが見つからない場合はNone
    """
    user = get_user(db, user_id)
    if not user:
        return None
    
    # 更新可能なフィールドのリスト
    updatable_fields = [
        "full_name", "hashed_password", "is_active", "is_verified",
        "is_2fa_enabled", "totp_secret", "school_id"
    ]
    
    # 更新データを適用
    for field in updatable_fields:
        if field in update_data:
            setattr(user, field, update_data[field])
    
    user.updated_at = datetime.utcnow()
    
    # 関連するレコードも更新
    if "is_verified" in update_data and user.email_verification:
        user.email_verification.email_verified = update_data["is_verified"]
        user.email_verification.updated_at = datetime.utcnow()
    
    if ("is_2fa_enabled" in update_data or "totp_secret" in update_data) and user.two_factor_auth:
        if "is_2fa_enabled" in update_data:
            user.two_factor_auth.enabled = update_data["is_2fa_enabled"]
        if "totp_secret" in update_data:
            user.two_factor_auth.secret = update_data["totp_secret"]
        user.two_factor_auth.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(user)
    return user

def verify_user_email(db: Session, user_id: str) -> bool:
    """
    ユーザーのメールアドレスを検証済みにする

    Args:
        db: データベースセッション
        user_id: ユーザーID

    Returns:
        更新に成功した場合はTrue、ユーザーが見つからない場合はFalse
    """
    user = get_user(db, user_id)
    if not user:
        return False
    
    user.is_verified = True
    if user.email_verification:
        user.email_verification.email_verified = True
        user.email_verification.updated_at = datetime.utcnow()
    
    user.updated_at = datetime.utcnow()
    db.commit()
    return True

def setup_2fa(db: Session, user_id: str, totp_secret: str) -> bool:
    """
    ユーザーの二要素認証を設定する

    Args:
        db: データベースセッション
        user_id: ユーザーID
        totp_secret: TOTPシークレット

    Returns:
        設定に成功した場合はTrue、ユーザーが見つからない場合はFalse
    """
    user = get_user(db, user_id)
    if not user:
        return False
    
    # ユーザーの2FA設定を更新
    user.is_2fa_enabled = True
    user.totp_secret = totp_secret
    user.updated_at = datetime.utcnow()
    
    # 既存の2FAレコードがあれば更新、なければ作成
    if user.two_factor_auth:
        user.two_factor_auth.enabled = True
        user.two_factor_auth.secret = totp_secret
        user.two_factor_auth.updated_at = datetime.utcnow()
    else:
        two_factor_auth = UserTwoFactorAuth(
            id=uuid.uuid4(),
            user_id=user.id,
            enabled=True,
            secret=totp_secret,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(two_factor_auth)
    
    db.commit()
    return True

def disable_2fa(db: Session, user_id: str) -> bool:
    """
    ユーザーの二要素認証を無効化する

    Args:
        db: データベースセッション
        user_id: ユーザーID

    Returns:
        無効化に成功した場合はTrue、ユーザーが見つからない場合はFalse
    """
    user = get_user(db, user_id)
    if not user:
        return False
    
    # ユーザーの2FA設定を更新
    user.is_2fa_enabled = False
    user.totp_secret = None
    user.updated_at = datetime.utcnow()
    
    # 既存の2FAレコードがあれば更新
    if user.two_factor_auth:
        user.two_factor_auth.enabled = False
        user.two_factor_auth.secret = None
        user.two_factor_auth.updated_at = datetime.utcnow()
    
    db.commit()
    return True

def record_login_attempt(db: Session, user_id: str, success: bool) -> None:
    """
    ログイン試行を記録する

    Args:
        db: データベースセッション
        user_id: ユーザーID
        success: ログイン成功したかどうか
    """
    user = get_user(db, user_id)
    if not user or not user.login_info:
        return
    
    login_info = user.login_info
    now = datetime.utcnow()
    
    if success:
        # ログイン成功時
        login_info.last_login_at = now
        login_info.failed_login_attempts = 0
        login_info.locked_until = None
        login_info.account_lock_reason = None
    else:
        # ログイン失敗時
        login_info.last_failed_login_at = now
        login_info.failed_login_attempts += 1
        
        # 一定回数失敗でアカウントロック
        if login_info.failed_login_attempts >= 5:
            login_info.locked_until = now + timedelta(minutes=15)
            login_info.account_lock_reason = AccountLockReason.FAILED_ATTEMPTS
    
    login_info.updated_at = now
    db.commit()

def is_account_locked(db: Session, user_id: str) -> bool:
    """
    アカウントがロックされているか確認する

    Args:
        db: データベースセッション
        user_id: ユーザーID

    Returns:
        アカウントがロックされている場合はTrue、そうでない場合はFalse
    """
    user = get_user(db, user_id)
    if not user or not user.login_info:
        return False
    
    login_info = user.login_info
    now = datetime.utcnow()
    
    # ロック有効期限がある場合、現在時刻と比較
    if login_info.locked_until and login_info.locked_until > now:
        return True
    
    # ロック期限が過ぎた場合、ロック情報をリセット
    if login_info.locked_until:
        login_info.locked_until = None
        login_info.account_lock_reason = None
        db.commit()
    
    return False

def delete_user(db: Session, user_id: str) -> bool:
    """
    ユーザーを削除する

    Args:
        db: データベースセッション
        user_id: ユーザーID

    Returns:
        削除に成功した場合はTrue、ユーザーが見つからない場合はFalse
    """
    user = get_user(db, user_id)
    if not user:
        return False
    
    # 関連するレコードごと削除（カスケード削除されるはず）
    db.delete(user)
    db.commit()
    return True

