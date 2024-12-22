from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from typing import List, Dict
import httpx
import json
from datetime import datetime
import logging
from app.schemas.chat import ChatRequest, ChatResponse, Message
from app.core.config import settings
from app.services.openai_service import stream_openai_response
import uuid

router = APIRouter()

# ロギング設定
logger = logging.getLogger(__name__)

@router.post("/chat/stream")
async def chat_stream(
    request: Request,
    chat_request: ChatRequest,
):
    logger.info(f"Received message: {chat_request.message}")
    session = request.session
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())

    try:
        logger.info(f"Chat request: {chat_request.message}")
        formatted_history = [
            {
                "role": "assistant" if msg.sender.lower() == "ai" else "user",
                "content": msg.text
            }
            for msg in chat_request.history
        ]
        messages = [
            {"role": "system", "content": settings.INSTRUCTION},
            *formatted_history,
            {"role": "user", "content": chat_request.message}
        ]

        logger.info(f"Formatted Messages: {messages}")

        return StreamingResponse(
            stream_openai_response(messages, session["session_id"]),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache", 
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="An Error Occurred")

@router.get("/session")
async def get_session(request: Request):
    if "session_id" not in request.session:
        request.session["session_id"] = str(uuid.uuid4())
    return {"session_id": request.session["session_id"]}

@router.delete("/session")
async def end_session(request: Request):
    request.session.clear()
    return {"message": "Session ended successfully"}