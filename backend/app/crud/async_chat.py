from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
import uuid

from app.models import chat as chat_models
from app.models import user as user_models
# from app.enums import ChatType # 古いインポートパスを削除
from app.models.enums import ChatType # 新しいインポートパスに変更
from app.models.enums import SessionStatus

# --- 非同期 ChatSession CRUD ---

async def get_user_chat_sessions(
    db: AsyncSession,
    user_id: uuid.UUID,
    chat_type: Optional[ChatType] = None,
    status: Optional[SessionStatus] = None
) -> List[chat_models.ChatSession]:
    """
    指定されたユーザーのチャットセッションを非同期で取得します。
    オプションで chat_type と status によるフィルタリングが可能です。
    """
    stmt = select(chat_models.ChatSession).where(chat_models.ChatSession.user_id == user_id)
    if chat_type:
        stmt = stmt.where(chat_models.ChatSession.chat_type == chat_type.value)
    if status:
        stmt = stmt.where(chat_models.ChatSession.status == str(status.value))

    stmt = stmt.order_by(chat_models.ChatSession.updated_at.desc())
    
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    return list(sessions) # 結果をリストにして返す

# --- 他の非同期CRUD関数も必要に応じてここに追加 --- 
# 例: async def get_chat_session_by_id(...) など 