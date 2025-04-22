from sqlalchemy.orm import Session, joinedload
from app.models.communication import Conversation, Message
from app.models.user import User
from app.schemas.communication import ConversationCreate, MessageCreate
from typing import List, Optional, Dict, Any
from uuid import UUID
import uuid
from datetime import datetime
from sqlalchemy import desc, or_, and_

def create_conversation(db: Session, conversation: ConversationCreate, user_id: UUID) -> Conversation:
    """新しい会話を作成する"""
    # 相手のユーザーが存在するか確認
    recipient = db.query(User).filter(User.id == conversation.recipient_id).first()
    if not recipient:
        raise ValueError("指定された受信者が見つかりません")
    
    # 既存の会話があるか確認
    existing_conversation = db.query(Conversation).filter(
        or_(
            and_(Conversation.user1_id == user_id, Conversation.user2_id == conversation.recipient_id),
            and_(Conversation.user1_id == conversation.recipient_id, Conversation.user2_id == user_id)
        )
    ).first()
    
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
    db.flush()
    
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
    
    db.commit()
    db.refresh(db_conversation)
    return db_conversation

def get_conversation_by_id(db: Session, conversation_id: str) -> Optional[Conversation]:
    """会話をIDで取得する"""
    return db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).options(
        joinedload(Conversation.user1),
        joinedload(Conversation.user2)
    ).first()

def get_user_conversations(db: Session, user_id: UUID, skip: int = 0, limit: int = 20) -> List[Conversation]:
    """ユーザーの会話一覧を取得する"""
    # ユーザーが参加している会話を取得（最新のメッセージ順）
    conversations = db.query(Conversation).filter(
        or_(
            Conversation.user1_id == user_id,
            Conversation.user2_id == user_id
        )
    ).options(
        joinedload(Conversation.user1),
        joinedload(Conversation.user2),
        joinedload(Conversation.messages)
    ).order_by(
        desc(Conversation.updated_at)
    ).offset(skip).limit(limit).all()
    
    # 各会話に対して未読メッセージ数と最新メッセージを追加
    for conversation in conversations:
        # 相手ユーザー情報を設定
        if str(conversation.user1_id) == str(user_id):
            conversation.recipient = conversation.user2
        else:
            conversation.recipient = conversation.user1
        
        # 最新メッセージを取得
        latest_message = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(desc(Message.created_at)).first()
        
        conversation.last_message = latest_message
        
        # 未読メッセージ数を取得
        unread_count = db.query(Message).filter(
            Message.conversation_id == conversation.id,
            Message.sender_id != user_id,
            Message.read == False
        ).count()
        
        conversation.unread_count = unread_count
    
    return conversations

def create_message(db: Session, conversation_id: UUID, sender_id: UUID, content: str, message_type: str = "text") -> Message:
    """メッセージを作成する"""
    # 会話の存在確認
    conversation = get_conversation_by_id(db, str(conversation_id))
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
    
    db.commit()
    db.refresh(db_message)
    return db_message

def get_conversation_messages(db: Session, conversation_id: UUID, skip: int = 0, limit: int = 50) -> List[Message]:
    """会話のメッセージ一覧を取得する"""
    return db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).options(
        joinedload(Message.sender)
    ).order_by(
        desc(Message.created_at)
    ).offset(skip).limit(limit).all()

def mark_messages_as_read(db: Session, conversation_id: UUID, user_id: UUID) -> int:
    """特定の会話の未読メッセージを既読にする"""
    # 自分が送信していないメッセージを既読にする
    result = db.query(Message).filter(
        Message.conversation_id == conversation_id,
        Message.sender_id != user_id,
        Message.read == False
    ).update({"read": True})
    
    db.commit()
    return result

def get_unread_count(db: Session, user_id: UUID) -> int:
    """ユーザーの全ての未読メッセージ数を取得する"""
    # ユーザーが参加している全ての会話の未読メッセージ数を合計
    conversations = db.query(Conversation).filter(
        or_(
            Conversation.user1_id == user_id,
            Conversation.user2_id == user_id
        )
    ).all()
    
    total_unread = 0
    for conversation in conversations:
        unread_count = db.query(Message).filter(
            Message.conversation_id == conversation.id,
            Message.sender_id != user_id,
            Message.read == False
        ).count()
        
        total_unread += unread_count
    
    return total_unread 