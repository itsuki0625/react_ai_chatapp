import logging
import json
from .adapters import openai_adapter
from .guardrails import guardrail
from .context_resources import ctx_mgr, rm, trace

from .agents.future import FutureAgent
from .agents.motivation import MotivationAgent
from .agents.history import HistoryAgent
from .agents.gap import GapAnalysisAgent
from .agents.vision import VisionAgent
from .agents.reflect import ReflectAgent

from .tools.notes import note_store
from .tools.reflexion import reflection_store
from app.models.self_analysis import SelfAnalysisSession as Session
from app.database.database import AsyncSessionLocal

async def get_progress(session_id: str) -> str:
    """
    セッションの現在のステップを取得する。
    """
    async with AsyncSessionLocal() as db:
        sa_sess = await db.get(Session, session_id)
        if not sa_sess:
            # 初回呼び出し時はセッションを作成し、最初のステップに設定
            sa_sess = Session(id=session_id, current_step=STEP_FLOW[0])
            db.add(sa_sess)
            await db.commit()
        return sa_sess.current_step

STEP_FLOW = [
    "FUTURE",
    "MOTIVATION",
    "HISTORY",
    "GAP",
    "VISION",
    "REFLECT",
]

AGENTS = {
    "FUTURE": FutureAgent(),
    "MOTIVATION": MotivationAgent(),
    "HISTORY": HistoryAgent(),
    "GAP": GapAnalysisAgent(),
    "VISION": VisionAgent(),
    "REFLECT": ReflectAgent(),
}

# Define allowed tools for each step (used by BaseSelfAnalysisAgent)
ALLOWED_TOOLS = { step: [] for step in STEP_FLOW }
# Allow macro-reflexion step "ALL" without tools as well
ALLOWED_TOOLS["ALL"] = []

class SelfAnalysisOrchestrator:
    """
    自己分析エージェントのオーケストレーター。
    """

    async def run(self, user_input: str, session_id: str):
        # 現在のステップを取得
        step = await get_progress(session_id)
        agent = AGENTS.get(step)
        if not agent:
            raise ValueError(f"Unknown step: {step}")
        
        # ユーザー入力をLLM用のメッセージ形式に変換
        llm_messages = [{"role": "user", "content": user_input}]
        
        # PlanEngine を介してサブタスクを自動計画・実行
        result = await agent.run_with_plan(messages=llm_messages, session_id=session_id)

        # --- ステップ遷移ロジック ---
        # 各エージェントの NEXT_STEP (定数) が result["next_step"] として返る
        # それをセッション状態に保存し、次回呼び出し時に参照する
        current_step_from_result = result.get("next_step", step)
        if current_step_from_result != step:
            await self._advance(session_id, current_step_from_result)
        
        # ノート保存
        if "final_notes" in result:
            await note_store(session_id, step, result.get("final_notes"))
        
        # 応答文字列の抽出（JSON文字列の場合はchat.questionを抽出）
        raw = result.get("user_visible") or result.get("final_notes") or result.get("content")
        # E: rawが空の場合のガード
        if not raw:
            raw = "すみません、もう一度お願いできますか？"
        # 文字列の場合、JSONをパースして質問を返す
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                chat = parsed.get("chat") if isinstance(parsed, dict) else None
                question = None
                if isinstance(chat, dict):
                    question = chat.get("question")
                elif isinstance(parsed, dict) and "question" in parsed:
                    question = parsed.get("question")
                if question:
                    return question
            except Exception:
                return raw
            return raw
        # dictの場合は直接questionを返す
        if isinstance(raw, dict):
            if "question" in raw:
                return raw.get("question")
            chat = raw.get("chat")
            if isinstance(chat, dict) and "question" in chat:
                return chat.get("question")
        # それ以外は文字列化して返却
        return str(raw)

    async def _advance(self, session_id: str, next_step: str):
        """
        セッションの現在ステップを更新する。
        """
        if next_step == "FIN":
            return
        async with AsyncSessionLocal() as db:
            sa_sess = await db.get(Session, session_id)
            if sa_sess:
                sa_sess.current_step = next_step
                db.add(sa_sess)
                await db.commit()

    # _apply_patches は PostSessionReflexionAgent 削除に伴い不要になる
    # def _apply_patches(self, patches: dict):
    #     ... 