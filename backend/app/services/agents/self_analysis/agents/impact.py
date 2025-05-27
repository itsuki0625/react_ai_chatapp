from .base_prompt import BaseSelfAnalysisAgent
from ..guardrails import impact_guardrail

class ImpactAgent(BaseSelfAnalysisAgent):
    """
    定量インパクト – KPI × ベースライン → 期待値（Before / After / Δ％）
    定性インパクト – 社会・経済・個人など 5 視点で物語化
    優先度付け – ステークホルダー重要度 × 達成確率でランク
    """
    STEP_ID = "IMPACT"
    NEXT_STEP = "UNIV"

    def __init__(self, **kwargs):
        super().__init__(
            step_id=self.STEP_ID,
            step_goal="定量＋定性インパクトの算定と優先度化",
            instructions=(
                "あなたは自己分析支援AIです。ActionPlanAgent で策定した plans を実行した場合の"
                "インパクトを以下フォーマットで示しなさい。\n\n"
                "{\n"
                "  \"cot\":\"<思考過程>\",\n"
                "  \"chat\": {\n"
                "    \"impacts\":[\n"
                "      {\n"
                "        \"stakeholder\":\"高齢者\",\n"
                "        \"domain\":\"social\",      # social|economic|environmental|personal|organizational\n"
                "        \"metric\":\"平均通院距離 (km)\",\n"
                "        \"baseline\":5.3,\n"
                "        \"expected\":3.5,\n"
                "        \"horizon\":\"1y\",          # 期間\n"
                "        \"assumption\":\"アプリ導入率30％\",\n"
                "        \"confidence\":0.7         # 0–1\n"
                "      }\n"
                "    ],\n"
                "    \"narrative\":\"上記の改善により…(120字以内)\",\n"
                "    \"question\":\"最も優先すべきインパクトはどれですか？\"\n"
                "  }\n"
                "}\n\n"
                "### 評価基準\n"
                "・impacts は 3–6 件\n"
                "・baseline と expected は数値\n"
                "・confidence は 0–1 小数\n"
                "・narrative 120 字以内、question 敬語 1 文\n"
            ),
            guardrail=impact_guardrail,
            **kwargs
        )

    async def interactive_plan(self, messages, session_id=None):
        """
        PlanningEngineで3つのサブタスク（collect_metrics→project_impact→rank_prioritize）を順次実行し、結果をまとめて返します。
        """
        from app.services.agents.monono_agent.components.planning_engine import SubTask, Plan
        tasks = [
            SubTask(
                id="collect_metrics",
                description="各 plan から KPI を抽出（「修了テスト80点→合格者数」など換算）",
                depends_on=[]
            ),
            SubTask(
                id="project_impact",
                description="参考データベースでベースライン算出 → 期待値計算 & 信頼度推定を行って返してください",
                depends_on=["collect_metrics"]
            ),
            SubTask(
                id="rank_prioritize",
                description="利害影響 × 信頼度でスコアを計算し、高→低順にソートして返してください",
                depends_on=["project_impact"]
            ),
        ]
        results = []
        for sub in tasks:
            res = await self.planning_engine.execute_sub_task(sub, self, session_id)
            results.append({"id": sub.id, "result": res})
        plan = Plan(tasks=tasks)
        # 後処理: impact_summary を trace_logger に記録
        # project_impact の結果から impacts を取得
        project_res = next((r['result'] for r in results if r['id'] == 'project_impact'), {})
        impacts = project_res.get('impacts', []) or []
        # delta% の平均を計算
        if impacts:
            avg_delta = sum(i.get('delta%', 0) for i in impacts) / len(impacts)
        else:
            avg_delta = 0
        self.trace_logger.trace('impact_summary', {'impact_count': len(impacts), 'avg_delta%': avg_delta})
        return {'plan': plan.dict(), 'subtask_results': results}

    async def run(self, messages, session_id=None):
        return await self.interactive_plan(messages, session_id) 