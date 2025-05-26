import logging
from .adapters import openai_adapter
from .guardrails import guardrail
from .context_resources import ctx_mgr, rm, trace

from .agents.future import FutureAgent
from .agents.motivation import MotivationAgent
from .agents.history import HistoryAgent
from .agents.gap import GapAnalysisAgent
from .agents.action import ActionPlanAgent
from .agents.impact import ImpactAgent
from .agents.univ import UniversityMapperAgent
from .agents.vision import VisionAgent
from .agents.reflect import ReflectAgent
from .agents.reflexion import PostSessionReflexionAgent

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
    "ACTION",
    "IMPACT",
    "UNIV",
    "VISION",
    "REFLECT",
]

AGENTS = {
    "FUTURE": FutureAgent(),
    "MOTIVATION": MotivationAgent(),
    "HISTORY": HistoryAgent(),
    "GAP": GapAnalysisAgent(),
    "ACTION": ActionPlanAgent(),
    "IMPACT": ImpactAgent(),
    "UNIV": UniversityMapperAgent(),
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

    async def run(self, session_id: str, user_input: str):
        # 現在のステップを取得
        step = await get_progress(session_id)
        agent = AGENTS.get(step)
        if not agent:
            raise ValueError(f"Unknown step: {step}")

        # MOTIVATIONステップではインタラクティブプランを使用
        if step == "MOTIVATION":
            # PlanningEngineでサブタスクを実行
            return await agent.interactive_plan(
                messages=[{"role": "user", "content": user_input}],
                session_id=session_id
            )
        # エージェントを通常実行
        result = await agent.run(
            messages=[{"role": "user", "content": user_input}],
            session_id=session_id
        )
        # GuardrailViolationError時に自動リトライ
        err = result.get("error", {})
        if err.get("type") == "GuardrailViolationError":
            logging.warning(f"[{step}] Guardrail violation: {err.get('message')}. Retrying once...")
            result = await agent.run(
                messages=[{"role": "user", "content": user_input}],
                session_id=session_id
            )
            err2 = result.get("error", {})
            if err2.get("type") == "GuardrailViolationError":
                logging.error(f"[{step}] Guardrail violation persists after retry: {err2.get('message')}")
                # UX途切れ防止のためerror情報を削除
                result.pop("error", None)

        # フォールバック: LLMのストリーム応答が空の場合は非ストリーミングで再取得
        if not result.get("content"):
            from app.services.agents.self_analysis.agents.base_prompt import default_openai_adapter
            # システムプロンプトを取得
            system_prompt = agent.instructions
            adapter = default_openai_adapter()
            # 非ストリーミングでChatCompletionを呼ぶ
            final = await adapter.chat_completion(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_input}],
                stream=False,
                model=agent.model
            )
            # 結果をresultにセット
            result["content"] = final.get("content", "")
            # final_notesとしても保存
            result["final_notes"] = final.get("content", "")

        # マイクロリフレクションのリトライ処理
        additional = result.get("additional", {})
        if additional.get("reflexion_status") == "retry":
            await reflection_store(session_id, step, "micro", additional.get("reason"))
            result = await agent.run(
                messages=[{"role": "user", "content": additional.get("next_action")}],
                session_id=session_id
            )

        # ノートを保存
        await note_store(session_id, step, result.get("final_notes"))
        # ステップを進める (next_stepがNoneであれば更新しない)
        next_step = result.get("next_step")
        if next_step:
            await self._advance(session_id, next_step)

        # セッション最終ステップ(REFLECT)後のマクロリフレクション
        if step == "REFLECT":
            macro = await PostSessionReflexionAgent().run(messages=[], session_id=session_id)
            await reflection_store(session_id, "ALL", "macro", macro.get("content"))
            self._apply_patches(macro.get("additional", {}))

        # クライアントに返す内容(user_visible)がない場合はLLM出力のcontentを返す
        return result.get("user_visible") or result.get("content")

    async def _advance(self, session_id: str, next_step: str):
        """
        セッションの現在ステップを更新する。
        """
        if next_step == "FIN":
            return
        async with AsyncSessionLocal() as db:
            sa_sess = await db.get(Session, session_id)
            sa_sess.current_step = next_step
            db.add(sa_sess)
            await db.commit()

    def _apply_patches(self, patches: dict):
        """
        マクロリフレクションからのパッチを適用する。
        """
        # TODO: パッチ適用ロジックを実装
        logging.debug(f"Applying patches: {patches}") 