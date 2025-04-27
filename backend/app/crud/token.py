from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
from app.models.user import TokenBlacklist
from app.models.enums import TokenBlacklistReason
import uuid

def add_token_to_blacklist(
    db: Session,
    token_jti: str,
    user_id: str,
    expires_at: datetime,
    reason: TokenBlacklistReason = TokenBlacklistReason.LOGOUT
) -> TokenBlacklist:
    """
    トークンをブラックリストに追加する

    Args:
        db: データベースセッション
        token_jti: トークンのJTI (JWT ID)
        user_id: ユーザーID
        expires_at: トークンの有効期限
        reason: 失効理由

    Returns:
        作成されたTokenBlacklistエントリ
    """
    db_token = TokenBlacklist(
        id=uuid.uuid4(),
        token_jti=token_jti,
        user_id=user_id,
        expires_at=expires_at,
        reason=reason,
        created_at=datetime.utcnow()
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token

def is_token_blacklisted(db: Session, token_jti: str) -> bool:
    """
    トークンがブラックリストに登録されているかチェックする

    Args:
        db: データベースセッション
        token_jti: トークンのJTI (JWT ID)

    Returns:
        ブラックリストに登録されている場合はTrue、そうでない場合はFalse
    """
    return db.query(TokenBlacklist).filter(TokenBlacklist.token_jti == token_jti).first() is not None

def get_blacklisted_tokens_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[TokenBlacklist]:
    """
    特定ユーザーのブラックリストに登録されたトークンを取得

    Args:
        db: データベースセッション
        user_id: ユーザーID
        skip: スキップするレコード数
        limit: 取得する最大レコード数

    Returns:
        ブラックリストに登録されたトークンのリスト
    """
    return db.query(TokenBlacklist).filter(TokenBlacklist.user_id == user_id).offset(skip).limit(limit).all()

def remove_expired_tokens(db: Session) -> int:
    """
    期限切れのブラックリストトークンを削除する

    Args:
        db: データベースセッション

    Returns:
        削除されたレコード数
    """
    now = datetime.utcnow()
    result = db.query(TokenBlacklist).filter(TokenBlacklist.expires_at < now).delete()
    db.commit()
    return result

def blacklist_tokens_by_user(
    db: Session,
    user_id: str,
    reason: TokenBlacklistReason = TokenBlacklistReason.SECURITY_BREACH
) -> int:
    """
    特定ユーザーの全アクティブトークンをブラックリストに登録する
    パスワード変更時や不審なアクティビティ検出時などに使用

    Args:
        db: データベースセッション
        user_id: ユーザーID
        reason: 失効理由

    Returns:
        影響を受けたレコード数
    """
    # 現実のアプリケーションでは、すべてのアクティブなトークンを追跡する方法が必要
    # この実装では、ユーザーのセキュリティイベント（パスワード変更など）発生時に、
    # そのイベント以前に発行されたすべてのトークンを無効化するための措置として、
    # 将来的な使用のためのスケルトン実装です
    
    # 実装例：現在より30日以内に発行されたトークンをすべて無効化
    # これは実際のトークンJTIがわからないため、ブロッキングには使えませんが、
    # セキュリティイベント発生時のタイムスタンプを記録するのに役立ちます
    
    now = datetime.utcnow()
    expiry = now + timedelta(days=30)  # 30日後を期限とする
    
    # セキュリティイベントを記録
    security_record = TokenBlacklist(
        id=uuid.uuid4(),
        token_jti=f"security-event-{uuid.uuid4()}",  # 特殊なJTIフォーマット
        user_id=user_id,
        expires_at=expiry,
        reason=reason,
        created_at=now
    )
    
    db.add(security_record)
    db.commit()
    
    # JWT検証時に、トークン発行日とユーザーの最終セキュリティイベント日時を比較する
    # 実装を追加することで、特定のJTIを知らなくても、発行日時に基づいてトークンを無効化できる
    
    return 1  # 影響を受けたレコード数（ここでは常に1）

def get_latest_security_event(db: Session, user_id: str) -> Optional[datetime]:
    """
    特定ユーザーの最新のセキュリティイベント（パスワード変更など）のタイムスタンプを取得

    Args:
        db: データベースセッション
        user_id: ユーザーID

    Returns:
        最新のセキュリティイベントのタイムスタンプ。イベントがない場合はNone
    """
    # セキュリティイベントはtokenがsecurity-event-で始まるレコード
    record = db.query(TokenBlacklist).filter(
        TokenBlacklist.user_id == user_id,
        TokenBlacklist.token_jti.like("security-event-%")
    ).order_by(TokenBlacklist.created_at.desc()).first()
    
    return record.created_at if record else None 