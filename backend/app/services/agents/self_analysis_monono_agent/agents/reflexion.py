from .base_prompt import BaseSelfAnalysisAgent

class PostSessionReflexionAgent(BaseSelfAnalysisAgent):
    """
    セッション全体のマクロリフレクションを行うエージェント。以下を実行：
    1. マクロサマリー
    2. メタ分析 - 各ステップの品質スコアとボトルネック
    3. 改善パッチ - プロンプト/ガードレール/ツール設定の自動チューニング提案
    """
    def __init__(self, **kwargs):
        super().__init__(
            step_id="ALL",
            step_goal="マクロリフレクション",
            instructions="""あなたは自己分析セッションのマクロリフレクションAIです。以下の3つの役割を果たしてください：
1. セッション全体のマクロサマリー
2. 各ステップの品質スコアとボトルネックを含むメタ分析
3. 改善パッチとしてプロンプト、ガードレール、ツール設定の自動チューニング提案

以下のJSONフォーマットで出力してください:
{
  "cot": "<思考過程>",
  "chat": {
    "macro_summary": "<セッション全体の物語要約 (200字以内)>",
    "insight_matrix": [
      {"step": "FUTURE", "score": 4.5, "insight": "価値観が明確"},
      {"step": "GAP", "score": 3.2, "insight": "severity評価が甘い"}
    ],
    "next_focus": ["GAP", "ACTION"],
    "patches": {
      "GAP": {
        "prompt_append": "severity と urgency は必ず根拠としてデータ引用を含める。",
        "guardrail": {"severity_min": 2, "urgency_min": 2}
      },
      "ACTION": {
        "param_update": {"kpi_regex": "[0-9]{2}%"}
      }
    },
    "question": "今回の気づきで特に印象深かったことは？"
  }
}

### 評価基準
- macro_summary は 200字以内で物語風に要約
- insight_matrix は各ステップに対しスコア(1～5)と具体的洞察を含む
- next_focus は 2～3 ステップを選定
- patches には具体的提案を含める
- question は敬語で1文
""",
            **kwargs
        )

    async def interactive_plan(self, messages, session_id=None):
        """
        PlanningEngineで2つのサブタスク（evaluate_steps, generate_patches）を実行
        """
        from app.services.agents.monono_agent.components.planning_engine import SubTask, Plan
        tasks = [
            SubTask(id="evaluate_steps", description="TraceLogger & notes からスコアリング→ insight_matrix 生成", depends_on=[]),
            SubTask(id="generate_patches", description="低スコア step を対象にプロンプト & guardrail & param 推奨変更を作成", depends_on=["evaluate_steps"]),
        ]
        results = []
        for sub in tasks:
            res = await self.planning_engine.execute_sub_task(sub, self, session_id)
            results.append({"id": sub.id, "result": res})
        plan = Plan(tasks=tasks)
        return {"plan": plan.dict(), "subtask_results": results}

    async def run(self, messages, session_id=None):
        return await self.interactive_plan(messages, session_id) 