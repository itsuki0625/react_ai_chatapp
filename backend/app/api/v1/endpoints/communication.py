from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from app.api.deps import get_current_user, get_async_db, require_permission
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
    current_user: User = Depends(require_permission('communication_write')),
    db: AsyncSession = Depends(get_async_db)
):
    """
    新しい会話を開始する ('communication_write' 権限が必要)
    """
    try:
        new_conversation = await create_conversation(db, conversation, current_user.id)
        return new_conversation
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="会話の開始中にエラーが発生しました")

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    current_user: User = Depends(require_permission('communication_read')),
    db: AsyncSession = Depends(get_async_db),
    skip: int = 0,
    limit: int = 20
):
    """
    ユーザーの会話一覧を取得 ('communication_read' 権限が必要)
    """
    conversations = await get_user_conversations(db, current_user.id, skip, limit)
    return conversations

@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(require_permission('communication_read')),
    db: AsyncSession = Depends(get_async_db)
):
    """
    特定の会話の詳細を取得 ('communication_read' 権限が必要)
    """
    conversation = await get_conversation_by_id(db, conversation_id)
    if not conversation or (current_user.id not in [conversation.user1_id, conversation.user2_id]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会話が見つからないか、アクセス権限がありません"
        )
    return conversation

@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    message: MessageCreate,
    current_user: User = Depends(require_permission('communication_write')),
    db: AsyncSession = Depends(get_async_db)
):
    """
    メッセージを送信 ('communication_write' 権限が必要)
    """
    try:
        conversation = await get_conversation_by_id(db, conversation_id)
        if not conversation or (current_user.id not in [conversation.user1_id, conversation.user2_id]):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会話が見つからないか、メッセージを送信する権限がありません"
            )

        new_message = await create_message(
            db=db,
            conversation_id=conversation.id,
            sender_id=current_user.id,
            content=message.content,
            message_type=message.message_type
        )
        return new_message
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="メッセージ送信中にエラーが発生しました")

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    current_user: User = Depends(require_permission('communication_read')),
    db: AsyncSession = Depends(get_async_db),
    skip: int = 0,
    limit: int = 50,
    mark_read: bool = True
):
    """
    会話のメッセージ履歴を取得 ('communication_read' 権限が必要)
    """
    conversation = await get_conversation_by_id(db, conversation_id)
    if not conversation or (current_user.id not in [conversation.user1_id, conversation.user2_id]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会話が見つからないか、アクセス権限がありません"
        )

    messages = await get_conversation_messages(db, conversation.id, skip, limit)

    if mark_read:
        await mark_messages_as_read(db, conversation.id, current_user.id)

    return messages

@router.get("/unread-count")
async def get_unread_message_count(
    current_user: User = Depends(require_permission('communication_read')),
    db: AsyncSession = Depends(get_async_db)
):
    """
    未読メッセージ数を取得 ('communication_read' 権限が必要)
    """
    count = await get_unread_count(db, current_user.id)
    return {"unread_count": count}

@router.post("/conversations/{conversation_id}/read")
async def mark_conversation_as_read(
    conversation_id: str,
    current_user: User = Depends(require_permission('communication_read')),
    db: AsyncSession = Depends(get_async_db)
):
    """
    会話のすべてのメッセージを既読にする ('communication_read' 権限が必要)
    """
    conversation = await get_conversation_by_id(db, conversation_id)
    if not conversation or (current_user.id not in [conversation.user1_id, conversation.user2_id]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会話が見つからないか、アクセス権限がありません"
        )

    await mark_messages_as_read(db, conversation.id, current_user.id)
    return {"message": "すべてのメッセージを既読にしました"} 