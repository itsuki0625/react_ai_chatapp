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
            instructions=(
                "あなたは自己分析セッションのマクロリフレクションAIです。"
                "以下の3つの役割を果たしてください：\n"
                "1. セッション全体のマクロサマリー\n"
                "2. 各ステップの品質スコアとボトルネックを含むメタ分析\n"
                "3. 改善パッチとしてプロンプト、ガードレール、ツール設定の自動チューニング提案\n\n"
                "以下のJSONフォーマットで出力してください:\n"
                "{\n"
                "  \"cot\": \"<思考過程>\",\n"
                "  \"chat\": {\n"
                "    \"macro_summary\": \"<セッション全体の物語要約 (200字以内)>\",\n"
                "    \"insight_matrix\": [\n"
                "      {\"step\": \"FUTURE\", \"score\": 4.5, \"insight\": \"価値観が明確\"},\n"
                "      {\"step\": \"GAP\", \"score\": 3.2, \"insight\": \"severity評価が甘い\"}\n"
                "    ],\n"
                "    \"next_focus\": [\"GAP\", \"ACTION\"],\n"
                "    \"patches\": {\n"
                "      \"GAP\": {\n"
                "        \"prompt_append\": \"severity と urgency は必ず根拠としてデータ引用を含める。\",\n"
                "        \"guardrail\": {\"severity_min\": 2, \"urgency_min\": 2}\n"
                "      },\n"
                "      \"ACTION\": {\n"
                "        \"param_update\": {\"kpi_regex\": \"[0-9]{2}%\"}\n"
                "      }\n"
                "    },\n"
                "    \"question\": \"今回の気づきで特に印象深かったことは？\"\n"
                "  }\n"
                "}\n\n"
                "### 評価基準\n"
                "- macro_summary は 200字以内で物語風に要約\n"
                "- insight_matrix は各ステップに対しスコア(1～5)と具体的洞察を含む\n"
                "- next_focus は 2～3 ステップを選定\n"
                "- patches には具体的提案を含める\n"
                "- question は敬語で1文\n"
            ),
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