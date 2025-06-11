from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.chat import ChatSession, ChatMessage, MessageSender
from app.models.enums import SessionStatus, ChatType
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import uuid
from fastapi import HTTPException
import logging
from sqlalchemy.exc import NoResultFound
from enum import Enum
from app.schemas.chat import ChatSessionSummary
from sqlalchemy.orm import selectinload

# ロガーの設定
logger = logging.getLogger(__name__)

async def get_or_create_chat_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    session_id: Optional[Union[str, uuid.UUID]] = None,
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
    try:
        chat_type_enum = ChatType(chat_type)
    except ValueError:
        logger.error(f"Invalid chat type provided to get_or_create_chat_session: {chat_type}")
        raise ValueError(f"Invalid chat type: {chat_type}")

    actual_session_uuid: Optional[uuid.UUID] = None

    if session_id:
        if isinstance(session_id, uuid.UUID):
            actual_session_uuid = session_id
        elif isinstance(session_id, str):
            try:
                actual_session_uuid = uuid.UUID(session_id)
            except ValueError:
                logger.warning(f"Invalid session_id string format: {session_id}. Proceeding to create a new session.")
        else:
            logger.warning(f"Unexpected type for session_id: {type(session_id)}. Proceeding to create a new session.")
    
    if actual_session_uuid:
        stmt = select(ChatSession).filter(
            ChatSession.id == actual_session_uuid,
            ChatSession.user_id == user_id,
        )
        result = await db.execute(stmt)
        session = result.scalars().first()
        if session:
            if session.chat_type != chat_type_enum:
                logger.warning(f"Requested chat_type '{chat_type_enum}' differs from existing session '{session.id}' chat_type '{session.chat_type}'. Returning existing session.")
            return session
        else:
            logger.warning(f"Session with ID {actual_session_uuid} not found for user {user_id}. Creating a new session instead.")
            pass

    new_session_uuid = uuid.uuid4()
    logger.info(f"Creating new chat session with ID {new_session_uuid} for user {user_id} and type {chat_type_enum}")

    new_session = ChatSession(
        id=new_session_uuid,
        user_id=user_id,
        title=None,  # タイトルは最初の投稿時に自動生成
        status=SessionStatus.ACTIVE,
        chat_type=chat_type_enum
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return new_session

async def save_chat_message(
    db: AsyncSession,
    session_id: uuid.UUID,
    content: str,
    user_id: Optional[uuid.UUID] = None,
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
    user_id: uuid.UUID,
    chat_type: str = "general",
    status: Optional[SessionStatus] = SessionStatus.ACTIVE
) -> List[ChatSessionSummary]:
    """
    ユーザーのチャットセッション一覧をChatSessionSummaryのリストとして取得。
    オプションでステータスによるフィルタリングも可能。
    """
    logger.debug(f"[CRUD get_user_chat_sessions] Called with user_id: {user_id}, chat_type_str: '{chat_type}', status: {status}")
    try:
        chat_type_enum_filter = ChatType(chat_type)
        logger.debug(f"[CRUD get_user_chat_sessions] Parsed chat_type_enum_filter: {chat_type_enum_filter}")
    except ValueError:
        logger.warning(f"[CRUD get_user_chat_sessions] Invalid chat_type string '{chat_type}'.")
        raise ValueError(f"Invalid chat type string for filtering: {chat_type}")

    filters = [
        ChatSession.user_id == user_id,
        ChatSession.chat_type == chat_type_enum_filter
    ]
    if status:
        filters.append(ChatSession.status == status)
    
    stmt = select(ChatSession).filter(*filters).order_by(ChatSession.updated_at.desc())
    result = await db.execute(stmt)
    sessions_db = result.scalars().all()
    logger.debug(f"[CRUD get_user_chat_sessions] Found {len(sessions_db)} sessions from DB before processing summaries.")

    summaries: List[ChatSessionSummary] = []
    for session_db in sessions_db:
        logger.debug(f"[CRUD get_user_chat_sessions] Processing session ID: {session_db.id}, title: {session_db.title}")
        last_message_stmt = select(ChatMessage.content)\
            .filter(ChatMessage.session_id == session_db.id)\
            .order_by(ChatMessage.created_at.desc())\
            .limit(1)
        last_message_result = await db.execute(last_message_stmt)
        last_message_content = last_message_result.scalars().first()
        logger.debug(f"[CRUD get_user_chat_sessions] For session {session_db.id}, last_message_content: '{last_message_content}'")

        summary_text = None
        if last_message_content:
            summary_text = (last_message_content[:50] + '...') if len(last_message_content) > 50 else last_message_content
        logger.debug(f"[CRUD get_user_chat_sessions] For session {session_db.id}, summary_text: '{summary_text}'")
        
        summaries.append(
            ChatSessionSummary(
                id=session_db.id,
                title=session_db.title,
                chat_type=session_db.chat_type,
                created_at=session_db.created_at,
                updated_at=session_db.updated_at,
                last_message_summary=summary_text
            )
        )
    logger.debug(f"[CRUD get_user_chat_sessions] Returning {len(summaries)} summaries.")
    return summaries

async def get_session_messages(
    db: AsyncSession,
    session_id: str,
    user_id: uuid.UUID,
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

    stmt_session = select(ChatSession).filter(
        ChatSession.id == session_uuid,
        ChatSession.user_id == user_id,
        ChatSession.chat_type == chat_type_enum
    )
    result_session = await db.execute(stmt_session)
    session = result_session.scalars().first()

    if not session:
        raise ValueError("Session not found or unauthorized")

    stmt_messages = select(ChatMessage).filter(
        ChatMessage.session_id == session_uuid
    ).order_by(ChatMessage.created_at.asc())
    result_messages = await db.execute(stmt_messages)
    return result_messages.scalars().all()

async def update_session_title(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    title: str,
) -> ChatSession:
    """
    チャットセッションのタイトルを更新する
    """

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
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

async def update_session_status(
    db: AsyncSession,
    session_id: Union[str, uuid.UUID],
    user_id: uuid.UUID,
    status: str,
    chat_type: str = "general"
) -> ChatSession:
    """
    チャットセッションのステータスを更新する
    """
    try:
        chat_type_enum = ChatType(chat_type)
    except ValueError:
        logger.error(f"Invalid chat_type '{chat_type}' in update_session_status.")
        raise ValueError(f"Invalid chat type: {chat_type}")
    
    actual_session_uuid: uuid.UUID
    if isinstance(session_id, uuid.UUID):
        actual_session_uuid = session_id
    elif isinstance(session_id, str):
        try:
            actual_session_uuid = uuid.UUID(session_id)
        except ValueError:
            logger.error(f"Invalid UUID string format for session_id: {session_id}")
            raise HTTPException(status_code=400, detail="Invalid session ID format")
    else:
        logger.error(f"Invalid type for session_id: {type(session_id)}. Expected str or UUID.")
        raise HTTPException(status_code=400, detail="Invalid session ID type")

    try:
        stmt = select(ChatSession).filter(
            ChatSession.id == actual_session_uuid, 
            ChatSession.user_id == user_id,
            ChatSession.chat_type == chat_type_enum
        )
        result = await db.execute(stmt)
        session = result.scalars().first()

        if not session:
            logger.warning(f"Session not found with id {actual_session_uuid} for user {user_id} and chat_type {chat_type_enum} during status update.")
            raise HTTPException(status_code=404, detail="Session not found or access denied for status update.")
        
        try:
            status_enum = SessionStatus[status.upper()]
        except KeyError:
            logger.error(f"Invalid status value: {status}. Cannot map to SessionStatus enum.")
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
        logger.error(f"Error in update_session_status for session_id {actual_session_uuid}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during session status update.")

async def get_archived_chat_sessions(
    db: AsyncSession,
    user_id: uuid.UUID,
    chat_type: str = "general"
) -> List[ChatSessionSummary]:
    """
    ユーザーのアーカイブ済みチャットセッション一覧を ChatSessionSummary のリストとして取得
    """
    return await get_user_chat_sessions(db, user_id, chat_type, status=SessionStatus.ARCHIVED)

async def get_chat_messages(db: AsyncSession, session_id: uuid.UUID) -> List[Dict]:
    """チャット履歴を取得"""
    try:
        pass
    except ValueError:
        logger.error(f"Invalid UUID format for session_id: {session_id}")
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    try:
        stmt = select(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc())
        result = await db.execute(stmt)
        messages = result.scalars().all()

        return [
            {
                "role": msg.sender.value.lower() if isinstance(msg.sender, Enum) else str(msg.sender).lower(),
                "content": msg.content,
                "timestamp": msg.created_at
            } for msg in messages
        ]
    except Exception as e:
        logger.error(f"Error getting chat messages for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve chat messages.")

async def get_chat_session_by_id(db: AsyncSession, session_id: uuid.UUID) -> Optional[ChatSession]:
    """指定されたIDのChatSessionを取得する"""
    stmt = select(ChatSession).filter(ChatSession.id == session_id)
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_chat_messages_history(
    db: AsyncSession, 
    session_id: str, 
    limit: int = 100, 
    offset: int = 0
) -> list[dict[str, Any]]:
    """
    特定のチャットセッションのメッセージ履歴を取得し、OpenAI APIに適した形式で返す。
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        logger.error(f"Invalid UUID format for session_id: {session_id}")
        return []

    stmt = (
        select(ChatMessage)
        .filter(ChatMessage.session_id == session_uuid)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()
    
    history = []
    for msg in messages:
        current_sender_value = msg.sender.value
        
        if current_sender_value == MessageSender.USER.value:
            role_for_openai = "user"
        elif current_sender_value == MessageSender.AI.value:
            role_for_openai = "assistant"
        else:
            logger.warning(f"Unexpected sender value: {current_sender_value} for message ID {msg.id}. Defaulting role to 'user'.")
            role_for_openai = "user"

        history.append({"role": role_for_openai, "content": msg.content})
    return history

async def create_chat_message(
    db: AsyncSession,
    session_id: uuid.UUID,
    content: str,
    user_id: Optional[uuid.UUID] = None,
    sender_type: str = "USER"
) -> ChatMessage:
    """
    チャットメッセージを作成する
    
    Args:
        db: データベースセッション
        session_id: セッションID
        content: メッセージ内容
        user_id: ユーザーID（AIの場合はNone）
        sender_type: 送信者タイプ（"USER" or "AI" or "SYSTEM"）
    
    Returns:
        ChatMessage: 作成されたメッセージ
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