from sqlalchemy.orm import Session, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_, and_, update as sql_update, func
from app.models.communication import Conversation, Message
from app.models.user import User
from app.schemas.communication import ConversationCreate, MessageCreate
from typing import List, Optional, Dict, Any
from uuid import UUID
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def create_conversation(db: AsyncSession, conversation: ConversationCreate, user_id: UUID) -> Conversation:
    """新しい会話を作成する"""
    # 相手のユーザーが存在するか確認
    result_user = await db.execute(select(User).filter(User.id == conversation.recipient_id))
    recipient = result_user.scalars().first()
    if not recipient:
        raise ValueError("指定された受信者が見つかりません")
    
    # 既存の会話があるか確認
    stmt_existing = select(Conversation).filter(
        or_(
            and_(Conversation.user1_id == user_id, Conversation.user2_id == conversation.recipient_id),
            and_(Conversation.user1_id == conversation.recipient_id, Conversation.user2_id == user_id)
        )
    )
    result_existing = await db.execute(stmt_existing)
    existing_conversation = result_existing.scalars().first()
    
    if existing_conversation:
        # 既存の会話を返す
        return existing_conversation
    
    # 新しい会話を作成
    db_conversation = Conversation(
        id=uuid.uuid4(),
        title=conversation.title,
        user1_id=user_id,
        user2_id=conversation.recipient_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_conversation)
    await db.flush()
    
    # 初期メッセージがある場合は追加
    if conversation.initial_message:
        db_message = Message(
            id=uuid.uuid4(),
            conversation_id=db_conversation.id,
            sender_id=user_id,
            content=conversation.initial_message,
            message_type="text",
            read=False,
            created_at=datetime.utcnow()
        )
        db.add(db_message)
    
    await db.commit()
    await db.refresh(db_conversation)
    return db_conversation

async def get_conversation_by_id(db: AsyncSession, conversation_id: str) -> Optional[Conversation]:
    """会話をIDで取得する"""
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        logger.error(f"Invalid UUID format for conversation_id: {conversation_id}")
        return None
    stmt = select(Conversation).filter(
        Conversation.id == conv_uuid
    ).options(
        joinedload(Conversation.user1),
        joinedload(Conversation.user2)
    )
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_user_conversations(db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 20) -> List[Conversation]:
    """ユーザーの会話一覧を取得する"""
    # ユーザーが参加している会話を取得（最新のメッセージ順）
    stmt = select(Conversation).filter(
        or_(
            Conversation.user1_id == user_id,
            Conversation.user2_id == user_id
        )
    ).options(
        joinedload(Conversation.user1),
        joinedload(Conversation.user2),
        # joinedload(Conversation.messages) # Avoid loading all messages initially
    ).order_by(
        desc(Conversation.updated_at)
    ).offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    conversations = result.scalars().all()
    
    # 各会話に対して未読メッセージ数と最新メッセージを追加
    for conversation in conversations:
        # 相手ユーザー情報を設定
        if str(conversation.user1_id) == str(user_id):
            conversation.recipient = conversation.user2
        else:
            conversation.recipient = conversation.user1
        
        # 最新メッセージを取得
        stmt_latest = select(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(desc(Message.created_at)).limit(1)
        result_latest = await db.execute(stmt_latest)
        conversation.last_message = result_latest.scalars().first()
        
        # 未読メッセージ数を取得
        stmt_unread = select(func.count(Message.id)).select_from(Message).filter(
            Message.conversation_id == conversation.id,
            Message.sender_id != user_id,
            Message.read == False
        )
        result_unread = await db.execute(stmt_unread)
        conversation.unread_count = result_unread.scalar_one()
    
    return conversations

async def create_message(db: AsyncSession, conversation_id: UUID, sender_id: UUID, content: str, message_type: str = "text") -> Message:
    """メッセージを作成する"""
    # 会話の存在確認
    conversation = await get_conversation_by_id(db, str(conversation_id))
    if not conversation:
        raise ValueError("指定された会話が見つかりません")
    
    # メッセージを作成
    db_message = Message(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        sender_id=sender_id,
        content=content,
        message_type=message_type,
        read=False,
        created_at=datetime.utcnow()
    )
    db.add(db_message)
    
    # 会話の更新日時を更新
    conversation.updated_at = datetime.utcnow()
    db.add(conversation)
    
    await db.commit()
    await db.refresh(db_message)
    return db_message

async def get_conversation_messages(db: AsyncSession, conversation_id: UUID, skip: int = 0, limit: int = 50) -> List[Message]:
    """会話のメッセージ一覧を取得する"""
    stmt = select(Message).filter(
        Message.conversation_id == conversation_id
    ).options(
        joinedload(Message.sender)
    ).order_by(
        desc(Message.created_at)
    ).offset(skip).limit(limit)
    result = await db.execute(stmt)
    # Reverse the list to get oldest first within the limit
    return list(reversed(result.scalars().all()))

async def mark_messages_as_read(db: AsyncSession, conversation_id: UUID, user_id: UUID) -> int:
    """特定の会話の未読メッセージを既読にする"""
    # 自分が送信していないメッセージを既読にする
    stmt = sql_update(Message).where(
        Message.conversation_id == conversation_id,
        Message.sender_id != user_id,
        Message.read == False
    ).values(read=True)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount

async def get_unread_count(db: AsyncSession, user_id: UUID) -> int:
    """ユーザーの全ての未読メッセージ数を取得する"""
    # Get IDs of conversations the user is part of
    stmt_conv_ids = select(Conversation.id).filter(
        or_(Conversation.user1_id == user_id, Conversation.user2_id == user_id)
    )
    result_conv_ids = await db.execute(stmt_conv_ids)
    conversation_ids = result_conv_ids.scalars().all()

    if not conversation_ids:
        return 0

    # Count unread messages across those conversations
    stmt_unread = select(func.count(Message.id)).select_from(Message).where(
        Message.conversation_id.in_(conversation_ids),
        Message.sender_id != user_id,
        Message.read == False
    )
    result_unread = await db.execute(stmt_unread)
    return result_unread.scalar_one() 