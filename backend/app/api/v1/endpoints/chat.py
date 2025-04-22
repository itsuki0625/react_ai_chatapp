from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List, Dict
from datetime import datetime
import logging
from app.schemas.chat import ChatRequest, ChatResponse, Message, ChatMessageCreate
from app.core.config import settings
from app.services.openai_service import stream_openai_response
import uuid
from openai import AsyncOpenAI
from app.api.deps import get_current_user, User
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.crud.chat import get_or_create_chat_session, get_session_messages, save_chat_message, get_user_chat_sessions, update_session_title, update_session_status, get_archived_chat_sessions
from fastapi.middleware.cors import CORSMiddleware
from app.crud.checklist import (
    ChecklistEvaluator, 
    create_evaluation, 
    get_evaluation_by_chat_id,
    update_evaluation
)
from uuid import UUID

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
            base_instruction = settings.INSTRUCTION
            
            # チェックリストの評価結果を取得
            evaluation = get_evaluation_by_chat_id(db, UUID(session_id))
            if evaluation:
                checklist_status = "\n\n現在の進捗状況:\n"
                for item in evaluation.checklist_items:
                    checklist_status += f"- {item['item']}: {item['status']}\n"
                    if item['status'] != "完了":
                        checklist_status += f"  次の質問: {item['next_question']}\n"
                
                checklist_status += f"\n全体的な状況: {evaluation.completion_status}"
                
                system_message = f"{base_instruction}\n{checklist_status}"
            else:
                system_message = base_instruction

        logger.info("システムメッセージの設定に成功しました")
        logger.info(f"System message: {system_message}")

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

            # 志望理由書相談チャットの場合のみチェックリスト評価を実行
            if chat_request.session_type == "CONSULTATION":
                try:
                    # 新しいセッションでメッセージを再取得
                    fresh_messages = await get_session_messages(
                        db, 
                        session_id, 
                        current_user.id,
                        chat_request.session_type
                    )
                    
                    chat_history = [
                        {
                            "role": str(msg.sender_type).split('.')[-1].lower(),
                            "content": msg.content,
                            "timestamp": msg.created_at
                        } for msg in fresh_messages
                    ]
                    logger.info(f"Chat history for evaluation: {chat_history}")
                    
                    evaluation_result = await checklist_evaluator.evaluate_chat(chat_history)
                    logger.info(f"Evaluation result: {evaluation_result}")
                    
                    if evaluation_result:
                        existing_evaluation = get_evaluation_by_chat_id(db, UUID(session_id))
                        if existing_evaluation:
                            update_evaluation(db, existing_evaluation.id, evaluation_result)
                        else:
                            create_evaluation(db, UUID(session_id), evaluation_result)
                        logger.info("Evaluation created/updated successfully")
                    else:
                        logger.error("Evaluation result is None")
                except Exception as e:
                    logger.error(f"Error in evaluate_checklist: {str(e)}")
            
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

@router.delete("/sessions")
async def end_session(request: Request):
    request.session.clear()
    return {"message": "Session ended successfully"}

@router.post("", response_model=ChatResponse)
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

@router.get("/sessions/archived")
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

@router.get("/sessions/{session_id}/messages")
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

@router.patch("/sessions/{session_id}/archive")
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

@router.get("/sessions")
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

@router.get("/{chat_id}/checklist")
async def get_checklist_evaluation(
    chat_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    session_type: str = "CONSULTATION"
):
    # FAQチャットの場合はエラーを返す
    if session_type != "CONSULTATION":
        raise HTTPException(
            status_code=400, 
            detail="Checklist evaluation is only available for consultation chats"
        )
    
    evaluation = get_evaluation_by_chat_id(db, chat_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Checklist evaluation not found")
    return evaluation

@router.post("/self-analysis")
async def start_self_analysis_chat(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    自己分析AIとのチャットを開始する
    専用のシステムプロンプトと分析ロジックを使用する
    """
    logger.info(f"自己分析チャット開始: {chat_request.message}")
    
    try:
        # 自己分析用のセッションタイプを設定
        chat_request.session_type = "SELF_ANALYSIS"
        
        # チャットセッションを取得または作成
        chat_session = await get_or_create_chat_session(
            db=db,
            user_id=current_user.id,
            session_id=chat_request.session_id,
            session_type=chat_request.session_type
        )
        
        # セッションIDを保持
        session_id = str(chat_session.id)
        
        # 新しいセッションの場合のみタイトルを更新
        if not chat_request.session_id:
            title = "自己分析: " + (chat_request.message[:20] + "..." if len(chat_request.message) > 20 else chat_request.message)
            await update_session_title(
                db, 
                chat_session.id, 
                current_user.id, 
                title
            )

        # ユーザーメッセージを保存
        await save_chat_message(
            db=db,
            session_id=session_id,
            content=chat_request.message,
            sender_id=current_user.id,
            sender_type="USER"
        )

        # 自己分析用のシステムメッセージを設定
        system_message = """あなたは自己分析を支援するAIアシスタントです。
ユーザーの興味・関心や能力、性格的な特徴を深掘りするような質問をしてください。
回答から学生の強み・適性を分析し、志望理由書作成に役立つ洞察を提供してください。
会話の中で以下の領域について情報を収集してください：
1. 学業的関心・得意科目
2. 課外活動・特別な経験
3. 価値観・将来の目標
4. 性格的特徴・強み
5. 志望理由の背景
質問は一度に1〜2個までとし、ユーザーが深く考えられるよう促してください。
すべての情報が集まったら、最終的に「あなたの自己分析レポート」としてまとめを提供してください。"""

        # 既存のメッセージ履歴を取得
        session_messages = await get_session_messages(
            db, 
            session_id, 
            current_user.id,
            chat_request.session_type
        )
        
        formatted_history = [
            {
                "role": "assistant" if msg.sender_type == "AI" else "user",
                "content": msg.content
            }
            for msg in session_messages
        ]

        messages = [
            {"role": "system", "content": system_message},
            *formatted_history,
            {"role": "user", "content": chat_request.message}
        ]

        # OpenAI APIを呼び出して回答を取得
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            temperature=0.7,
        )
        
        ai_response = response.choices[0].message.content

        # AIの回答を保存
        await save_chat_message(
            db=db,
            session_id=session_id,
            content=ai_response,
            sender_type="AI"
        )

        return {
            "session_id": session_id,
            "message": ai_response
        }
        
    except Exception as e:
        logger.error(f"自己分析チャットエラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="自己分析チャットの処理中にエラーが発生しました"
        )

@router.get("/self-analysis/report")
async def get_self_analysis_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    自己分析の結果レポートを取得する
    過去の自己分析チャットの履歴から分析レポートを生成
    """
    try:
        # 自己分析のセッションを取得
        sessions = await get_user_chat_sessions(
            db,
            current_user.id,
            "SELF_ANALYSIS"
        )
        
        if not sessions:
            raise HTTPException(
                status_code=404,
                detail="自己分析の履歴が見つかりません。まず自己分析チャットを行ってください。"
            )
        
        # 最新のセッションを使用
        latest_session = sessions[0]
        session_id = str(latest_session.id)
        
        # セッションのメッセージを取得
        messages = await get_session_messages(
            db,
            session_id,
            current_user.id,
            "SELF_ANALYSIS"
        )
        
        if len(messages) < 4:  # 十分な対話がない場合
            raise HTTPException(
                status_code=400,
                detail="自己分析が不十分です。もう少し対話を続けてから再度お試しください。"
            )
        
        # 対話履歴から分析用のコンテキストを作成
        chat_history = "\n".join([
            f"{'AI: ' if msg.sender_type == 'AI' else 'ユーザー: '}{msg.content}"
            for msg in messages
        ])
        
        # レポート生成のシステムプロンプト
        system_message = """あなたは学生の自己分析を支援するAIアシスタントです。
以下の対話履歴に基づいて、学生の自己分析レポートを作成してください。
レポートには以下の項目を含めてください：
1. 学生の強み（スキル、知識、性格的特徴）
2. 興味・関心分野
3. 価値観・大切にしていること
4. 学業・研究における適性
5. 推奨される学問分野や進路
6. 志望理由書に活かせるポイント

レポートは客観的かつ建設的な内容にし、学生の可能性を広げるような分析を心がけてください。
"""
        
        # OpenAI APIでレポート生成
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"以下は学生との自己分析対話です。\n\n{chat_history}\n\nこの対話に基づいて自己分析レポートを作成してください。"}
            ],
            temperature=0.5,
        )
        
        report = response.choices[0].message.content
        
        return {
            "report": report,
            "session_id": session_id,
            "created_at": datetime.now().isoformat()
        }
        
    except HTTPException as he:
        # 既存のHTTPExceptionはそのまま再発生
        raise he
    except Exception as e:
        logger.error(f"自己分析レポート生成エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="自己分析レポートの生成中にエラーが発生しました"
        )

@router.post("/admission")
async def start_admission_chat(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    総合型選抜AIとのチャットを開始する
    """
    logger.info(f"総合型選抜チャット開始: {chat_request.message}")
    
    try:
        # 総合型選抜用のセッションタイプを設定
        chat_request.session_type = "ADMISSION"
        
        # チャットセッションを取得または作成
        chat_session = await get_or_create_chat_session(
            db=db,
            user_id=current_user.id,
            session_id=chat_request.session_id,
            session_type=chat_request.session_type
        )
        
        # セッションIDを保持
        session_id = str(chat_session.id)
        
        # 新しいセッションの場合のみタイトルを更新
        if not chat_request.session_id:
            title = "総合型選抜: " + (chat_request.message[:20] + "..." if len(chat_request.message) > 20 else chat_request.message)
            await update_session_title(
                db, 
                chat_session.id, 
                current_user.id, 
                title
            )

        # ユーザーメッセージを保存
        await save_chat_message(
            db=db,
            session_id=session_id,
            content=chat_request.message,
            sender_id=current_user.id,
            sender_type="USER"
        )

        # 総合型選抜用のシステムメッセージを設定
        system_message = """あなたは総合型選抜（AO入試）に関するエキスパートAIアシスタントです。
以下の点について詳しい情報と具体的なアドバイスを提供してください：
1. 大学別の総合型選抜情報
2. 出願書類（志望理由書、活動報告書など）の書き方
3. 面接対策（想定質問と回答例）
4. 小論文・課題対策
5. 過去の合格事例や統計情報
6. 出願スケジュール管理

ユーザーの志望校や状況に合わせた具体的なアドバイスを心がけ、総合型選抜対策を包括的にサポートしてください。
わからない質問には推測せず、正直に不明であることを伝えてください。"""

        # 既存のメッセージ履歴を取得
        session_messages = await get_session_messages(
            db, 
            session_id, 
            current_user.id,
            chat_request.session_type
        )
        
        formatted_history = [
            {
                "role": "assistant" if msg.sender_type == "AI" else "user",
                "content": msg.content
            }
            for msg in session_messages
        ]

        messages = [
            {"role": "system", "content": system_message},
            *formatted_history,
            {"role": "user", "content": chat_request.message}
        ]

        # OpenAI APIを呼び出して回答を取得
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            temperature=0.7,
        )
        
        ai_response = response.choices[0].message.content

        # AIの回答を保存
        await save_chat_message(
            db=db,
            session_id=session_id,
            content=ai_response,
            sender_type="AI"
        )

        return {
            "session_id": session_id,
            "message": ai_response
        }
        
    except Exception as e:
        logger.error(f"総合型選抜チャットエラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="総合型選抜チャットの処理中にエラーが発生しました"
        )

@router.post("/study-support")
async def start_study_support_chat(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    汎用学習支援AIとのチャットを開始する
    """
    logger.info(f"学習支援チャット開始: {chat_request.message}")
    
    try:
        # 学習支援用のセッションタイプを設定
        chat_request.session_type = "STUDY_SUPPORT"
        
        # チャットセッションを取得または作成
        chat_session = await get_or_create_chat_session(
            db=db,
            user_id=current_user.id,
            session_id=chat_request.session_id,
            session_type=chat_request.session_type
        )
        
        # セッションIDを保持
        session_id = str(chat_session.id)
        
        # 新しいセッションの場合のみタイトルを更新
        if not chat_request.session_id:
            title = "学習支援: " + (chat_request.message[:20] + "..." if len(chat_request.message) > 20 else chat_request.message)
            await update_session_title(
                db, 
                chat_session.id, 
                current_user.id, 
                title
            )

        # ユーザーメッセージを保存
        await save_chat_message(
            db=db,
            session_id=session_id,
            content=chat_request.message,
            sender_id=current_user.id,
            sender_type="USER"
        )

        # 学習支援用のシステムメッセージを設定
        system_message = """あなたは学習全般をサポートするAI教育アシスタントです。
以下の点について正確な情報と効果的な学習方法を提供してください：
1. 各教科（数学、英語、国語、理科、社会など）の学習方法
2. 受験対策や効率的な勉強法
3. 学習スケジュールの立て方
4. 苦手科目の克服方法
5. モチベーション維持のコツ
6. 学習リソースの活用法

ユーザーの学年や学力レベルに合わせた適切なアドバイスを心がけ、
わかりやすく丁寧な説明を提供してください。
必要に応じて例題や実践的なヒントも加えると効果的です。"""

        # 既存のメッセージ履歴を取得
        session_messages = await get_session_messages(
            db, 
            session_id, 
            current_user.id,
            chat_request.session_type
        )
        
        formatted_history = [
            {
                "role": "assistant" if msg.sender_type == "AI" else "user",
                "content": msg.content
            }
            for msg in session_messages
        ]

        messages = [
            {"role": "system", "content": system_message},
            *formatted_history,
            {"role": "user", "content": chat_request.message}
        ]

        # OpenAI APIを呼び出して回答を取得
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            temperature=0.7,
        )
        
        ai_response = response.choices[0].message.content

        # AIの回答を保存
        await save_chat_message(
            db=db,
            session_id=session_id,
            content=ai_response,
            sender_type="AI"
        )

        return {
            "session_id": session_id,
            "message": ai_response
        }
        
    except Exception as e:
        logger.error(f"学習支援チャットエラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="学習支援チャットの処理中にエラーが発生しました"
        )

@router.get("/analysis")
async def get_chat_analysis(
    session_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AIチャット対話の分析結果を取得する
    特定のセッションIDが提供されない場合は、すべてのチャットセッションの総合分析を返す
    """
    try:
        if session_id:
            # 特定のセッションの分析
            messages = await get_session_messages(
                db,
                session_id,
                current_user.id
            )
            
            if not messages:
                raise HTTPException(
                    status_code=404,
                    detail="指定されたチャットセッションが見つからないか、メッセージがありません"
                )
            
            # セッションのタイプを確認
            session = await get_or_create_chat_session(
                db=db,
                user_id=current_user.id,
                session_id=session_id
            )
            session_type = session.session_type
            
            # 分析のためのメッセージ履歴を整形
            chat_history = [
                {
                    "role": "assistant" if msg.sender_type == "AI" else "user",
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat()
                }
                for msg in messages
            ]
            
            # 分析用のプロンプトを設定
            analysis_prompt = f"""以下のチャット履歴を詳細に分析し、以下の点についてレポートを作成してください。
チャットタイプ: {session_type}

1. 主な話題やテーマ
2. ユーザーの関心事や懸念点
3. 特に重要な情報やインサイト
4. フォローアップが必要な項目
5. 次のステップの提案

チャット履歴:
{str(chat_history)}

分析結果はJSON形式ではなく、読みやすい日本語のテキスト形式で提供してください。
"""
        else:
            # すべてのセッションの総合分析
            sessions = await get_user_chat_sessions(
                db,
                current_user.id
            )
            
            if not sessions:
                raise HTTPException(
                    status_code=404,
                    detail="チャットセッションが見つかりません"
                )
            
            # セッションの概要を収集
            session_summaries = []
            for session in sessions[:5]:  # 最新の5セッションのみ分析
                messages = await get_session_messages(
                    db,
                    str(session.id),
                    current_user.id
                )
                
                if messages:
                    session_summaries.append({
                        "session_id": str(session.id),
                        "title": session.title,
                        "type": session.session_type,
                        "created_at": session.created_at.isoformat(),
                        "message_count": len(messages),
                        "first_user_message": messages[0].content if messages[0].sender_type == "USER" else (messages[1].content if len(messages) > 1 and messages[1].sender_type == "USER" else "")
                    })
            
            # 分析用のプロンプトを設定
            analysis_prompt = f"""以下のユーザーのチャットセッション概要を分析し、全体的な傾向と洞察をレポートしてください。

セッション概要:
{str(session_summaries)}

以下の点に注目して分析してください:
1. ユーザーの主な関心領域
2. 繰り返し出現するテーマや質問
3. 時間経過に伴う関心の変化
4. 学習パターンの特徴
5. 改善のための提案
6. 次に取り組むべき学習テーマの提案

分析結果はJSON形式ではなく、読みやすい日本語のテキスト形式で提供してください。
"""

        # OpenAI APIを使用して分析を実行
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "あなたはチャット対話を分析する専門家です。客観的かつ洞察に富んだ分析を提供してください。"},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.5,
        )
        
        analysis = response.choices[0].message.content
        
        return {
            "analysis": analysis,
            "created_at": datetime.now().isoformat(),
            "session_id": session_id if session_id else None
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"チャット分析エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="チャット分析の処理中にエラーが発生しました"
        )
