from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.chat import ChatSession, ChatMessage
from app.models.enums import SessionStatus, ChatType
from uuid import UUID
from typing import List, Optional, Dict
from datetime import datetime
import uuid
from fastapi import HTTPException
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

async def get_or_create_chat_session(
    db: AsyncSession,
    user_id: UUID,
    session_id: Optional[str] = None,
    chat_type: str = "general"
) -> ChatSession:
    """
    チャットセッションを取得または作成する
    
    Args:
        db: データベースセッション
        user_id: ユーザーID
        session_id: セッションID（オプション）
        chat_type: チャットタイプ (例: "consultation", "self_analysis")
    
    Returns:
        ChatSession: 取得または作成されたチャットセッション
    """
    # セッションタイプをEnumに変換
    try:
        chat_type_enum = ChatType(chat_type)
    except ValueError:
        raise ValueError(f"Invalid chat type: {chat_type}")

    if session_id:
        try:
            session_uuid = uuid.UUID(session_id)
            # session = db.query(ChatSession).filter(...).first()
            stmt = select(ChatSession).filter(
                ChatSession.id == session_uuid,
                ChatSession.user_id == user_id,
                ChatSession.chat_type == chat_type_enum
            )
            result = await db.execute(stmt)
            session = result.scalars().first()
            if session:
                return session
        except ValueError:
            logger.warning(f"Invalid session_id format: {session_id}. Proceeding to create a new session.")

    # 新しいセッションを作成
    new_session = ChatSession(
        id=uuid.uuid4(),
        user_id=user_id,
        title=("自己分析" if chat_type_enum == ChatType.SELF_ANALYSIS 
               else ("総合型選抜" if chat_type_enum == ChatType.ADMISSION
                     else ("学習支援" if chat_type_enum == ChatType.STUDY_SUPPORT
                           else "一般的なチャット"))),
        status=SessionStatus.ACTIVE,
        chat_type=chat_type_enum
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return new_session

async def save_chat_message(
    db: AsyncSession,
    session_id: UUID,
    content: str,
    user_id: Optional[UUID] = None,
    sender_type: str = "USER"
) -> ChatMessage:
    """
    チャットメッセージを保存する
    
    Args:
        db: データベースセッション
        session_id: セッションID
        content: メッセージ内容
        user_id: ユーザーID（AIの場合はNone）
        sender_type: 送信者タイプ（"USER" or "AI" or "SYSTEM"）
    
    Returns:
        ChatMessage: 保存されたメッセージ
    """
    message = ChatMessage(
        session_id=session_id,
        content=content,
        user_id=user_id,
        sender=sender_type
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message

async def get_user_chat_sessions(
    db: AsyncSession,
    user_id: UUID,
    chat_type: str = "general"
) -> List[ChatSession]:
    """
    ユーザーのアクティブなチャットセッション一覧を取得
    """
    try:
        chat_type_enum = ChatType(chat_type)
    except ValueError:
        raise ValueError(f"Invalid chat type: {chat_type}")

    # return db.query(ChatSession).filter(...).order_by(...).all()
    stmt = select(ChatSession).filter(
        ChatSession.user_id == user_id,
        ChatSession.status != SessionStatus.ARCHIVED,
        ChatSession.chat_type == chat_type_enum
    ).order_by(ChatSession.updated_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_session_messages(
    db: AsyncSession,
    session_id: str,
    user_id: UUID,
    chat_type: str
) -> List[ChatMessage]:
    """
    特定のセッションのメッセージ履歴を取得する
    """
    try:
        chat_type_enum = ChatType(chat_type)
    except ValueError:
        raise ValueError(f"Invalid chat type: {chat_type}")
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
         logger.error(f"Invalid UUID format for session_id: {session_id}")
         raise ValueError("Invalid session ID format")

    # セッションの所有者確認
    stmt_session = select(ChatSession).filter(
        ChatSession.id == session_uuid,
        ChatSession.user_id == user_id,
        ChatSession.chat_type == chat_type_enum
    )
    result_session = await db.execute(stmt_session)
    session = result_session.scalars().first()

    if not session:
        raise ValueError("Session not found or unauthorized")

    # return db.query(ChatMessage).filter(...).order_by(...).all()
    stmt_messages = select(ChatMessage).filter(
        ChatMessage.session_id == session_uuid
    ).order_by(ChatMessage.created_at.asc())
    result_messages = await db.execute(stmt_messages)
    return result_messages.scalars().all()

async def update_session_title(
    db: AsyncSession,
    session_id: UUID,
    user_id: UUID,
    title: str,
) -> ChatSession:
    """
    チャットセッションのタイトルを更新する
    """

    # session = db.query(ChatSession).filter(...).first()
    stmt = select(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id,
    )
    result = await db.execute(stmt)
    session = result.scalars().first()
    
    if not session:
        raise ValueError("Session not found or unauthorized")
    
    session.title = title
    session.updated_at = datetime.utcnow()
    db.add(session) # Add to session for tracking changes
    await db.commit()
    await db.refresh(session)
    return session

async def update_session_status(
    db: AsyncSession,
    session_id: str,
    user_id: UUID,
    status: str,
    chat_type: str = "general"
) -> ChatSession:
    """
    チャットセッションのステータスを更新する
    """
    try:
        chat_type_enum = ChatType(chat_type)
    except ValueError:
        raise ValueError(f"Invalid chat type: {chat_type}")
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        logger.error(f"Invalid UUID format for session_id: {session_id}")
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    try:
        # session = db.query(ChatSession).filter(...).first()
        stmt = select(ChatSession).filter(
            ChatSession.id == session_uuid,
            ChatSession.user_id == user_id,
            ChatSession.chat_type == chat_type_enum
        )
        result = await db.execute(stmt)
        session = result.scalars().first()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        try:
            status_enum = SessionStatus[status.upper()]
        except KeyError:
             raise HTTPException(status_code=400, detail=f"Invalid status value: {status}")

        session.status = status_enum
        
        session.updated_at = datetime.utcnow()
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        return session
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error in update_session_status: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error during session status update.")

async def get_archived_chat_sessions(
    db: AsyncSession,
    user_id: UUID,
    chat_type: str = "general"
) -> List[ChatSession]:
    """
    ユーザーのアーカイブされたチャットセッション一覧を取得
    """
    try:
        chat_type_enum = ChatType(chat_type)
    except ValueError:
        raise ValueError(f"Invalid chat type: {chat_type}")

    logger.debug(f"Fetching archived sessions for user {user_id} with type {chat_type_enum}")

    # return db.query(ChatSession).filter(...).order_by(...).all()
    stmt = select(ChatSession).filter(
        ChatSession.user_id == user_id,
        ChatSession.status == SessionStatus.ARCHIVED,
        ChatSession.chat_type == chat_type_enum
    ).order_by(ChatSession.updated_at.desc())
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    logger.debug(f"Found {len(sessions)} archived sessions.")
    return sessions

async def get_chat_messages(db: AsyncSession, session_id: UUID) -> List[Dict]:
    """チャット履歴を取得"""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        logger.error(f"Invalid UUID format for session_id: {session_id}")
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    try:
        # messages = db.query(ChatMessage).filter(...).order_by(...).all()
        stmt = select(ChatMessage).filter(
            ChatMessage.session_id == session_uuid
        ).order_by(ChatMessage.created_at.asc())
        result = await db.execute(stmt)
        messages = result.scalars().all()

        return [
            {
                "role": msg.sender_type.lower(),
                "content": msg.content,
                "timestamp": msg.created_at
            } for msg in messages
        ]
    except Exception as e:
        logger.error(f"Error getting chat messages for session {session_id}: {e}", exc_info=True)
        # Re-raise a more specific HTTP exception if appropriate,
        # otherwise let the default FastAPI handler catch it.
        raise HTTPException(status_code=500, detail="Failed to retrieve chat messages.")

async def get_chat_session_by_id(db: AsyncSession, session_id: UUID) -> Optional[ChatSession]:
    """指定されたIDのChatSessionを取得する"""
    stmt = select(ChatSession).filter(ChatSession.id == session_id)
    result = await db.execute(stmt)
    return result.scalars().first()