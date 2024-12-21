import os
from fastapi import FastAPI, HTTPException,Request,Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional,Dict
import httpx
from dotenv import load_dotenv
from datetime import datetime
import logging
import json
from starlette.middleware.sessions import SessionMiddleware
import uuid
import secrets

# .envファイルから環境変数をロード
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
print(api_key)
if not api_key:
    raise ValueError("OPENAI_API_KEY is not set in environment variables")

app = FastAPI()

# セッション設定
SECRET_KEY = os.getenv("SECRET_KEY")

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CORSの設定（必要に応じてオリジンを調整）
origins = [
    "http://localhost:3000",  # すべてのオリジンを許可。運用時には特定のオリジンに変更することを推奨。
    "http://localhost:80",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 例: ["http://localhost", "https://yourdomain.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# リクエストおよびレスポンスのPydanticモデル定義

class Message(BaseModel):
    sender: str
    text: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Message]] = []

class ChatResponse(BaseModel):
    reply: str
    timestamp: str
    session_id: str


# サーバー起動時にinstruction.mdを読み込む
try:
    with open('./instruction.md', 'r', encoding='utf-8') as f:
        instruction = f.read()
except FileNotFoundError:
    instruction = ""
    logger.warning("instruction.mdが見つかりません。システム指示なしで進行します。")


async def stream_openai_response(messages:List[Dict],session_id:str):
    logger.info(f"Sending to OpenAI: {messages}")
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000,
        "stream":True
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


# チャットエンドポイント
@app.post("/chat/stream")
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
            {"role": "system", "content": instruction},
            *formatted_history,
            {"role": "user", "content": chat_request.message}
        ]

        logger.info(f"Formatted Messages: {messages}")

        return StreamingResponse(
            stream_openai_response(messages,session["session_id"]),
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

@app.get("/session")
async def get_session(request: Request):
    if "session_id" not in request.session:
        request.session["session_id"] = str(uuid.uuid4())
    return {"session_id": request.session["session_id"]}

@app.delete("/session")
async def end_session(request: Request):
    request.session.clear()
    return {"message": "Session ended successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)