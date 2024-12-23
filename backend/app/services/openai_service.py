import os
import json
import asyncio
import httpx
import logging
from fastapi import HTTPException
from datetime import datetime
from app.core.config import settings
from typing import List, Dict, AsyncGenerator
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def stream_openai_response(messages: List[Dict], session_id: str):
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            stream=True,
            temperature=0.7
        )
        
        async for chunk in response:
            if chunk.choices[0].delta.content is not None:
                yield f"data: {chunk.choices[0].delta.content}\n\n"
        
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Error from OpenAI: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 