from datetime import datetime, timedelta
from typing import Any, Union, Dict, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings
import uuid
import os
import hashlib
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- AUTH_SECRET からキーを導出 --- 
# このキーは AuthMiddleware でも使用される
AUTH_SECRET = settings.AUTH_SECRET
if not AUTH_SECRET:
    raise RuntimeError("AUTH_SECRET not found in settings")
derived_key = hashlib.sha512(AUTH_SECRET.encode('utf-8')).digest()

# --- JWT アルゴリズム --- 
# AuthMiddleware と合わせる
# JWT_ALGORITHM = "HS512" # settings から読むので削除

# JWTアルゴリズム (config.py にないため、ここで定義するか、configに追加する)
# ALGORITHM = "HS256" # settings から読むので削除、また HS512 に統一

logger = logging.getLogger(__name__)

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
        derived_key,      # 導出したキーを使用
        algorithm=settings.JWT_ALGORITHM # settings から読み込む
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
        derived_key,      # 導出したキーを使用
        algorithm=settings.JWT_ALGORITHM # settings から読み込む
    )
    return encoded_jwt

def verify_token(token: str) -> bool:
    """
    JWTトークンの署名と有効期限を検証
    """
    try:
        payload = jwt.decode(
            token,
            derived_key, # derived_key を使用
            algorithms=[settings.JWT_ALGORITHM] # settings から読み込む
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
            derived_key, # derived_key を使用
            algorithms=[settings.JWT_ALGORITHM] # settings から読み込む
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

def decode_token_to_user_id(token: str) -> str | None:
    """
    JWTトークンをデコードし、ユーザーID (subクレーム) を返します。
    デコードに失敗した場合はHTTPExceptionを発生させます。
    """
    try:
        payload = jwt.decode(
            token, 
            derived_key, # settings.SECRET_KEY から derived_key に変更
            algorithms=[settings.JWT_ALGORITHM] # settings から読み込む
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            logger.warning("Token decoding successful, but 'sub' claim is missing.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials (sub claim missing)",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.debug(f"Token decoded successfully. User ID (sub): {user_id}")
        return user_id
    except JWTError as e:
        logger.error(f"JWTError during token decoding: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials, token may be invalid or expired ({str(e)})",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during token decoding: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing authentication token.",
        )

# パスワードハッシュ化などの他のセキュリティ関連ユーティリティもここに追加可能 