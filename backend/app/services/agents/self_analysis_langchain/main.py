from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
import inspect
import json
import logging

# Local application imports
from app.database.database import AsyncSessionLocal 
from app.models.self_analysis import SelfAnalysisSession 
from .steps.future import FutureStepAgent
from .steps.gap import GapStepAgent
from .steps.history import HistoryStepAgent
from .steps.motivation import MotivationStepAgent
from .steps.reflect import ReflectStepAgent
from .steps.vision import VisionStepAgent

logger = logging.getLogger(__name__)

# ステートスキーマ定義
class SelfAnalysisState(TypedDict):
    messages: list
    session_id: str
    next_step: str | None
    current_response: str | None  # Add field for current agent response
    user_message: str | None      # Add field for user-facing message

# ステップ実行のラッパー関数を定義
async def run_future_step(state: SelfAnalysisState) -> SelfAnalysisState:
    agent = FutureStepAgent()
    response = await agent(state)
    
    # Debug logging
    logger.info(f"FUTURE step response type: {type(response)}, content: {response}")
    
    # Extract user-facing message from JSON response if possible
    user_message = extract_user_message(response, "FUTURE")
    
    # ステップ完了判定に基づいて次のステップを決定
    step_completed = is_step_completed("FUTURE", response)
    next_step = "MOTIVATION" if step_completed else None
    
    logger.info(f"FUTURE step completed: {step_completed}, next_step: {next_step}")
    
    return {
        **state, 
        "next_step": next_step,
        "current_response": response,
        "user_message": user_message
    }

async def run_motivation_step(state: SelfAnalysisState) -> SelfAnalysisState:
    agent = MotivationStepAgent()
    response = await agent(state)
    
    # Debug logging
    logger.info(f"MOTIVATION step response type: {type(response)}, content: {response}")
    
    user_message = extract_user_message(response, "MOTIVATION")
    
    # ステップ完了判定に基づいて次のステップを決定
    step_completed = is_step_completed("MOTIVATION", response)
    next_step = "HISTORY" if step_completed else None
    
    logger.info(f"MOTIVATION step completed: {step_completed}, next_step: {next_step}")
    
    return {
        **state, 
        "next_step": next_step,
        "current_response": response,
        "user_message": user_message
    }

async def run_history_step(state: SelfAnalysisState) -> SelfAnalysisState:
    agent = HistoryStepAgent()
    response = await agent(state)
    
    # Debug logging
    logger.info(f"HISTORY step response type: {type(response)}, content: {response}")
    
    user_message = extract_user_message(response, "HISTORY")
    
    # ステップ完了判定に基づいて次のステップを決定
    step_completed = is_step_completed("HISTORY", response)
    next_step = "GAP" if step_completed else None
    
    logger.info(f"HISTORY step completed: {step_completed}, next_step: {next_step}")
    
    return {
        **state, 
        "next_step": next_step,
        "current_response": response,
        "user_message": user_message
    }

async def run_gap_step(state: SelfAnalysisState) -> SelfAnalysisState:
    agent = GapStepAgent()
    response = await agent(state)
    
    # Debug logging
    logger.info(f"GAP step response type: {type(response)}, content: {response}")
    
    user_message = extract_user_message(response, "GAP")
    
    # ステップ完了判定に基づいて次のステップを決定
    step_completed = is_step_completed("GAP", response)
    next_step = "VISION" if step_completed else None
    
    logger.info(f"GAP step completed: {step_completed}, next_step: {next_step}")
    
    return {
        **state, 
        "next_step": next_step,
        "current_response": response,
        "user_message": user_message
    }

async def run_vision_step(state: SelfAnalysisState) -> SelfAnalysisState:
    agent = VisionStepAgent()
    response = await agent(state)
    
    # Debug logging
    logger.info(f"VISION step response type: {type(response)}, content: {response}")
    
    user_message = extract_user_message(response, "VISION")
    
    # ステップ完了判定に基づいて次のステップを決定
    step_completed = is_step_completed("VISION", response)
    next_step = "REFLECT" if step_completed else None
    
    logger.info(f"VISION step completed: {step_completed}, next_step: {next_step}")
    
    return {
        **state, 
        "next_step": next_step,
        "current_response": response,
        "user_message": user_message
    }

async def run_reflect_step(state: SelfAnalysisState) -> SelfAnalysisState:
    agent = ReflectStepAgent()
    response = await agent(state)
    
    # Debug logging
    logger.info(f"REFLECT step response type: {type(response)}, content: {response}")
    
    user_message = extract_user_message(response, "REFLECT")
    
    # REFLECTステップは最終ステップなので常にNone
    next_step = None
    
    logger.info(f"REFLECT step completed, next_step: {next_step}")
    
    return {
        **state, 
        "next_step": next_step,  # End of flow
        "current_response": response,
        "user_message": user_message
    }

def extract_user_message(response: str | dict, step: str) -> str:
    """Extract user-facing message from agent response"""
    try:
        # Handle dictionary response directly
        if isinstance(response, dict):
            # Look for chat.question field
            if "chat" in response and "question" in response["chat"]:
                return response["chat"]["question"]
            # Look for other user-facing fields
            elif "user_visible" in response:
                return response["user_visible"]
            # Fallback for dict responses
            else:
                return get_step_continuation_message(step)
        
        # Handle string response
        elif isinstance(response, str):
            # Check for agent timeout/iteration limit errors
            if "Agent stopped due to iteration limit" in response or "time limit" in response:
                return get_step_continuation_message(step)
                
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                data = json.loads(response)
                if isinstance(data, dict):
                    # Look for chat.question field
                    if "chat" in data and "question" in data["chat"]:
                        return data["chat"]["question"]
                    # Look for other user-facing fields
                    elif "user_visible" in data:
                        return data["user_visible"]
                    # Fallback to step-specific message
                    else:
                        return get_step_continuation_message(step)
            
            # If not JSON, return the response as-is if it looks like a question
            if response and ("?" in response or "？" in response or "ください" in response):
                return response
            
            # Default fallback message
            return get_step_continuation_message(step)
        
        # Handle other types
        else:
            logger.warning(f"Unexpected response type {type(response)}: {response}")
            return get_step_continuation_message(step)
            
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to extract user message from response: {e}")
        return get_step_continuation_message(step)

def get_step_continuation_message(step: str) -> str:
    """ステップ継続時の適切なメッセージを取得"""
    step_messages = {
        "FUTURE": "将来の目標についてもう少し具体的に教えてください。どのような分野で、どのような課題を解決したいですか？",
        "MOTIVATION": "その目標を持つようになったきっかけや原体験について、5W1Hで詳しく教えてください。",
        "HISTORY": "これまでの経験や活動について、時系列で詳しく教えてください。特に印象的だった出来事はありますか？",
        "GAP": "現在の状況と目標とのギャップについて、具体的にどのような課題があるか教えてください。",
        "VISION": "理想の将来像について、一文で表現してみてください。",
        "REFLECT": "これまでの内容を振り返って、今後のアクションプランについて考えてみましょう。"
    }
    return step_messages.get(step, "続けて詳しく教えてください。")

# ステップ順序の定義
STEP_ORDER = ["FUTURE", "MOTIVATION", "HISTORY", "GAP", "VISION", "REFLECT"]

def determine_current_step(session_current_step: str, messages_count: int) -> str:
    """現在のセッション状態とメッセージ数から適切なステップを決定"""
    if not session_current_step or session_current_step not in STEP_ORDER:
        return "FUTURE"
    
    # セッションの現在ステップを返す
    return session_current_step

def get_next_step(current_step: str) -> str | None:
    """次のステップを取得"""
    try:
        current_index = STEP_ORDER.index(current_step)
        if current_index < len(STEP_ORDER) - 1:
            return STEP_ORDER[current_index + 1]
        return None  # 最後のステップ
    except ValueError:
        return "FUTURE"  # デフォルト

def is_step_completed(step: str, response: str | dict) -> bool:
    """ステップが完了したかどうかを判定"""
    try:
        # 辞書型の場合はそのまま使用、文字列の場合はJSONパース
        if isinstance(response, str):
            if not response.strip().startswith('{'):
                logger.debug(f"Response for {step} is not JSON: {response[:100]}")
                return False
            data = json.loads(response.strip())
        else:
            data = response

        # chatセクションが存在するかチェック
        if not isinstance(data, dict) or "chat" not in data:
            logger.debug(f"No chat section found for {step}: {data}")
            return False
            
        chat = data["chat"]
        
        if step == "FUTURE":
            # future, values, questionが適切に設定されているかチェック
            future_valid = (
                "future" in chat and 
                isinstance(chat["future"], str) and 
                len(chat["future"].strip()) > 0
            )
            values_valid = (
                "values" in chat and 
                isinstance(chat["values"], list) and 
                len(chat["values"]) >= 1  # 少なくとも1つあれば良い
            )
            question_valid = (
                "question" in chat and 
                isinstance(chat["question"], str) and 
                len(chat["question"].strip()) > 0
            )
            
            logger.debug(f"FUTURE step validation - future: {future_valid}, values: {values_valid}, question: {question_valid}")
            logger.debug(f"Chat content: {chat}")
            
            return future_valid and values_valid and question_valid
            
        elif step == "MOTIVATION":
            # episodeの全フィールドが埋まっているかチェック
            episode = chat.get("episode", {})
            required_fields = ["when", "where", "who", "what", "why", "how", "emotion", "insight"]
            
            # 初期の質問段階では完了していないと見なす
            if not episode or len(episode) < len(required_fields):
                logger.debug(f"MOTIVATION step incomplete - episode fields: {len(episode.keys()) if episode else 0}/{len(required_fields)}")
                return False
                
            return (
                isinstance(episode, dict) and
                all(field in episode and isinstance(episode[field], str) and len(episode[field].strip()) > 0 
                    for field in required_fields) and
                len(episode["insight"]) <= 40 and
                "question" in chat and 
                isinstance(chat["question"], str) and 
                len(chat["question"].strip()) > 0
            )
            
        elif step == "HISTORY":
            # timelineに適切なエントリがあるかチェック
            timeline = chat.get("timeline", [])
            return (
                isinstance(timeline, list) and
                len(timeline) > 0 and
                all(
                    isinstance(entry, dict) and
                    "year" in entry and isinstance(entry["year"], int) and
                    "event" in entry and isinstance(entry["event"], str) and len(entry["event"].strip()) > 0 and
                    "detail" in entry and isinstance(entry["detail"], str) and len(entry["detail"].strip()) > 0 and
                    "skills" in entry and isinstance(entry["skills"], list) and 1 <= len(entry["skills"]) <= 3 and
                    "values" in entry and isinstance(entry["values"], list) and 1 <= len(entry["values"]) <= 3
                    for entry in timeline
                ) and
                "question" in chat and 
                isinstance(chat["question"], str) and 
                len(chat["question"].strip()) > 0
            )
            
        elif step == "GAP":
            # gaps配列に適切なギャップ分析があるかチェック
            gaps = chat.get("gaps", [])
            valid_categories = ["knowledge", "skill", "resource", "network", "mindset"]
            return (
                isinstance(gaps, list) and
                3 <= len(gaps) <= 6 and
                all(
                    isinstance(gap, dict) and
                    "gap" in gap and isinstance(gap["gap"], str) and len(gap["gap"].strip()) > 0 and
                    "category" in gap and gap["category"] in valid_categories and
                    "root_causes" in gap and isinstance(gap["root_causes"], list) and 1 <= len(gap["root_causes"]) <= 3 and
                    "severity" in gap and isinstance(gap["severity"], int) and 1 <= gap["severity"] <= 5 and
                    "urgency" in gap and isinstance(gap["urgency"], int) and 1 <= gap["urgency"] <= 5 and
                    "recommend" in gap and isinstance(gap["recommend"], str) and len(gap["recommend"].strip()) > 0
                    for gap in gaps
                ) and
                "question" in chat and 
                isinstance(chat["question"], str) and 
                len(chat["question"].strip()) > 0
            )
            
        elif step == "VISION":
            # vision文が30字以内で適切に設定されているかチェック
            return (
                "vision" in chat and 
                isinstance(chat["vision"], str) and 
                len(chat["vision"].strip()) > 0 and
                len(chat["vision"]) <= 30 and
                (chat["vision"].endswith("する") or chat["vision"].endswith("なる")) and
                "tone_scores" in chat and isinstance(chat["tone_scores"], dict) and
                "uniq_score" in chat and isinstance(chat["uniq_score"], (int, float)) and 0 <= chat["uniq_score"] <= 1 and
                "question" in chat and 
                isinstance(chat["question"], str) and 
                len(chat["question"].strip()) > 0
            )
            
        elif step == "REFLECT":
            # insights, strengths, growth_edges, milestonesが設定されているかチェック
            return (
                "insights" in chat and isinstance(chat["insights"], list) and 3 <= len(chat["insights"]) <= 5 and
                "strengths" in chat and isinstance(chat["strengths"], list) and len(chat["strengths"]) == 3 and
                "growth_edges" in chat and isinstance(chat["growth_edges"], list) and len(chat["growth_edges"]) == 3 and
                "milestones" in chat and isinstance(chat["milestones"], list) and len(chat["milestones"]) > 0 and
                all(
                    isinstance(milestone, dict) and
                    "days" in milestone and isinstance(milestone["days"], int) and
                    "kpi" in milestone and isinstance(milestone["kpi"], str) and len(milestone["kpi"].strip()) > 0
                    for milestone in chat["milestones"]
                ) and
                "summary" in chat and isinstance(chat["summary"], str) and len(chat["summary"]) <= 140 and
                "question" in chat and 
                isinstance(chat["question"], str) and 
                len(chat["question"].strip()) > 0
            )
            
        return False
        
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
        logger.warning(f"Error checking step completion for {step}: {e}")
        return False

# 動的ノード選択関数  
def select_step_node(state: SelfAnalysisState) -> str:
    """状態に基づいて実行するステップを決定"""
    session_id = state.get("session_id", "")
    messages = state.get("messages", [])
    
    # DBから現在のステップを取得
    try:
        import asyncio
        async def get_current_step():
            async with AsyncSessionLocal() as db:
                sa = await db.get(SelfAnalysisSession, session_id)
                return sa.current_step if sa else "FUTURE"
        
        # 非同期関数を同期的に実行
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 既存のループ内で実行中の場合は新しいタスクとして実行
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, get_current_step())
                    current_step = future.result(timeout=5)
            else:
                current_step = asyncio.run(get_current_step())
        except (RuntimeError, Exception) as e:
            # イベントループ関連のエラーの場合は、同期的にDBアクセスを試行
            try:
                # 同期セッションを使って直接DBアクセス
                logger.warning(f"Cannot access event loop for session {session_id}, trying synchronous DB access: {e}")
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                from app.core.config import settings
                
                sync_engine = create_engine(settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))
                SyncSessionLocal = sessionmaker(bind=sync_engine)
                
                with SyncSessionLocal() as db:
                    sa = db.get(SelfAnalysisSession, session_id)
                    current_step = sa.current_step if sa else "FUTURE"
                    logger.info(f"Retrieved current step synchronously: {current_step}")
                    return determine_current_step(current_step, len(messages))
                    
            except Exception as sync_e:
                logger.error(f"Synchronous DB access also failed for session {session_id}: {sync_e}")
                return "FUTURE"
            
        return determine_current_step(current_step, len(messages))
    except Exception as e:
        logger.error(f"Error getting current step for session {session_id}: {e}")
        return "FUTURE"  # デフォルト

# 条件分岐でフェーズ移行を制御する関数を追加
def decide_next_step(state: SelfAnalysisState) -> str:
    """ステップ完了状況に基づいて次のアクションを決定"""
    session_id = state.get("session_id", "")
    current_response = state.get("current_response", "")
    
    try:
        import asyncio
        async def get_current_step_and_check():
            async with AsyncSessionLocal() as db:
                sa = await db.get(SelfAnalysisSession, session_id)
                if not sa:
                    return "FUTURE", False
                
                current_step = sa.current_step or "FUTURE"
                step_completed = is_step_completed(current_step, current_response)
                return current_step, step_completed
        
        # 非同期関数を同期的に実行
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, get_current_step_and_check())
                    current_step, step_completed = future.result(timeout=5)
            else:
                current_step, step_completed = asyncio.run(get_current_step_and_check())
        except (RuntimeError, Exception) as e:
            # イベントループ関連のエラーの場合は、同期的にDBアクセスを試行
            try:
                logger.warning(f"Cannot access event loop for session {session_id}, trying synchronous DB access: {e}")
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                from app.core.config import settings
                
                sync_engine = create_engine(settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))
                SyncSessionLocal = sessionmaker(bind=sync_engine)
                
                with SyncSessionLocal() as db:
                    sa = db.get(SelfAnalysisSession, session_id)
                    if not sa:
                        current_step, step_completed = "FUTURE", False
                    else:
                        current_step = sa.current_step or "FUTURE"
                        step_completed = is_step_completed(current_step, current_response)
                    logger.info(f"Retrieved step info synchronously: {current_step}, completed: {step_completed}")
                    
            except Exception as sync_e:
                logger.error(f"Synchronous DB access also failed for session {session_id}: {sync_e}")
                return END
        
        if step_completed:
            next_step = get_next_step(current_step)
            if next_step:
                logger.info(f"Step {current_step} completed, moving to {next_step}")
                # DB更新もここで実行して一貫性を保つ
                try:
                    from sqlalchemy import create_engine
                    from sqlalchemy.orm import sessionmaker
                    from app.core.config import settings
                    
                    sync_engine = create_engine(settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))
                    SyncSessionLocal = sessionmaker(bind=sync_engine)
                    
                    with SyncSessionLocal() as db:
                        sa = db.get(SelfAnalysisSession, session_id)
                        if sa:
                            sa.current_step = next_step
                            db.add(sa)
                            db.commit()
                            logger.info(f"Updated SelfAnalysisSession {session_id}: {current_step} -> {next_step}")
                except Exception as update_err:
                    logger.error(f"Failed to update step in decide_next_step: {update_err}")
                
                return next_step
            else:
                logger.info(f"All steps completed for session {session_id}")
                return END
        else:
            logger.info(f"Step {current_step} not completed, staying on current step")
            return END  # フローを終了してユーザーの次の入力を待つ
            
    except Exception as e:
        logger.error(f"Error in decide_next_step for session {session_id}: {e}")
        return END

# Graphオーケストレーターの構築
builder = StateGraph(SelfAnalysisState)

builder.add_node("FUTURE", run_future_step)
builder.add_node("MOTIVATION", run_motivation_step)
builder.add_node("HISTORY", run_history_step)
builder.add_node("GAP", run_gap_step)
builder.add_node("VISION", run_vision_step)
builder.add_node("REFLECT", run_reflect_step)

# 開始ノードを条件分岐で設定
builder.add_conditional_edges(
    START,
    select_step_node,
    {
        "FUTURE": "FUTURE",
        "MOTIVATION": "MOTIVATION", 
        "HISTORY": "HISTORY",
        "GAP": "GAP",
        "VISION": "VISION",
        "REFLECT": "REFLECT"
    }
)

# 各ステップから条件分岐で次のステップまたは終了を決定
builder.add_conditional_edges(
    "FUTURE",
    decide_next_step,
    {
        "MOTIVATION": "MOTIVATION",
        END: END
    }
)

builder.add_conditional_edges(
    "MOTIVATION", 
    decide_next_step,
    {
        "HISTORY": "HISTORY",
        END: END
    }
)

builder.add_conditional_edges(
    "HISTORY",
    decide_next_step, 
    {
        "GAP": "GAP",
        END: END
    }
)

builder.add_conditional_edges(
    "GAP",
    decide_next_step,
    {
        "VISION": "VISION", 
        END: END
    }
)

builder.add_conditional_edges(
    "VISION",
    decide_next_step,
    {
        "REFLECT": "REFLECT",
        END: END
    }
)

builder.add_edge("REFLECT", END)

orchestrator = builder.compile()

class SelfAnalysisOrchestrator:
    """
    LangChain + LangGraph を用いた自己分析オーケストレーターです。
    """
    def __init__(self):
        self.orchestrator = orchestrator

    async def run(self, messages: list, session_id: str):
        """
        messages: List of message dicts with 'role' and 'content'
        session_id: Session ID string
        """
        logger.info(f"SelfAnalysisOrchestrator.run starting for session {session_id} with {len(messages)} messages")
        
        # Ensure session exists before processing
        try:
            async with AsyncSessionLocal() as db:
                sa = await db.get(SelfAnalysisSession, session_id)
                if not sa:
                    sa = SelfAnalysisSession(id=session_id, current_step="FUTURE")
                    db.add(sa)
                    await db.commit()
                    logger.info(f"Created new SelfAnalysisSession for {session_id}")
                else:
                    logger.info(f"Found existing SelfAnalysisSession for {session_id}, step: {sa.current_step}")
        except Exception as db_err:
            logger.error(f"Database error creating session in SelfAnalysisOrchestrator: {db_err}", exc_info=True)
            # Continue execution even if DB session creation fails
        
        try:
            initial_state = SelfAnalysisState(
                messages=messages, 
                session_id=session_id, 
                next_step=None,
                current_response=None,
                user_message=None
            )
            logger.info(f"Initial state created: {initial_state}")
            
            result = await self.orchestrator.ainvoke(initial_state)
            logger.info(f"Orchestrator ainvoke completed. Result: {result}")
            
            # Note: DB updates are now handled within decide_next_step for consistency
            logger.info(f"Orchestrator completed for session {session_id}")
            
            # Return user-facing message instead of raw state
            user_message = result.get("user_message")
            if user_message:
                logger.info(f"Returning user_message: {user_message}")
                return {"user_visible": user_message}
            else:
                fallback_message = "ありがとうございます。自己分析を続けましょう。"
                logger.warning(f"No user_message found in result, using fallback: {fallback_message}")
                return {"user_visible": fallback_message}
                
        except Exception as e:
            logger.error(f"Error in SelfAnalysisOrchestrator.run for session {session_id}: {e}", exc_info=True)
            return {"user_visible": "申し訳ございませんが、自己分析処理中にエラーが発生しました。もう一度お試しください。"}
