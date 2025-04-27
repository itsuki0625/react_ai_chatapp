from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta
import secrets
import string
from typing import Optional, Dict, Any, List, Tuple, Union
import logging

from ..models.user import User, UserLoginInfo
from ..core.security import get_password_hash, verify_password
from ..utils.time import get_current_time

logger = logging.getLogger(__name__)

def create_reset_token() -> str:
    """
    パスワードリセット用のランダムなトークンを生成
    """
    # 64文字のランダムな文字列を生成
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(64))

def save_reset_token(db: Session, user_id: UUID, token: str, expires_at: datetime) -> Dict:
    """
    パスワードリセットトークンをデータベースに保存
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.error(f"トークン保存エラー: ユーザーID {user_id} が見つかりません")
        return {"success": False, "error": "ユーザーが見つかりません"}
    
    # Userモデルにレコードのリセットトークンフィールドがないため、
    # リセットトークンはauthエンドポイントのJWTで管理しています。
    # この関数はそのためのプレースホルダーです。
    
    return {"success": True}

def verify_reset_token(db: Session, token: str) -> Optional[User]:
    """
    パスワードリセットトークンを検証し、関連ユーザーを返す
    """
    # この関数はプレースホルダーです。
    # 実際のトークン検証はauthエンドポイントのJWTデコードで行います。
    return None

def update_password(db: Session, user_id: UUID, new_password: str) -> Dict:
    """
    ユーザーのパスワードを更新
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"パスワード更新エラー: ユーザーID {user_id} が見つかりません")
            return {"success": False, "error": "ユーザーが見つかりません"}
        
        # パスワードをハッシュ化
        hashed_password = get_password_hash(new_password)
        user.hashed_password = hashed_password
        
        # ログイン情報をリセット
        login_info = db.query(UserLoginInfo).filter(UserLoginInfo.user_id == user_id).first()
        if login_info:
            login_info.failed_login_attempts = 0
            login_info.locked_until = None
            login_info.account_lock_reason = None
        
        db.commit()
        logger.info(f"ユーザーID {user_id} のパスワードを更新しました")
        return {"success": True}
    
    except Exception as e:
        db.rollback()
        logger.error(f"パスワード更新エラー: {str(e)}")
        return {"success": False, "error": str(e)}

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    パスワードの強度を検証
    
    戻り値:
        (検証結果, エラーメッセージ)
    """
    # 最小文字数
    if len(password) < 8:
        return False, "パスワードは8文字以上である必要があります"
    
    # 文字種の混在チェック（英大文字、英小文字、数字、記号の混在）
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    
    # 英大文字、英小文字、数字のうち2種類以上を含む必要がある
    criteria_count = sum([has_upper, has_lower, has_digit, has_special])
    if criteria_count < 2:
        return False, "パスワードは英大文字、英小文字、数字、記号のうち2種類以上を含む必要があります"
    
    # 連続する文字や数字のチェック
    for i in range(len(password) - 2):
        if (
            ord(password[i]) + 1 == ord(password[i+1]) and 
            ord(password[i+1]) + 1 == ord(password[i+2])
        ):
            return False, "パスワードに連続する3文字以上の並びは使用できません"
    
    # 同じ文字の繰り返しチェック
    for i in range(len(password) - 2):
        if password[i] == password[i+1] == password[i+2]:
            return False, "パスワードに同じ文字を3回以上連続して使用することはできません"
    
    return True, ""

def is_password_previously_used(db: Session, user_id: UUID, password: str) -> bool:
    """
    パスワードが以前に使用されたものかをチェック
    
    注：実際のパスワード履歴テーブルが必要です。
    この実装はプレースホルダーです。
    """
    # この機能を完全に実装するには、パスワード履歴を保存するテーブルが必要です
    # 現在のパスワードとの比較のみ行います
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    return verify_password(password, user.hashed_password)

def check_password_age(db: Session, user_id: UUID) -> Dict:
    """
    パスワードの経過日数を確認し、古い場合は更新を促す
    
    注：パスワード更新日時を記録する必要があります。
    この実装はプレースホルダーです。
    """
    # この機能を完全に実装するには、パスワード更新日時を保存する必要があります
    # プレースホルダー実装として、常にパスワードが有効であると返します
    return {
        "password_expired": False,
        "days_until_expiration": 90,  # 一般的なパスワード有効期限は90日
        "must_change": False
    } 