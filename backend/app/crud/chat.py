from sqlalchemy.orm import Session
from app.models.chat import ChatSession, ChatMessage
from app.models.enums import SessionStatus, SessionType
from uuid import UUID
from typing import List, Optional
from datetime import datetime
import uuid
from fastapi import HTTPException

async def get_or_create_chat_session(
    db: Session,
    user_id: UUID,
    session_id: Optional[str] = None,
    session_type: str = "CONSULTATION"
) -> ChatSession:
    """
    チャットセッションを取得または作成する
    
    Args:
        db: データベースセッション
        user_id: ユーザーID
        session_id: セッションID（オプション）
        session_type: セッションタイプ（CONSULTATION or FAQ）
    
    Returns:
        ChatSession: 取得または作成されたチャットセッション
    """
    # セッションタイプをEnumに変換
    try:
        session_type_enum = SessionType[session_type]
    except KeyError:
        raise ValueError(f"Invalid session type: {session_type}")

    if session_id:
        try:
            # 既存のセッションを取得
            session = db.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id,
                ChatSession.session_type == session_type_enum
            ).first()
            if session:
                return session
        except ValueError:
            print("セッションIDが無効な場合は新規作成")

    # 新しいセッションを作成
    new_session = ChatSession(
        id=uuid.uuid4(),
        user_id=user_id,
        title="新しいチャット" if session_type == "CONSULTATION" else "新しい質問",
        status=SessionStatus.ACTIVE,
        session_type=session_type_enum
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

async def save_chat_message(
    db: Session,
    session_id: UUID,
    content: str,
    sender_id: Optional[UUID] = None,
    sender_type: str = "USER"
) -> ChatMessage:
    """
    チャットメッセージを保存する
    
    Args:
        db: データベースセッション
        session_id: セッションID
        content: メッセージ内容
        sender_id: 送信者ID（AIの場合はNone）
        sender_type: 送信者タイプ（"USER" or "AI" or "SYSTEM"）
    
    Returns:
        ChatMessage: 保存されたメッセージ
    """
    message = ChatMessage(
        session_id=session_id,
        content=content,
        sender_id=sender_id,
        sender_type=sender_type,
        is_read=True
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

async def get_user_chat_sessions(
    db: Session,
    user_id: UUID,
    session_type: str = "CONSULTATION"
) -> List[ChatSession]:
    """
    ユーザーのアクティブなチャットセッション一覧を取得
    """
    try:
        session_type_enum = SessionType[session_type]
    except KeyError:
        raise ValueError(f"Invalid session type: {session_type}")

    return db.query(ChatSession).filter(
        ChatSession.user_id == user_id,
        ChatSession.status != SessionStatus.ARCHIVED,
        ChatSession.session_type == session_type_enum
    ).order_by(ChatSession.updated_at.desc()).all()

async def get_session_messages(
    db: Session,
    session_id: str,
    user_id: UUID,
    session_type: str = "CONSULTATION"
) -> List[ChatMessage]:
    """
    特定のセッションのメッセージ履歴を取得する
    """
    try:
        session_type_enum = SessionType[session_type]
    except KeyError:
        raise ValueError(f"Invalid session type: {session_type}")

    # セッションの所有者確認
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id,
        ChatSession.session_type == session_type_enum
    ).first()
    
    if not session:
        raise ValueError("Session not found or unauthorized")
    
    return db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).all()

async def update_session_title(
    db: Session,
    session_id: UUID,
    user_id: UUID,
    title: str,
) -> ChatSession:
    """
    チャットセッションのタイトルを更新する
    """

    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id,
    ).first()
    
    if not session:
        raise ValueError("Session not found or unauthorized")
    
    session.title = title
    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    return session

async def update_session_status(
    db: Session,
    session_id: str,
    user_id: UUID,
    status: str,
    session_type: str = "CONSULTATION"
) -> ChatSession:
    """
    チャットセッションのステータスを更新する
    """
    try:
        session_type_enum = SessionType[session_type]
    except KeyError:
        raise ValueError(f"Invalid session type: {session_type}")

    try:
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
            ChatSession.session_type == session_type_enum
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if status.lower() == "archived":
            session.status = SessionStatus.ARCHIVED
        elif status.lower() == "active":
            session.status = SessionStatus.ACTIVE
        else:
            raise HTTPException(status_code=400, detail=f"Invalid status value: {status}")
        
        session.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(session)
        
        return session
    except Exception as e:
        print("Error in update_session_status:", str(e))
        db.rollback()
        raise

async def get_archived_chat_sessions(
    db: Session,
    user_id: UUID,
    session_type: str = "CONSULTATION"
) -> List[ChatSession]:
    """
    ユーザーのアーカイブされたチャットセッション一覧を取得
    """
    try:
        session_type_enum = SessionType[session_type]
    except KeyError:
        raise ValueError(f"Invalid session type: {session_type}")
    
    print("session_type_enum : ", session_type_enum)

    return db.query(ChatSession).filter(
        ChatSession.user_id == user_id,
        ChatSession.status == SessionStatus.ARCHIVED,
        ChatSession.session_type == session_type_enum
    ).order_by(ChatSession.updated_at.desc()).all()