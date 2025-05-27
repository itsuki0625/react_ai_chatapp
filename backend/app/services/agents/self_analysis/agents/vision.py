from .base_prompt import BaseSelfAnalysisAgent
from ..tools.vision import ngram_similarity, tone_score
from ..guardrails import vision_guardrail
from app.services.agents.monono_agent.components.learning_engine import LearningEngine

class VisionAgent(BaseSelfAnalysisAgent):
    """
    キャリアビジョンを1行で確定するエージェント
    """
    STEP_ID = "VISION"
    NEXT_STEP = "REFLECT"

    def __init__(self, **kwargs):
        super().__init__(
            step_id=self.STEP_ID,
            step_goal="1 行ビジョン確定",
            instructions=(
                "あなたはキャリアビジョン策定 AI です。\n"
                "Future / Gap / Action / Impact / Univ すべてを踏まえ、"
                "30 字以内 1 文のビジョンを考案してください。\n\n"
                "### 出力 JSON\n"
                "{\n"
                "  \"cot\":\"<思考過程>\",\n"
                "  \"chat\": {\n"
                "    \"vision\":\"医療格差を AI でゼロにする\",\n"
                "    \"tone_scores\":{\"excitement\":6,\"social\":7,\"feasible\":5},\n"
                "    \"uniq_score\":0.42,\n"
                "    \"alt_taglines\":[\n"
                "      \"誰もが医療に届く社会を創る\",\n"
                "      \"医療アクセスの壁を壊すAIリーダー\"\n"
                "    ],\n"
                "    \"question\":\"このビジョンはあなたの言葉としてしっくり来ますか？\"\n"
                "  }\n"
                "}\n\n"
                "### 評価基準\n"
                "- vision 30 字以内、語尾は「する/なる」\n"
                "- tone_scores 各 1–7\n"
                "- uniq_score 0–1（低いほど独自）\n"
                "- question 敬語 1 文\n"
            ),
            tools=[ngram_similarity, tone_score],
            learning_engine=LearningEngine(),
            guardrail=vision_guardrail,
            **kwargs
        )

    async def interactive_plan(self, messages, session_id=None):
        """
        PlanningEngineで3つのサブタスク（draft_candidates→score_filter→refine_wording）を順次実行し、結果をまとめて返します。
        """
        from app.services.agents.monono_agent.components.planning_engine import SubTask, Plan
        tasks = [
            SubTask(
                id="draft_candidates",
                description="価値観×将来像×インパクトから候補 3～5 本生成",
                depends_on=[]
            ),
            SubTask(
                id="score_filter",
                description="excitement/social/feasible & uniq_score を算出 → 最高スコアを選定",
                depends_on=["draft_candidates"]
            ),
            SubTask(
                id="refine_wording",
                description="30 字以内に圧縮・リズム調整・語尾「する/なる」で確定",
                depends_on=["score_filter"]
            ),
        ]
        results = []
        for sub in tasks:
            res = await self.planning_engine.execute_sub_task(sub, self, session_id)
            results.append({"id": sub.id, "result": res})
        plan = Plan(tasks=tasks)
        # 後処理: vision_final トレース & 学習
        refine_res = next((r["result"] for r in results if r["id"] == "refine_wording"), {})
        v = refine_res.get("vision", "")
        tone = refine_res.get("tone_scores", {}) or {}
        uniq = refine_res.get("uniq_score", 0)
        self.trace_logger.trace(
            "vision_final",
            {"len": len(v), "excite": tone.get("excitement"), "uniq": uniq}
        )
        if self.learning_engine:
            self.learning_engine.track_success_patterns(
                task_description="vision_final",
                approach_details={"vision": v, "tone_scores": tone, "uniq_score": uniq},
                was_successful=True
            )
        return {"plan": plan.dict(), "subtask_results": results}

    async def run(self, messages, session_id=None):
        return await self.interactive_plan(messages, session_id) 