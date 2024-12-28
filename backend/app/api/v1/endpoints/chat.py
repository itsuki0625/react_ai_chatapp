from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from typing import List, Dict
from datetime import datetime
import logging
from app.schemas.chat import ChatRequest, ChatResponse, Message
from app.core.config import settings
from app.services.openai_service import stream_openai_response
import uuid
from openai import AsyncOpenAI
from app.api.deps import get_current_user, User
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.crud.chat import get_or_create_chat_session, get_session_messages, save_chat_message, get_user_chat_sessions, update_session_title, update_session_status, get_archived_chat_sessions
from fastapi.middleware.cors import CORSMiddleware

router = APIRouter()

# ロギング設定
logger = logging.getLogger(__name__)

@router.options("/chat/stream")
async def chat_stream_options():
    return {"message": "OK"}

@router.post("/chat/stream")
async def chat_stream(
    request: Request,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"Received message: {chat_request.message}")
    logger.info(f"Chat request: {chat_request}")
    
    try:
        # チャットセッションを取得または作成
        chat_session = await get_or_create_chat_session(
            db=db,
            user_id=current_user.id,
            session_id=chat_request.session_id,
            session_type=chat_request.session_type
        )
        print("セッションの作成に成功しました")
        
        # セッションIDを保持
        session_id = str(chat_session.id)
        print("セッションIDの保持に成功しました")
        
        # 新しいセッションの場合のみタイトルを更新
        if not chat_request.session_id:
            title = chat_request.message[:30] + "..." if len(chat_request.message) > 30 else chat_request.message
            await update_session_title(
                db, 
                chat_session.id, 
                current_user.id, 
                title
            )
        print("セッションのタイトルの更新に成功しました")

        # ユーザーメッセージを保存
        user_message = await save_chat_message(
            db=db,
            session_id=session_id,
            content=chat_request.message,
            sender_id=current_user.id,
            sender_type="USER"
        )
        print("ユーザーメッセージの保存に成功しました")

        # 既存のメッセージ履歴を取得
        session_messages = await get_session_messages(
            db, 
            session_id, 
            current_user.id,
            chat_request.session_type
        )
        print("既存のメッセージ履歴の取得に成功しました")
        formatted_history = [
            {
                "role": "assistant" if msg.sender_type == "AI" else "user",
                "content": msg.content
            }
            for msg in session_messages
        ]
        print("メッセージ履歴のフォーマットに成功しました")

        # セッションタイプに応じてシステムメッセージを設定
        if chat_request.session_type == "FAQ":
            system_message = "あなたは総合型選抜に関する質問に答えるFAQボットです。"
        else:
            system_message = settings.INSTRUCTION
        print("システムメッセージの設定に成功しました")
        
        messages = [
            {"role": "system", "content": system_message},
            *formatted_history,
            {"role": "user", "content": chat_request.message}
        ]

        # AIメッセージを作成（内容は空で）
        ai_message = await save_chat_message(
            db=db,
            session_id=session_id,
            content="",
            sender_type="AI"
        )
        print("AIメッセージの保存に成功しました")

        async def stream_and_save():
            full_response = ""
            async for chunk in stream_openai_response(messages, session_id):
                if isinstance(chunk, str):
                    sanitized = chunk.replace("data: ", "").strip()
                    full_response += sanitized
                    yield f'data: {sanitized}\n\n'
            
            # ストリーミング完了後、完全なAIレスポンスを保存
            ai_message.content = full_response.replace("[DONE]", "").strip()
            db.add(ai_message)
            db.commit()
            
            # 終了を示すメッセージ
            yield 'data: [DONE]\n\n'
        print("ストリーミングの終了を示すメッセージの送信に成功しました")

        return StreamingResponse(
            stream_and_save(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

    except Exception as e:
        logger.error(f"Error in chat_stream: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session")
async def get_session(request: Request):
    if "session_id" not in request.session:
        request.session["session_id"] = str(uuid.uuid4())
    return {"session_id": request.session["session_id"]}

@router.delete("/session")
async def end_session(request: Request):
    request.session.clear()
    return {"message": "Session ended successfully"}

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        logger.info(f"Sending to OpenAI: {chat_request.message}")
        
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        system_message = "あなたは就職活動中の学生の自己分析をサポートするAIアシスタントです。"
        
        messages = [
            {"role": "system", "content": system_message},
        ]
        
        if chat_request.history:
            formatted_history = [
                {
                    "role": "assistant" if msg.sender.lower() == "ai" else "user",
                    "content": msg.text
                }
                for msg in chat_request.history
            ]
            messages.extend(formatted_history)
        
        messages.append({"role": "user", "content": chat_request.message})
        
        logger.info(f"Full message history: {messages}")
        
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        response_content = response.choices[0].message.content
        logger.info(f"Received response from OpenAI: {response_content}")
        
        return ChatResponse(
            reply=response_content,
            timestamp=datetime.now().isoformat(),
            session_id=str(uuid.uuid4())
        )
    except Exception as e:
        logger.error(f"Error in chat_with_ai: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/sessions")
async def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    session_type: str = "CONSULTATION"
):
    """ユーザーのチャットセッション一覧を取得"""
    try:
        print(session_type)
        sessions = await get_user_chat_sessions(
            db, 
            current_user.id,
            session_type
        )
        return sessions
    except Exception as e:
        logger.error(f"Error getting chat sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/sessions/{session_id}/messages")
async def get_chat_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    session_type: str = "CONSULTATION"
):
    """特定のセッションのメッセージ履歴を取得"""
    try:
        messages = await get_session_messages(
            db, 
            session_id, 
            current_user.id,
            session_type
        )
        return messages
    except Exception as e:
        logger.error(f"Error getting chat messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/chat/sessions/{session_id}/archive")
async def archive_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    session_type: str = "CONSULTATION"
):
    """チャットセッションを非表示（アーカイブ）にする"""
    try:
        await update_session_status(
            db, 
            session_id, 
            current_user.id, 
            "ARCHIVED",
            session_type
        )
        return {"message": "Session archived successfully"}
    except Exception as e:
        logger.error(f"Error archiving chat session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/sessions/archived")
async def get_archived_chat_sessions_route(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    session_type: str = "CONSULTATION"
):
    """アーカイブされたチャットセッションを取得"""
    try:
        sessions = await get_archived_chat_sessions(
            db, 
            current_user.id,
            session_type
        )
        return sessions
    except Exception as e:
        logger.error(f"Error getting archived chat sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
    
@router.patch("/chat/sessions/{session_id}/restore")
async def restore_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    session_type: str = "CONSULTATION"
):
    """チャットセッションをアクティブにする"""
    try:
        await update_session_status(
            db, 
            session_id, 
            current_user.id, 
            "ACTIVE",
            session_type
        )
        return {"message": "Session restored successfully"}
    except Exception as e:
        logger.error(f"Error restoring chat session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
