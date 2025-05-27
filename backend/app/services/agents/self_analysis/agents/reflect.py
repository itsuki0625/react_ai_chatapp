from .base_prompt import BaseSelfAnalysisAgent
from ..guardrails import reflect_guardrail

class ReflectAgent(BaseSelfAnalysisAgent):
    """
    セッション最終振り返りを行うエージェント
    """
    STEP_ID = "REFLECT"
    # 最終ステップのためNEXT_STEPは定義しないかFINに遷移
    NEXT_STEP = None

    def __init__(self, **kwargs):
        super().__init__(
            step_id=self.STEP_ID,
            step_goal="セッション最終振り返り",
            instructions="""あなたは自己分析セッションの振り返り AI です。VALUES〜VISION までの全ノート・CoT を読んだうえで、以下 JSON フォーマットでアウトプットしてください。

{
  "cot":"<思考過程>",
  "chat": {
    "insights":["行動が最速の学習である", ...],
    "strengths":["課題発見力",...],
    "growth_edges":["仮説検証の頻度",...],
    "milestones":[
      {"days":30,"kpi":"医工ゼミ出願完了"},
      {"days":90,"kpi":"TOEFL 80→90"},
      {"days":365,"kpi":"医療DXインターン1社経験"}
    ],
    "tips":["Notion で週レビュー","友人と月1共有"],
    "summary":"…(140字)",
    "question":"本日の学びを一言で表すと何ですか？"
  }
}

### 評価基準
- insights 3〜5 行
- strengths / growth_edges 各 3 行
- milestones に KPI 数値 or 状態変化を含む
- summary 140 字以内
- question 敬語 1 文
""",
            guardrail=reflect_guardrail,
            **kwargs
        )

    async def interactive_plan(self, messages, session_id=None):
        """
        PlanningEngineで2つのサブタスク（synthesize_findings→format_polish）を順次実行し、結果をまとめて返します。
        """
        from app.services.agents.monono_agent.components.planning_engine import SubTask, Plan
        tasks = [
            SubTask(
                id="synthesize_findings",
                description="全ステップの note / cot / reflection を要約 → raw insights, strengths, edges 抽出",
                depends_on=[]
            ),
            SubTask(
                id="format_polish",
                description="テンプレに整形・文字数調整・ランキング（重要度順）",
                depends_on=["synthesize_findings"]
            ),
        ]
        results = []
        for sub in tasks:
            res = await self.planning_engine.execute_sub_task(sub, self, session_id)
            results.append({"id": sub.id, "result": res})
        plan = Plan(tasks=tasks)
        return {"plan": plan.dict(), "subtask_results": results}

    async def run(self, messages, session_id=None):
        return await self.interactive_plan(messages, session_id) 