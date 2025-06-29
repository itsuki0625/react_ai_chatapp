from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks, status, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import StreamingResponse
from typing import List, Dict, Optional
from datetime import datetime
import logging
from app.schemas.chat import ChatRequest, ChatResponse, Message, ChatMessageCreate, ChatMessage as ChatMessageSchema, ChatSessionCreate, ChatType, ChatSessionStatus, ChatSessionSummary, ChatSession, ChatMessageResponse
from app.core.config import settings
from app.services.openai_service import stream_openai_response
import uuid
from openai import AsyncOpenAI
from app.api.deps import get_current_user, User, require_permission, get_current_user_from_token, check_permissions_for_user
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_async_db
from app.crud.chat import (
    get_or_create_chat_session,
    get_session_messages,
    save_chat_message,
    get_user_chat_sessions,
    update_session_title,
    update_session_status,
    get_archived_chat_sessions,
    get_chat_session_by_id,
    get_chat_messages as get_chat_messages_history
)
from fastapi.middleware.cors import CORSMiddleware
from app.crud.checklist import (
    ChecklistEvaluator,
    create_evaluation_records,
    get_evaluation_by_session_id,
    update_evaluation_for_session
)
from uuid import UUID
from sqlalchemy.orm import Session
from app import models, crud
from app.api import deps
from app.models.chat import MessageSender
from app.services.ai_service import get_self_analysis_agent_response
from app.services.agents.self_analysis_langchain.main import SelfAnalysisOrchestrator
from app.crud.async_chat import get_user_chat_sessions
import json
import asyncio
from app.models.enums import ChatType as ChatTypeEnum, SessionStatus as ChatSessionStatusEnum # Enumを別名でインポート
from starlette.websockets import WebSocketState # WebSocketState をインポート

router = APIRouter()

# ロギング設定
logger = logging.getLogger(__name__)

checklist_evaluator = ChecklistEvaluator()

class WebSocketTraceHandler(logging.Handler):
    def __init__(self, websocket: WebSocket, session_id: str):
        super().__init__()
        self.websocket = websocket
        self.session_id = session_id
    def emit(self, record):
        try:
            msg = self.format(record)
            asyncio.create_task(
                self.websocket.send_text(json.dumps({"type": "trace", "content": msg, "session_id": self.session_id}))
            )
        except Exception:
            pass

@router.websocket("/ws/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_async_db)
):
    await websocket.accept()
    logger.info(f"WebSocket connection accepted from: {websocket.client}")
    current_user: Optional[User] = None
    token = websocket.query_params.get("token")
    session_id_from_request: Optional[UUID] = None # ChatRequestから取得するセッションID

    try:
        if not token:
            logger.warning("Token not provided in query params for WebSocket.")
            await websocket.send_text(json.dumps({"type": "error", "detail": "Authentication token required."}))
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token not provided")
            return

        current_user = await get_current_user_from_token(token, db)
        
        logger.info(f"User {current_user.email} authenticated for WebSocket chat.")

        if not await check_permissions_for_user(current_user, ('chat_message_send',)):
            logger.warning(f"User {current_user.email} lacks 'chat_message_send' permission for WebSocket.")
            await websocket.send_text(json.dumps({"type": "error", "detail": "Insufficient permissions to send messages."}))
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Insufficient permissions")
            return

        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received raw data via WebSocket from {current_user.email}: {data[:200]}")

            try:
                chat_request_data = json.loads(data)
                if 'chat_type' in chat_request_data and isinstance(chat_request_data['chat_type'], str):
                    chat_request_data['chat_type'] = chat_request_data['chat_type'].lower().replace('-', '_')
                chat_request = ChatRequest(**chat_request_data)
                session_id_from_request = chat_request.session_id
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from {current_user.email}: {data}")
                await websocket.send_text(json.dumps({"type": "error", "detail": "Invalid JSON format"}))
                continue
            except Exception as e:
                logger.error(f"Error parsing ChatRequest from {current_user.email}: {str(e)}. Data: {data}")
                await websocket.send_text(json.dumps({"type": "error", "detail": f"Invalid request payload: {str(e)}"}))
                continue

            logger.info(f"Processing chat request for user {current_user.email}, session: {chat_request.session_id}, type: {chat_request.chat_type}")

            chat_session = await get_or_create_chat_session(
                db=db,
                user_id=current_user.id,
                session_id=chat_request.session_id, # ここで UUID オブジェクトが渡される可能性がある
                chat_type=chat_request.chat_type.value
            )
            actual_session_id = str(chat_session.id)
            logger.info(f"Using chat session ID: {actual_session_id}")

            # タイトルが未設定または"新規チャット"の場合は自動生成
            if (not chat_session.title or chat_session.title == "新規チャット" or chat_session.title == "無題のチャット") and chat_request.message:
                try:
                    user_message_prefix = chat_request.message.replace('\n', ' ').strip()
                    title = user_message_prefix[:30].strip() + "..." if len(user_message_prefix) > 30 else user_message_prefix.strip()
                    if title:
                        await update_session_title(db, chat_session.id, current_user.id, title)
                        logger.info(f"Session title updated to '{title}' for session {actual_session_id}")
                except Exception as e:
                    logger.error(f"Failed to update session title for {actual_session_id}: {e}", exc_info=True)
            
            user_message_db_obj = await save_chat_message(
                db=db, session_id=UUID(actual_session_id), content=chat_request.message,
                user_id=current_user.id, sender_type="USER"
            )
            logger.info(f"User message saved (ID: {user_message_db_obj.id}) for session {actual_session_id}")

            session_messages_history = await get_chat_messages_history(db, actual_session_id)
            formatted_history = []
            if isinstance(session_messages_history, list):
                for msg_item in session_messages_history:
                    if isinstance(msg_item, dict):
                        formatted_history.append({"role": msg_item.get("role", "unknown"), "content": msg_item.get("content", "")})
                    else: logger.warning(f"Unexpected item type in session_messages_history: {type(msg_item)}")
            
            system_message_content = settings.INSTRUCTION
            if chat_request.chat_type == ChatTypeEnum.FAQ:
                system_message_content = "あなたは総合型選抜に関する質問に答えるFAQボットです。"

            # messages_for_openai の準備段階
            temp_messages = [
                {"role": "system", "content": system_message_content},
                *formatted_history,
            ]
            # ユーザーの最新メッセージを追加 (重複を避けるチェックはそのまま)
            if not any(m['role'] == 'user' and m['content'] == chat_request.message for m in formatted_history):
                 temp_messages.append({"role": "user", "content": chat_request.message})
            
            # OpenAI APIに渡す最終的な messages_for_openai リストを生成
            # ここで 'ai' ロールを 'assistant' に強制的に変換する
            messages_for_openai = []
            for msg in temp_messages:
                role = msg.get("role")
                content = msg.get("content")
                # MessageSender.AI.value は "ai"
                if role == MessageSender.AI.value: 
                    messages_for_openai.append({"role": "assistant", "content": content})
                elif role in ["user", "system", "assistant"]: # 有効なロールはそのまま
                    messages_for_openai.append({"role": role, "content": content})
                else: # 不明なロールの場合はログを残し、'user'ロールとして扱う (またはエラー処理)
                    logger.warning(f"Unknown role '{role}' in message preparation for OpenAI. Original message: {msg}")
                    messages_for_openai.append({"role": "user", "content": content}) # 安全策

            # デバッグログで変換後の内容を確認
            logger.debug(f"Final messages for OpenAI API: {messages_for_openai}")

            ai_message_db_obj = await save_chat_message(
                db=db, session_id=UUID(actual_session_id), content="", sender_type="AI"
            )
            logger.info(f"Empty AI message saved (ID: {ai_message_db_obj.id}) for session {actual_session_id}")
            await db.commit() # 先にAIメッセージのプレースホルダーをコミット
            await db.refresh(ai_message_db_obj)

            # SELF_ANALYSIS 用 AI Service 呼び出し
            if chat_request.chat_type == ChatTypeEnum.SELF_ANALYSIS:
                # まず簡単なテスト応答を送信
                await websocket.send_text(json.dumps({
                    "type": "test", 
                    "content": "自己分析処理を開始します...",
                    "session_id": actual_session_id
                }))
                
                # Traceログをクライアントに送信するハンドラーを設定
                trace_logger = logging.getLogger("self_analysis_trace")
                ws_handler = WebSocketTraceHandler(websocket, actual_session_id)
                ws_handler.setFormatter(logging.Formatter("%(message)s"))
                trace_logger.addHandler(ws_handler)
                try:
                    logger.info(f"Starting SelfAnalysisOrchestrator for session {actual_session_id}")
                    # 新版LangChain自己分析オーケストレーターを利用
                    orchestrator = SelfAnalysisOrchestrator()
                    logger.info(f"Orchestrator created, calling run with {len(messages_for_openai)} messages")
                    # LangChainオーケストレーター実行 (辞書結果を受け取る)
                    result = await orchestrator.run(messages_for_openai, actual_session_id)
                    logger.info(f"Orchestrator run completed. Result type: {type(result)}, content: {result}")
                    # ユーザー向け応答抽出
                    reply = None
                    if isinstance(result, dict):
                        reply = result.get("user_visible") or result.get("final_notes") or str(result)
                        logger.info(f"Extracted reply from dict result: {reply}")
                    else:
                        reply = str(result)
                        logger.info(f"Using result as string reply: {reply}")
                    
                    if not reply or reply.strip() == "":
                        reply = "申し訳ございませんが、処理中に問題が発生しました。もう一度お試しください。"
                        logger.warning(f"Empty reply detected, using fallback message for session {actual_session_id}")
                    
                    logger.info(f"Final reply to be sent: {reply}")
                except Exception as orchestrator_err:
                    # OpenAI rate limit specific error handling
                    import openai
                    if isinstance(orchestrator_err, openai.RateLimitError):
                        logger.warning(f"OpenAI rate limit reached for session {actual_session_id}: {orchestrator_err}")
                        # Send user-friendly rate limit message
                        rate_limit_message = "申し訳ございませんが、現在APIの利用制限に達しています。少し時間をおいてから再度お試しください。"
                        await websocket.send_text(json.dumps({
                            "type": "error", 
                            "detail": rate_limit_message,
                            "session_id": actual_session_id,
                            "error_code": "rate_limit"
                        }))
                        await websocket.send_text(json.dumps({"type": "done", "session_id": actual_session_id, "error": True}))
                        continue
                    else:
                        # Log the original error and send generic error message
                        logger.error(f"Error in self-analysis orchestrator for session {actual_session_id}: {orchestrator_err}", exc_info=True)
                        await websocket.send_text(json.dumps({
                            "type": "error", 
                            "detail": "AI処理中にエラーが発生しました。しばらく時間をおいてから再度お試しください。",
                            "session_id": actual_session_id
                        }))
                        await websocket.send_text(json.dumps({"type": "done", "session_id": actual_session_id, "error": True}))
                        continue
                finally:
                    # ハンドラーを解除
                    trace_logger.removeHandler(ws_handler)
                # ユーザー向け内容を一括で返す
                await websocket.send_text(json.dumps({"type": "chunk", "content": reply or "", "session_id": actual_session_id}))
                await websocket.send_text(json.dumps({"type": "done", "session_id": actual_session_id}))
                # AI応答をDBに保存
                await save_chat_message(
                    db=db,
                    session_id=UUID(actual_session_id),
                    content=reply or "",
                    sender_type="AI"
                )
                await db.commit()
                continue

            full_ai_response = ""
            try:
                logger.debug(f"Streaming OpenAI response for session {actual_session_id} with {len(messages_for_openai)} messages.")
                async for chunk in stream_openai_response(messages_for_openai, actual_session_id):
                    if isinstance(chunk, str):
                        sanitized_chunk = chunk.replace("data: ", "").strip()
                        if sanitized_chunk == "[DONE]":
                            logger.info(f"Received [DONE] signal from stream_openai_response for session {actual_session_id}")
                            break
                        if sanitized_chunk:
                            full_ai_response += sanitized_chunk
                            await websocket.send_text(json.dumps({"type": "chunk", "content": sanitized_chunk, "session_id": actual_session_id}))
                    else:
                        logger.warning(f"Received non-string chunk from stream: {type(chunk)} for session {actual_session_id}")
                
                logger.info(f"Streaming finished for session {actual_session_id}. Full AI response length: {len(full_ai_response)}")

                if ai_message_db_obj:
                    ai_message_db_obj.content = full_ai_response
                    ai_message_db_obj.updated_at = datetime.utcnow()
                    db.add(ai_message_db_obj)
                    await db.commit()
                    await db.refresh(ai_message_db_obj)
                    logger.info(f"AI response saved/updated for message ID: {ai_message_db_obj.id} in session {actual_session_id}")
                
                # 自己分析評価ロジックは呼び出さない (コメントアウトまたは削除)
                # if chat_request.chat_type == ChatTypeEnum.SELF_ANALYSIS: 
                #     try:
                #         # ... (略) ...
                #     except Exception as eval_e:
                #         logger.error(f"Error during self-analysis evaluation for session {actual_session_id}: {eval_e}", exc_info=True)

                await websocket.send_text(json.dumps({"type": "done", "session_id": actual_session_id}))
                logger.info(f"Sent [DONE] signal to client for session {actual_session_id}")

            except Exception as stream_err:
                logger.error(f"Error during OpenAI streaming or saving for session {actual_session_id}: {stream_err}", exc_info=True)
                error_payload = {"type": "error", "detail": "Error processing your request with AI.", "session_id": actual_session_id}
                try:
                    if websocket.client_state == WebSocketState.CONNECTED:
                        await websocket.send_text(json.dumps(error_payload))
                except Exception as send_err:
                    logger.error(f"Failed to send error to client after stream error for session {actual_session_id}: {send_err}")
                try:
                    if websocket.client_state == WebSocketState.CONNECTED:
                        await websocket.send_text(json.dumps({"type": "done", "session_id": actual_session_id, "error": True}))
                except Exception as send_done_err:
                    logger.error(f"Failed to send done signal to client after stream error for session {actual_session_id}: {send_done_err}")

    except WebSocketDisconnect:
        if current_user:
            logger.info(f"WebSocket disconnected for user {current_user.email}: {websocket.client}")
        else:
            logger.info(f"WebSocket disconnected (unauthenticated): {websocket.client}")
        return

    except HTTPException as http_exc:
        logger.warning(f"HTTPException during WebSocket handshake or processing: {http_exc.detail}")
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                 await websocket.send_text(json.dumps({"type": "error", "detail": http_exc.detail}))
        except Exception: pass 
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=http_exc.detail)
        except Exception: pass
        return

    except Exception as e:
        error_message = f"Unexpected error in WebSocket endpoint: {str(e)}"
        logger.error(error_message, exc_info=True)
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(json.dumps({"type": "error", "detail": "Internal server error"}))
        except Exception: pass
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except Exception: pass
        return

@router.delete("/sessions")
async def end_session(request: Request):
    request.session.clear()
    return {"message": "Session ended successfully"}

@router.post("", response_model=ChatResponse)
async def chat_with_ai(
    chat_request: ChatRequest,
    current_user: User = Depends(require_permission('chat_message_send')),
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

@router.get("/sessions/archived")
async def get_archived_chat_sessions_route(
    current_user: User = Depends(require_permission('chat_session_read')),
    db: AsyncSession = Depends(get_async_db),
    chat_type: str = "general"
):
    try:
        archived_sessions = await get_archived_chat_sessions(db, current_user.id, chat_type)
        return archived_sessions
    except ValueError as ve:
        logger.error(f"Invalid chat type requested: {chat_type}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error fetching archived chat sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch archived chat sessions")

@router.get("/sessions/{session_id}/messages", response_model=List[Dict])
async def get_chat_messages(
    session_id: str,
    current_user: User = Depends(require_permission('chat_session_read')),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        session_uuid = UUID(session_id)
        session = await get_chat_session_by_id(db, session_uuid)
        if not session: # セッションが存在しない
            raise HTTPException(status_code=404, detail="Session not found")
        
        # --- デバッグログ追加 ---
        logger.debug(f"Auth check for session {session_id}: session.user_id = {session.user_id}, current_user.id = {current_user.id}")
        # --- デバッグログ追加ここまで ---

        if session.user_id != current_user.id: # 所有権がない
            raise HTTPException(status_code=403, detail="Not authorized to view messages for this session")

        messages = await get_chat_messages_history(db, session_id)
        return messages
    except ValueError: # UUIDの形式が不正な場合
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except HTTPException as http_exc: # 意図したHTTPExceptionはそのまま再送出
        raise http_exc
    except Exception as e: # その他の予期せぬエラー
        logger.error(f"Unexpected error fetching messages for session {session_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch messages due to an unexpected error.")

@router.patch("/sessions/{session_id}/archive")
async def archive_chat_session(
    session_id: str,
    current_user: User = Depends(require_permission('chat_session_read')), 
    db: AsyncSession = Depends(get_async_db)
    # chat_type クエリパラメータを削除
):
    try:
        session_uuid = UUID(session_id)

        # 1. まずセッションを取得して存在確認と所有権確認、そして chat_type を得る
        session_to_archive = await get_chat_session_by_id(db, session_uuid)

        if not session_to_archive:
            raise HTTPException(status_code=404, detail="Session to archive not found")
        
        if session_to_archive.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to archive this session")

        # 2. 取得したセッションの chat_type を使ってステータスを更新
        updated_session = await update_session_status(
            db, 
            session_uuid, 
            current_user.id, 
            "ARCHIVED", 
            session_to_archive.chat_type.value # 実際のチャットタイプを渡す
        )
        
        if not updated_session:
            logger.error(f"update_session_status returned None unexpectedly for session {session_id} during archive.")
            raise HTTPException(status_code=500, detail="Failed to archive session due to an unexpected internal error.")
        
        return updated_session
    except ValueError: # UUID(session_id) でのエラー
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error archiving session {session_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to archive session")

@router.patch("/sessions/{session_id}/unarchive")
async def unarchive_chat_session(
    session_id: str,
    current_user: User = Depends(require_permission('chat_session_read')),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        session_uuid = UUID(session_id)
        session_to_unarchive = await get_chat_session_by_id(db, session_uuid)

        if not session_to_unarchive:
            raise HTTPException(status_code=404, detail="Session to unarchive not found")
        
        if session_to_unarchive.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to unarchive this session")

        updated_session = await update_session_status(
            db,
            session_uuid,
            current_user.id,
            ChatSessionStatusEnum.ACTIVE.value, # SessionStatus.ACTIVE.value から変更
            session_to_unarchive.chat_type.value
        )

        if not updated_session:
            logger.error(f"update_session_status returned None for session {session_id} during unarchive.")
            raise HTTPException(status_code=500, detail="Failed to unarchive session due to internal error.")
            
        return updated_session
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error unarchiving session {session_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to unarchive session")

@router.get("/sessions", response_model=List[ChatSessionSummary])
async def get_chat_sessions(
    current_user: User = Depends(require_permission('chat_session_read')),
    db: AsyncSession = Depends(get_async_db),
    chat_type_str: Optional[str] = Query(None, alias="chat_type"), # 文字列として受け取り、エイリアスを指定
    status_str: Optional[str] = Query(None, alias="status")       # 文字列として受け取り、エイリアスを指定
):
    """
    ユーザーのチャットセッションのリストを取得します。
    オプションでチャットタイプとステータスでフィルタリングできます。
    """
    logger.debug(f"Attempting to fetch sessions for user {current_user.email} with chat_type_str='{chat_type_str}' and status_str='{status_str}'")
    
    chat_type_enum: Optional[ChatTypeEnum] = None
    if chat_type_str:
        try:
            # ChatTypeEnum の値は小文字スネークケースなので、入力もそれに合わせる
            chat_type_enum = ChatTypeEnum(chat_type_str.lower().replace('-', '_'))
        except ValueError:
            logger.warning(f"Invalid chat_type string received: {chat_type_str}. Valid values are: {[e.value for e in ChatTypeEnum]}")
            # 422を返すか、フィルタリングなしとするか。ここではフィルタリングなしとする。
            # raise HTTPException(status_code=422, detail=f"Invalid chat_type: {chat_type_str}")
            pass 
    
    status_enum: Optional[ChatSessionStatusEnum] = None
    if status_str:
        try:
            # SessionStatusEnum の値は大文字なので、入力もそれに合わせる
            status_enum = ChatSessionStatusEnum(status_str.upper())
        except ValueError:
            logger.warning(f"Invalid status string received: {status_str}. Valid values are: {[e.value for e in ChatSessionStatusEnum]}")
            # raise HTTPException(status_code=422, detail=f"Invalid status: {status_str}")
            pass

    try:
        chat_type_value_for_crud = chat_type_enum.value if chat_type_enum else None
        # SessionStatusEnum は str を継承したので .value は文字列 (e.g. "ACTIVE")
        status_value_for_crud = status_enum.value if status_enum else None

        logger.debug(f"Calling get_user_chat_sessions with user_id='{current_user.id}', chat_type='{chat_type_value_for_crud}', session_status='{status_value_for_crud}'")

        sessions_db = await get_user_chat_sessions(
            db=db, 
            user_id=current_user.id, 
            chat_type=chat_type_value_for_crud, 
            status=status_value_for_crud
        )
        
        logger.debug(f"Retrieved {len(sessions_db)} sessions from DB.")
        # デバッグ: 取得したセッションの最初の1件の型と内容を出力
        # if sessions_db:
        #    logger.debug(f"First session from DB raw type: {type(sessions_db[0])}, content: {sessions_db[0].__dict__ if hasattr(sessions_db[0], '__dict__') else sessions_db[0]}")


        # response_model=List[ChatSessionSummary] により、FastAPIが自動的に変換を試みる
        # sessions_dbの各要素がChatSessionSummaryのフィールドと互換性があるか確認
        # 特に、ChatSessionSummaryのchat_typeはChatTypeEnum型なので、
        # sessions_dbから取得したchat_typeの文字列がChatTypeEnumの有効な値である必要がある。
        # get_user_chat_sessions が返すオブジェクトの chat_type フィールドがEnumのメンバーの .value (e.g., "self_analysis") であることを期待。
        
        # 手動で変換する場合の例 (FastAPIの自動変換に任せる前にデバッグとして)
        # response_data = []
        # for session_obj in sessions_db:
        #     try:
        #         # DBのchat_type (文字列) を ChatTypeEnum に変換
        #         db_chat_type_enum = ChatTypeEnum(session_obj.chat_type) if session_obj.chat_type else None
        #         summary = ChatSessionSummary(
        #             id=session_obj.id,
        #             title=session_obj.title,
        #             chat_type=db_chat_type_enum, # Enum型で渡す
        #             created_at=session_obj.created_at,
        #             updated_at=session_obj.updated_at
        #         )
        #         response_data.append(summary)
        #     except Exception as conv_e:
        #         logger.error(f"Error converting session DB object to ChatSessionSummary: {conv_e}, object: {session_obj.__dict__ if hasattr(session_obj, '__dict__') else session_obj}", exc_info=True)
        #         # エラーのあるオブジェクトはスキップするか、エラーレスポンスを返す
        # return response_data

        return sessions_db

    except Exception as e:
        logger.error(f"Error in get_chat_sessions for user {current_user.email}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch chat sessions."
        )

@router.get("/{chat_id}/checklist")
async def get_checklist_evaluation_endpoint(
    chat_id: UUID,
    current_user: User = Depends(require_permission('chat_session_read')),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        session = await get_chat_session_by_id(db, chat_id)
        if not session or session.user_id != current_user.id:
             raise HTTPException(status_code=403, detail="Not authorized to view this evaluation")

        evaluation = await get_evaluation_by_session_id(db, chat_id)
        if not evaluation:
            return []

        return evaluation.checklist_items
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chat ID format")
    except Exception as e:
        logger.error(f"Error fetching checklist evaluation for chat {chat_id}: {str(e)}", exc_info=True)
        if db.in_transaction():
            await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch checklist evaluation")

@router.post("/self-analysis", response_model=ChatResponse)
async def start_self_analysis_chat(
    chat_request: ChatRequest,
    current_user: User = Depends(require_permission('chat_message_send')),
    db: AsyncSession = Depends(get_async_db)
):
    # セッションを取得または作成
    chat_session = await get_or_create_chat_session(
        db=db,
        user_id=current_user.id,
        session_id=chat_request.session_id,
        chat_type=chat_request.chat_type.value
    )
    actual_session_id = chat_session.id
    # ユーザー発言を保存
    await save_chat_message(
        db=db,
        session_id=actual_session_id,
        content=chat_request.message,
        user_id=current_user.id,
        sender_type="USER"
    )
    # 新版LangChain自己分析オーケストレーターを利用して応答生成
    orchestrator = SelfAnalysisOrchestrator()
    result = await orchestrator.run([{"role": "user", "content": chat_request.message}], actual_session_id)
    # ユーザー向け応答抽出
    if isinstance(result, dict):
        reply = result.get("user_visible") or result.get("final_notes") or str(result)
    else:
        reply = str(result)
    # AIメッセージを保存
    await save_chat_message(
        db=db,
        session_id=actual_session_id,
        content=reply or "",
        user_id=current_user.id,
        sender_type="AI"
    )
    return ChatResponse(reply=reply or "", session_id=actual_session_id, timestamp=datetime.utcnow())

@router.get("/self-analysis/report")
async def get_self_analysis_report(
    session_id: UUID = Query(..., description="対象の自己分析セッションID"),
    current_user: User = Depends(require_permission('chat_session_read')),
    db: AsyncSession = Depends(get_async_db)
):
    """
    指定の自己分析セッションについて、各ステップのノートとMarkdown年表をまとめて返します。
    """
    # セッション存在と所有権の確認
    session = await get_chat_session_by_id(db, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this report")
    # ノート取得関数
    from app.services.agents.self_analysis_monono_agent.tools.notes import list_notes as list_notes_fn
    # Markdown変換
    from app.services.agents.self_analysis_langchain.markdown import render_markdown_timeline

    # 各ステップのJSONノート
    future = await list_notes_fn(str(session_id), 'FUTURE')
    motivation = await list_notes_fn(str(session_id), 'MOTIVATION')
    history = await list_notes_fn(str(session_id), 'HISTORY')
    gap = await list_notes_fn(str(session_id), 'GAP')
    vision = await list_notes_fn(str(session_id), 'VISION')
    reflect = await list_notes_fn(str(session_id), 'REFLECT')
    # Markdown年表
    timeline = history[0].get('timeline', []) if history and isinstance(history[0], dict) else []
    timeline_md = render_markdown_timeline(timeline)

    return {
        'future': future,
        'motivation': motivation,
        'history': history,
        'timeline_md': timeline_md,
        'gap': gap,
        'vision': vision,
        'reflect': reflect,
    }

@router.post("/admission", response_model=ChatResponse)
async def start_admission_chat(
    chat_request: ChatRequest,
    current_user: User = Depends(require_permission('chat_message_send')),
    db: AsyncSession = Depends(get_async_db)
):
    chat_session = await get_or_create_chat_session(db=db, user_id=current_user.id, session_id=chat_request.session_id, chat_type=chat_request.chat_type.value)
    actual_session_id = chat_session.id
    await save_chat_message(db=db, session_id=actual_session_id, content=chat_request.message, user_id=current_user.id, sender_type="USER")
    reply = await get_admission_agent_response(chat_request.message, history=None)
    await save_chat_message(db=db, session_id=actual_session_id, content=reply or "", user_id=current_user.id, sender_type="AI")
    return ChatResponse(reply=reply or "", session_id=actual_session_id, timestamp=datetime.utcnow())

@router.post("/study-support", response_model=ChatResponse)
async def start_study_support_chat(
    chat_request: ChatRequest,
    current_user: User = Depends(require_permission('chat_message_send')),
    db: AsyncSession = Depends(get_async_db)
):
    chat_session = await get_or_create_chat_session(db=db, user_id=current_user.id, session_id=chat_request.session_id, chat_type=chat_request.chat_type.value)
    actual_session_id = chat_session.id
    await save_chat_message(db=db, session_id=actual_session_id, content=chat_request.message, user_id=current_user.id, sender_type="USER")
    reply = await get_study_support_agent_response(chat_request.message, history=None)
    await save_chat_message(db=db, session_id=actual_session_id, content=reply or "", user_id=current_user.id, sender_type="AI")
    return ChatResponse(reply=reply or "", session_id=actual_session_id, timestamp=datetime.utcnow())

@router.get("/analysis")
async def get_chat_analysis(
    session_id: str = None,
    current_user: User = Depends(require_permission('chat_session_read')),
    db: AsyncSession = Depends(get_async_db)
):
    logger.warning("Chat analysis endpoint not fully implemented with async DB.")
    raise HTTPException(status_code=501, detail="Not Implemented Yet")

@router.post("/sessions", response_model=ChatSession, status_code=status.HTTP_201_CREATED)
async def create_new_chat_session(
    *,
    session_in: ChatSessionCreate,
    db: AsyncSession = Depends(deps.get_async_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    指定されたタイプ (リクエストボディの chat_type) の新しいチャットセッションを作成します。
    """
    session = await crud.chat.get_or_create_chat_session(
        db=db,
        user_id=current_user.id,
        chat_type=session_in.chat_type.value
    )
    # 新規セッションに初期AIメッセージを追加
    initial_message_content = settings.INSTRUCTION
    # SELF_ANALYSISモードの場合の最初の挨拶文を設定
    if session.chat_type == ChatType.SELF_ANALYSIS:
        initial_message_content = "こんにちは、今日から自己分析を始めましょう！　まずは将来やってみたいことを 1〜2 行で教えていただけますか？"
    # FAQモードの場合の固定メッセージ（必要に応じて他のモードも追加）
    elif session.chat_type == ChatType.FAQ:
        initial_message_content = "あなたは総合型選抜に関する質問に答えるFAQボットです。"
    await save_chat_message(
        db=db,
        session_id=session.id,
        content=initial_message_content,
        sender_type="AI"
    )
    return session

@router.get("/{session_id}", response_model=ChatSession)
async def read_chat_session(
    session_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_permission("chat_session_read"))
):
    """指定されたIDのチャットセッションを取得する"""
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    session = await crud.chat.get_chat_session_by_id(db=db, session_id=session_uuid)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session

@router.post("/sessions/{session_id}/messages", response_model=ChatMessageSchema, status_code=status.HTTP_201_CREATED)
async def create_new_chat_message(
    session_id: UUID,
    message_in: ChatMessageCreate,
    db: AsyncSession = Depends(deps.get_async_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    """
    チャットセッションに新しいメッセージを追加し、セッションタイプに応じた
    AI Agent を呼び出して応答を生成・保存し、そのAI応答メッセージを返します。
    """
    # 1. セッションの存在と所有権を確認
    session = await crud.chat.get_chat_session_by_id(db, session_id=session_id)

    if not session or session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found or access denied",
        )

    # 2. ユーザーメッセージをデータベースに保存
    user_message = await crud.chat.save_chat_message(
        db=db, 
        session_id=session_id,
        content=message_in.content,
        user_id=current_user.id,
        sender_type="USER"
    )

    # --- ここからAI応答生成 (Agent SDK使用 & タイプ別呼び出し) ---
    ai_response_content = "AI応答の生成中にエラーが発生しました。" # デフォルトのエラーメッセージ
    try:
        # 3. セッションタイプに応じて呼び出すAgent関数を選択
        agent_function = None
        if session.chat_type == ChatType.SELF_ANALYSIS:
            agent_function = get_self_analysis_agent_response
        elif session.chat_type == ChatType.ADMISSION:
            agent_function = get_admission_agent_response
        elif session.chat_type == ChatType.STUDY_SUPPORT:
            agent_function = get_study_support_agent_response
        # elif session.chat_type == ChatType.GENERAL: # GENERAL の場合の処理も必要？
        #     # agent_function = get_general_agent_response # (もしあれば)
        #     pass # GENERAL 用の Agent がなければ何もしないかエラー
        else:
            # 未対応のチャットタイプの場合 (現状 GENERAL などが該当)
            # 必要であれば GENERAL 用の処理を追加する
            logger.warning(f"AI agent call not implemented for chat type '{session.chat_type}' in session {session_id}")
            # raise HTTPException(status_code=501, detail=f"AI agent for chat type '{session.chat_type}' is not implemented.")
            # 一旦、AI応答なしで進めるか、固定メッセージを返すなど検討
            ai_response_content = "このチャットタイプに対するAI応答は現在実装されていません。"
            # この場合は agent_function は None のまま

        # 4. 選択したAgent関数を呼び出して応答を取得
        if agent_function:
            logger.info(f"Calling {agent_function.__name__} for session {session_id} (type: {session.chat_type})...")
            # TODO: 会話履歴 (history) をAgentに渡す処理を追加する
            # 現状はユーザーの最後のメッセージのみを渡している
            history = await crud.chat.get_session_messages(db, str(session_id), current_user.id, session.chat_type.value)
            formatted_history = [
                {"role": "assistant" if msg.sender == "AI" else "user", "content": msg.content}
                for msg in history # user_message は含めない (agent_function の引数で渡すため)
                if msg.id != user_message.id # 保存したばかりのユーザーメッセージは除く
            ]
            ai_response = await agent_function(
                user_input=user_message.content,
                history=formatted_history # 会話履歴を渡す (Agent SDK側の対応確認が必要)
            )

            if ai_response is not None:
                ai_response_content = ai_response
            else:
                 # AI AgentがNoneを返した場合 (サービス側の関数内でログ出力・エラー応答済みのはず)
                 logger.warning(f"AI Agent ({agent_function.__name__}) returned None for session {session_id}")
                 ai_response_content = "申し訳ありません、応答を生成できませんでした。" # フォールバック
        # else: # agent_function が None の場合の ai_response_content は上で設定済み
        #     pass

    except HTTPException as http_exc:
        # chat_type が未対応の場合など、意図したHTTPエラーはそのままraise
        raise http_exc
    except Exception as e:
        logger.error(f"Error during AI Agent execution for session {session_id} (type: {session.chat_type}): {e}", exc_info=True)
        ai_response_content = f"{session.chat_type.name if session.chat_type else 'AI'} の実行中に内部エラーが発生しました。"
        # AI実行エラーが発生しても、AIメッセージレコード自体は保存する (エラー内容を含む)

    # 5. AIの応答をデータベースに保存
    logger.info(f"Saving AI Agent message for session {session_id} (type: {session.chat_type})...")
    ai_message = await crud.chat.save_chat_message(
        db=db, 
        session_id=session_id,
        content=ai_response_content,
        sender_type="AI" # sender_type を AI に
        # sender_id は AI なので不要
    )
    logger.info(f"AI Agent message saved (ID: {ai_message.id})")

    return ai_message

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageSchema])
async def read_chat_messages(
    session_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(deps.get_async_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    指定されたチャットセッションのメッセージ履歴を取得します。
    """
    # セッションの存在と所有権を確認 (crud 層で行う想定だったが、ここで一旦行う)
    session = await crud.chat.get_chat_session_by_id(db, session_id=session_id)

    if not session or session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found or access denied",
        )

    # messages = crud.chat.get_chat_messages(db, session_id=session_id, skip=skip, limit=limit)
    # 非同期版の関数を呼び出し、session_type も渡す
    messages = await crud.chat.get_session_messages(
        db=db,
        session_id=str(session_id),
        user_id=current_user.id,
        chat_type=session.chat_type.value
    )

    # スキップとリミットの適用 (get_session_messages がサポートしない場合)
    # messages = messages[skip : skip + limit]

    return messages

@router.patch("/sessions/{session_id}/generate-title")
async def generate_session_title(
    session_id: str,
    current_user: User = Depends(require_permission('chat_session_read')),
    db: AsyncSession = Depends(get_async_db)
):
    """
    チャットセッションの内容を基にAIがタイトルを自動生成する
    """
    try:
        # セッションの存在確認
        session = await get_chat_session_by_id(db, session_id, current_user.id)
        if not session:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")

        # セッションのメッセージを取得
        messages = await get_chat_messages_history(db, session_id)
        if not messages or len(messages) == 0:
            raise HTTPException(status_code=400, detail="メッセージがないためタイトルを生成できません")

        # 最初の数個のメッセージを抽出してタイトル生成用のプロンプトを作成
        conversation_summary = ""
        message_count = 0
        for msg in messages[:6]:  # 最初の3往復程度
            if isinstance(msg, dict):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                if role == "user":
                    conversation_summary += f"ユーザー: {content[:100]}\n"
                elif role in ["ai", "assistant"]:
                    conversation_summary += f"AI: {content[:100]}\n"
                message_count += 1
            if message_count >= 6:
                break

        if not conversation_summary.strip():
            # フォールバック：最初のユーザーメッセージからタイトル生成
            first_user_message = None
            for msg in messages:
                if isinstance(msg, dict) and msg.get("role") == "user":
                    first_user_message = msg.get("content", "")
                    break
            
            if first_user_message:
                title = first_user_message[:25].strip() + ("..." if len(first_user_message) > 25 else "")
            else:
                title = f"{session.chat_type}セッション"
        else:
            # OpenAI APIを使ってタイトルを生成
            try:
                client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                title_prompt = f"""以下の会話の内容を基に、適切なタイトルを15文字以内で生成してください。
タイトルは会話の主要なトピックを表現し、ユーザーが後で見返した時に内容が分かりやすいものにしてください。

会話内容:
{conversation_summary}

タイトルのみを出力してください（説明や追加のテキストは不要）。"""

                response = await client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": title_prompt}],
                    max_tokens=50,
                    temperature=0.7
                )
                
                generated_title = response.choices[0].message.content.strip()
                # タイトルの長さ制限とサニタイズ
                title = generated_title[:30] if generated_title else f"{session.chat_type}セッション"
                
            except Exception as e:
                logger.error(f"Failed to generate title using OpenAI: {e}")
                # フォールバック：最初のユーザーメッセージから生成
                first_user_message = None
                for msg in messages:
                    if isinstance(msg, dict) and msg.get("role") == "user":
                        first_user_message = msg.get("content", "")
                        break
                
                if first_user_message:
                    title = first_user_message[:25].strip() + ("..." if len(first_user_message) > 25 else "")
                else:
                    title = f"{session.chat_type}セッション"

        # タイトルを更新
        await update_session_title(db, UUID(session_id), current_user.id, title)
        logger.info(f"Session title updated to '{title}' for session {session_id}")

        return {"title": title, "session_id": session_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating title for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="タイトル生成中にエラーが発生しました")
