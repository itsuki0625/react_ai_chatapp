import os
import json
import asyncio
import httpx
import logging
from fastapi import HTTPException
from datetime import datetime
from app.core.config import settings
from typing import List, Dict, AsyncGenerator

logger = logging.getLogger(__name__)

async def stream_openai_response(messages: List[Dict], session_id: str):
    logger.info(f"Sending to OpenAI: {messages}")
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "gpt-4-mini",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000,
        "stream": True
    }

    try:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=30.0,
            ) as response:
                if response.status_code != 200:
                    logger.error(f"Error from OpenAI: {response.status_code}")
                    raise HTTPException(status_code=500, detail="An Error Occurred")
                
                async for chunk in response.aiter_lines():
                    if chunk.startswith("data: "):
                        try:
                            if chunk[6:] == "[DONE]":
                                break
                            json_line = json.loads(chunk[6:])
                            content = json_line["choices"][0]["delta"].get("content","")
                            
                            if content:
                                logger.info(f"Sending response: {content}")
                                response_data = {
                                    "content": content,
                                    "sender": "AI",
                                    "timestamp": datetime.now().isoformat()
                                }
                                yield f"data: {json.dumps(response_data,ensure_ascii=False)}\n\n"

                        except json.JSONDecodeError:
                            logger.error(f"Error decoding JSON: {chunk}")
                            continue
                        except Exception as e:
                            logger.error(f"Error: {str(e)}")
                            continue
    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An Error Occurred{str(e)}") 