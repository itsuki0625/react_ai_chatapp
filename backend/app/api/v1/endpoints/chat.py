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

router = APIRouter()

# ロギング設定
logger = logging.getLogger(__name__)

@router.post("/chat/stream")
async def chat_stream(
    request: Request,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    logger.info(f"Received message: {chat_request.message}")
    
    # セッションの初期化を確実に行う
    if not hasattr(request, 'session'):
        request.session = {}
    
    # セッションIDがない場合は新規作成
    if "session_id" not in request.session:
        request.session["session_id"] = str(uuid.uuid4())
        logger.info(f"Created new session_id: {request.session['session_id']}")
    
    try:
        logger.info(f"Chat request: {chat_request.message}")
        formatted_history = [
            {
                "role": "assistant" if msg.sender.lower() == "ai" else "user",
                "content": msg.text
            }
            for msg in chat_request.history
        ]
        
        system_message = settings.INSTRUCTION
        
        messages = [
            {"role": "system", "content": system_message},
            *formatted_history,
            {"role": "user", "content": chat_request.message}
        ]

        logger.info(f"Formatted Messages: {messages}")

        return StreamingResponse(
            stream_openai_response(messages, request.session["session_id"]),
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