from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.communication import (
    MessageCreate,
    MessageResponse,
    ConversationResponse,
    ConversationCreate
)
from app.crud.communication import (
    create_message,
    get_user_conversations,
    get_conversation_messages,
    mark_messages_as_read,
    get_unread_count,
    create_conversation,
    get_conversation_by_id
)

router = APIRouter()

@router.post("/conversations", response_model=ConversationResponse)
async def start_conversation(
    conversation: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    新しい会話を開始する
    """
    return create_conversation(db, conversation, current_user.id)

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20
):
    """
    ユーザーの会話一覧を取得
    """
    return get_user_conversations(db, current_user.id, skip, limit)

@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    特定の会話の詳細を取得
    """
    conversation = get_conversation_by_id(db, conversation_id)
    if not conversation or (current_user.id not in [str(conversation.user1_id), str(conversation.user2_id)]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会話が見つからないか、アクセス権限がありません"
        )
    return conversation

@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    メッセージを送信
    """
    # 会話の存在とアクセス権限を確認
    conversation = get_conversation_by_id(db, conversation_id)
    if not conversation or (current_user.id not in [str(conversation.user1_id), str(conversation.user2_id)]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会話が見つからないか、アクセス権限がありません"
        )
    
    # メッセージを保存
    return create_message(
        db=db,
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=message.content,
        message_type=message.message_type
    )

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
    mark_read: bool = True
):
    """
    会話のメッセージ履歴を取得
    """
    # 会話の存在とアクセス権限を確認
    conversation = get_conversation_by_id(db, conversation_id)
    if not conversation or (current_user.id not in [str(conversation.user1_id), str(conversation.user2_id)]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会話が見つからないか、アクセス権限がありません"
        )
    
    # メッセージを取得
    messages = get_conversation_messages(db, conversation_id, skip, limit)
    
    # 必要に応じて未読メッセージを既読に
    if mark_read:
        mark_messages_as_read(db, conversation_id, current_user.id)
    
    return messages

@router.get("/unread-count")
async def get_unread_message_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    未読メッセージ数を取得
    """
    count = get_unread_count(db, current_user.id)
    return {"unread_count": count}

@router.post("/conversations/{conversation_id}/read")
async def mark_conversation_as_read(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    会話のすべてのメッセージを既読にする
    """
    # 会話の存在とアクセス権限を確認
    conversation = get_conversation_by_id(db, conversation_id)
    if not conversation or (current_user.id not in [str(conversation.user1_id), str(conversation.user2_id)]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会話が見つからないか、アクセス権限がありません"
        )
    
    mark_messages_as_read(db, conversation_id, current_user.id)
    return {"message": "すべてのメッセージを既読にしました"} 