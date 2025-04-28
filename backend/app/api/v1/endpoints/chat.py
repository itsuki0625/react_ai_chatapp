from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks, status
from fastapi.responses import StreamingResponse
from typing import List, Dict, Optional
from datetime import datetime
import logging
from app.schemas.chat import ChatRequest, ChatResponse, Message, ChatMessageCreate, ChatMessage as ChatMessageSchema, ChatSessionCreate, ChatType, ChatSessionStatus, ChatSessionSummary, ChatSession, ChatMessageResponse
from app.core.config import settings
from app.services.openai_service import stream_openai_response
import uuid
from openai import AsyncOpenAI
from app.api.deps import get_current_user, User, require_permission
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
    create_evaluation,
    get_evaluation_by_chat_id,
    update_evaluation
)
from uuid import UUID
from sqlalchemy.orm import Session
from app import models, crud
from app.api import deps
from app.models.chat import MessageSender
from app.services.ai_service import (
    get_self_analysis_agent_response,
    get_admission_agent_response,
    get_study_support_agent_response
)
from app.crud.async_chat import get_user_chat_sessions

router = APIRouter()

# ロギング設定
logger = logging.getLogger(__name__)

checklist_evaluator = ChecklistEvaluator()

@router.options("/stream")
async def chat_stream_options():
    return {"message": "OK"}

@router.post("/stream")
async def chat_stream(
    request: Request,
    chat_request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission('chat_message_send')),
    db: AsyncSession = Depends(get_async_db),
):
    logger.info("--- chat_stream endpoint called ---")
    logger.info(f"Received message: {chat_request.message}")
    logger.info(f"Chat request: {chat_request}")
    
    try:
        chat_session = await get_or_create_chat_session(
            db=db,
            user_id=current_user.id,
            session_id=chat_request.session_id,
            chat_type=chat_request.chat_type.value
        )
        logger.info("セッションの取得または作成に成功しました")
        
        session_id = str(chat_session.id)
        logger.info(f"Session ID: {session_id}")
        
        if not chat_request.session_id:
            title = chat_request.message[:30] + "..." if len(chat_request.message) > 30 else chat_request.message
            await update_session_title(
                db, 
                chat_session.id, 
                current_user.id, 
                title
            )
            logger.info(f"Session title updated to: {title}")

        user_message = await save_chat_message(
            db=db,
            session_id=session_id,
            content=chat_request.message,
            sender_id=current_user.id,
            sender_type="USER"
        )
        logger.info(f"User message saved (ID: {user_message.id})")

        session_messages = await get_chat_messages_history(
            db,
            session_id
        )
        logger.info(f"Fetched {len(session_messages)} existing messages for the session")
        formatted_history = [
            {
                "role": "assistant" if msg.sender_type == "AI" else "user",
                "content": msg.content
            }
            for msg in session_messages
        ]
        logger.info("Formatted message history")

        system_message = ""
        if chat_request.chat_type == ChatType.FAQ:
            system_message = "あなたは総合型選抜に関する質問に答えるFAQボットです。"
        elif chat_request.chat_type == ChatType.CONSULTATION:
            logger.warning(f"Handling potentially unused chat_type: {chat_request.chat_type}")
            system_message = settings.INSTRUCTION
        else:
            base_instruction = settings.INSTRUCTION
            system_message = base_instruction
            logger.info(f"Using base instruction for chat_type: {chat_request.chat_type}")

        logger.info(f"System message: {system_message[:100]}...")

        messages = [
            {"role": "system", "content": system_message},
            *formatted_history,
            {"role": "user", "content": chat_request.message}
        ]

        ai_message = await save_chat_message(
            db=db,
            session_id=session_id,
            content="",
            sender_type="AI"
        )
        logger.info(f"Empty AI message saved (ID: {ai_message.id})")

        async def stream_and_save():
            full_response = ""
            try:
                async for chunk in stream_openai_response(messages, session_id):
                    if isinstance(chunk, str):
                        sanitized = chunk.replace("data: ", "").strip()
                        if sanitized == "[DONE]":
                            logger.info("Received [DONE] signal")
                            break
                        full_response += sanitized
                        yield f'data: {sanitized}\n\n'
                    else:
                         logger.warning(f"Received non-string chunk: {type(chunk)}")

                logger.info(f"Streaming finished. Full AI response length: {len(full_response)}")

                if ai_message:
                    ai_message.content = full_response
                    ai_message.updated_at = datetime.utcnow()
                    db.add(ai_message)
                    await db.commit()
                    await db.refresh(ai_message)
                    logger.info(f"AI response saved/updated for message ID: {ai_message.id}")
                else:
                     logger.error("ai_message object was None before saving full response")

                if chat_request.chat_type == ChatType.SELF_ANALYSIS:
                    try:
                        fresh_messages_history = await get_chat_messages_history(
                            db,
                            str(chat_session.id)
                        )
                        chat_history_for_eval = []
                        if isinstance(fresh_messages_history, list):
                            for msg_item in fresh_messages_history:
                                if isinstance(msg_item, dict):
                                     chat_history_for_eval.append({
                                         "role": msg_item.get("role", "unknown"), 
                                         "content": msg_item.get("content", "")
                                     })
                                elif hasattr(msg_item, 'sender_type') and hasattr(msg_item, 'content'):
                                     chat_history_for_eval.append({
                                         "role": "assistant" if msg_item.sender_type == "AI" else "user",
                                         "content": msg_item.content
                                     })
                                else:
                                     logger.warning(f"Unexpected item type in message history: {type(msg_item)}")
                        else:
                            logger.error(f"Expected list from get_chat_messages_history, got: {type(fresh_messages_history)}")

                        logger.info(f"Chat history for evaluation ({len(chat_history_for_eval)} messages)")

                        evaluation_result = await checklist_evaluator.evaluate_chat(chat_history_for_eval)
                        logger.info(f"Evaluation result obtained: {evaluation_result is not None}")

                        if evaluation_result:
                            existing_evaluation = await get_evaluation_by_chat_id(db, UUID(session_id))
                            if existing_evaluation:
                                await update_evaluation(db, existing_evaluation.id, evaluation_result)
                                logger.info("Evaluation updated successfully")
                            else:
                                await create_evaluation(db, UUID(session_id), evaluation_result)
                                logger.info("Evaluation created successfully")
                        else:
                            logger.warning("Evaluation result was None, skipping DB update.")
                    except Exception as eval_e:
                        logger.error(f"Error during checklist evaluation or DB update: {str(eval_e)}")
                        # ここでエラーを raise するかは検討事項

                yield 'data: [DONE]\n\n'
                logger.info("Sent final [DONE] signal")
            except Exception as stream_err:
                 logger.error(f"Error during streaming or saving: {stream_err}", exc_info=True)
                 yield 'data: [ERROR] Streaming failed\n\n'
                 yield 'data: [DONE]\n\n'

        return StreamingResponse(
            stream_and_save(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

    except ValueError as ve:
        logger.error(f"Invalid chat type provided: {chat_request.chat_type}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error in chat_stream endpoint: {str(e)}", exc_info=True)
        if db.in_transaction():
             await db.rollback()
             logger.info("Rolled back transaction due to error")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

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
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view messages for this session")

        messages = await get_chat_messages_history(db, session_id)
        return messages
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except Exception as e:
        logger.error(f"Error fetching messages for session {session_id}: {str(e)}")
        if db.in_transaction():
            await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch messages")

@router.patch("/sessions/{session_id}/archive")
async def archive_chat_session(
    session_id: str,
    current_user: User = Depends(require_permission('chat_session_read')),
    db: AsyncSession = Depends(get_async_db),
    chat_type: str = "general"
):
    try:
        session_uuid = UUID(session_id)
        updated_session = await update_session_status(db, session_uuid, current_user.id, "ARCHIVED", chat_type)
        if not updated_session:
            logger.error(f"update_session_status returned None unexpectedly for session {session_id}")
            raise HTTPException(status_code=500, detail="Failed to archive session due to unexpected error.")
        return updated_session
    except ValueError as ve:
        detail = str(ve)
        status_code = 400
        if "Invalid session ID format" in detail:
            status_code = 400
        elif "Invalid chat type" in detail:
            status_code = 400
        else:
            status_code = 400
        logger.error(f"Error processing archive request: {detail}")
        raise HTTPException(status_code=status_code, detail=detail)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error archiving session {session_id}: {str(e)}")
        if db.in_transaction():
             await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to archive session")

@router.get("/sessions", response_model=List[ChatSessionSummary])
async def get_chat_sessions(
    current_user: User = Depends(require_permission('chat_session_read')),
    db: AsyncSession = Depends(get_async_db),
    chat_type: Optional[ChatType] = None,
    status: Optional[ChatSessionStatus] = None
):
    try:
        sessions = await get_user_chat_sessions(
            db,
            current_user.id,
            chat_type=chat_type,
            status=status
        )
        return sessions
    except Exception as e:
        logger.error(f"Error fetching chat sessions for user {current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch chat sessions")

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

        evaluation = await get_evaluation_by_chat_id(db, chat_id)
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

@router.post("/self-analysis")
async def start_self_analysis_chat(
    chat_request: ChatRequest,
    current_user: User = Depends(require_permission('chat_message_send')),
    db: AsyncSession = Depends(get_async_db)
):
    logger.warning("Self-analysis chat endpoint not fully implemented with async DB.")
    raise HTTPException(status_code=501, detail="Not Implemented Yet")

@router.get("/self-analysis/report")
async def get_self_analysis_report(
    current_user: User = Depends(require_permission('chat_session_read')),
    db: AsyncSession = Depends(get_async_db)
):
    logger.warning("Self-analysis report endpoint not fully implemented with async DB.")
    raise HTTPException(status_code=501, detail="Not Implemented Yet")

@router.post("/admission")
async def start_admission_chat(
    chat_request: ChatRequest,
    current_user: User = Depends(require_permission('chat_message_send')),
    db: AsyncSession = Depends(get_async_db)
):
    logger.warning("Admission chat endpoint not fully implemented with async DB.")
    raise HTTPException(status_code=501, detail="Not Implemented Yet")

@router.post("/study-support")
async def start_study_support_chat(
    chat_request: ChatRequest,
    current_user: User = Depends(require_permission('chat_message_send')),
    db: AsyncSession = Depends(get_async_db)
):
    logger.warning("Study support chat endpoint not fully implemented with async DB.")
    raise HTTPException(status_code=501, detail="Not Implemented Yet")

@router.get("/analysis")
async def get_chat_analysis(
    session_id: str = None,
    current_user: User = Depends(require_permission('chat_session_read')),
    db: AsyncSession = Depends(get_async_db)
):
    logger.warning("Chat analysis endpoint not fully implemented with async DB.")
    raise HTTPException(status_code=501, detail="Not Implemented Yet")

@router.post("/sessions/", response_model=ChatSession, status_code=status.HTTP_201_CREATED)
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
    return session

@router.get("/sessions/{session_id}", response_model=ChatSession)
def read_chat_session(
    session_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    特定のチャットセッションの詳細を取得します。
    メッセージは含まれません。メッセージ取得は別のエンドポイントを使用します。
    """
    session = crud.chat.get_chat_session(db=db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this session")
    return session

@router.post("/sessions/{session_id}/messages/", response_model=ChatMessageSchema, status_code=status.HTTP_201_CREATED)
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

@router.get("/sessions/{session_id}/messages/", response_model=List[ChatMessageSchema])
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
