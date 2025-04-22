from datetime import datetime, timedelta
from typing import Any, Union, Dict, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings
import uuid
from sqlalchemy.orm import Session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    アクセストークンを生成
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),  # 発行時刻
        "type": "access"
    })
    
    # JWTの一意のIDを生成
    if "jti" not in to_encode:
        to_encode["jti"] = str(uuid.uuid4())
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    リフレッシュトークンを生成
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),  # 発行時刻
        "type": "refresh",
        "jti": str(uuid.uuid4())  # リフレッシュトークンは必ず一意のIDを持つ
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_token(token: str) -> bool:
    """
    JWTトークンの署名と有効期限を検証
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return True
    except JWTError:
        return False

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    JWTトークンをデコードしてペイロードを取得
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None

def verify_token_against_security_events(token: str, db: Session, user_id: str) -> bool:
    """
    トークンがセキュリティイベント（パスワード変更など）以前に発行されたものでないか検証する

    Args:
        token: 検証するJWTトークン
        db: データベースセッション
        user_id: ユーザーID

    Returns:
        有効なトークンの場合はTrue、無効な場合はFalse
    """
    from app.crud.token import get_latest_security_event
    
    # トークンをデコード
    payload = decode_token(token)
    if not payload:
        return False
    
    # 発行時刻を取得
    if "iat" not in payload:
        return False  # 発行時刻がないトークンは無効
    
    token_issued_at = datetime.fromtimestamp(payload["iat"])
    
    # ユーザーの最新のセキュリティイベント時刻を取得
    latest_security_event = get_latest_security_event(db, user_id)
    
    # セキュリティイベントがない場合は有効
    if not latest_security_event:
        return True
    
    # トークンがセキュリティイベント以前に発行されたものなら無効
    if token_issued_at < latest_security_event:
        return False
    
    return True

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    プレーンパスワードとハッシュ化されたパスワードを比較
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    パスワードをハッシュ化
    """
    return pwd_context.hash(password) 