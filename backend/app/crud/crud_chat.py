from sqlalchemy.orm import Session
from typing import List, Optional

from app.models import chat as models # models.chat をインポート
from app.schemas import chat as schemas # schemas.chat をインポート
from app.schemas.chat import ChatType, ChatSessionStatus

# --- ChatSession CRUD ---

def create_chat_session(db: Session, user_id: int, chat_type: ChatType) -> models.ChatSession:
    """
    指定されたタイプの新しいチャットセッションを作成します。
    """
    db_session = models.ChatSession(user_id=user_id, chat_type=chat_type)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_chat_session(db: Session, session_id: int) -> Optional[models.ChatSession]:
    """
    指定されたIDのチャットセッションを取得します。
    メッセージも一緒にロードします。
    """
    # sqlalchemy.orm.joinedload を使ってメッセージを事前に読み込むと効率が良い場合があります
    # from sqlalchemy.orm import joinedload
    return db.query(models.ChatSession).options(
        # joinedload(models.ChatSession.messages) # N+1問題を避けるために必要に応じて有効化
    ).filter(models.ChatSession.id == session_id).first()

def get_user_chat_sessions(
    db: Session, 
    user_id: int, 
    chat_type: Optional[ChatType] = None, 
    status: Optional[ChatSessionStatus] = None
) -> List[models.ChatSession]:
    """
    指定されたユーザーのチャットセッションを取得します。
    オプションで chat_type と status によるフィルタリングが可能です。
    """
    query = db.query(models.ChatSession).filter(models.ChatSession.user_id == user_id)
    if chat_type:
        query = query.filter(models.ChatSession.chat_type == chat_type)
    if status:
        query = query.filter(models.ChatSession.status == status)
        
    return query.order_by(models.ChatSession.updated_at.desc()).all()

# --- ChatMessage CRUD ---

def create_chat_message(db: Session, session_id: int, sender: models.MessageSender, content: str) -> models.ChatMessage:
    """
    新しいチャットメッセージを作成します。
    """
    db_message = models.ChatMessage(
        session_id=session_id,
        sender=sender,
        content=content
    )
    db.add(db_message)
    # セッションのupdated_atも更新
    # import datetime # 必要に応じてインポート
    # session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
    # if session:
    #     session.updated_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_chat_messages(db: Session, session_id: int, skip: int = 0, limit: int = 100) -> List[models.ChatMessage]:
    """
    指定されたチャットセッションのメッセージを取得します（ページネーション対応）。
    """
    return db.query(models.ChatMessage)\
        .filter(models.ChatMessage.session_id == session_id)\
        .order_by(models.ChatMessage.created_at.asc())\
        .offset(skip)\
        .limit(limit)\
        .all() 