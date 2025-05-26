from .base_prompt import BaseSelfAnalysisAgent
import re
from datetime import datetime
from app.services.agents.monono_agent.components.guardrail import GuardrailViolationError

def cost_estimate(resources: list[str]) -> float:
    """リソース文字列から金額を抽出して合計を返す"""
    total = 0.0
    for r in resources:
        m = re.search(r'(\d+[\d,]*)円', r)
        if m:
            total += float(m.group(1).replace(',',''))
    return total

def normalize_deadline(date_str: str) -> str:
    """ISOフォーマットの日付文字列を YYYY-MM-DD に整形、失敗時は TBD を返す"""
    try:
        d = datetime.fromisoformat(date_str)
        return d.strftime("%Y-%m-%d")
    except:
        return "TBD"

class ActionPlanAgent(BaseSelfAnalysisAgent):
    """
    短中長期プランを策定するエージェント
    """
    STEP_ID = "ACTION"
    NEXT_STEP = "IMPACT"

    def __init__(self, **kwargs):
        super().__init__(
            step_id=self.STEP_ID,
            step_goal="ギャップを解消する短中長期アクションプラン策定",
            instructions=(
              "あなたは自己分析支援AIです。GapAnalysisAgent の出力 (gaps) を受け取り、"
              "短期(≤6ヶ月)・中期(6-24ヶ月)・長期(>24ヶ月) の3段階アクションプランを作成してください。"
              "必ず以下の JSON 形式で返答します：\n"
              "{\n"
              "  \"cot\":\"<思考過程>\",\n"
              "  \"chat\": {\n"
              "    \"plans\":[\n"
              "      {\n"
              "        \"timeframe\":\"short\",               # short|mid|long\n"
              "        \"goal\":\"医療専門知識の基礎習得\",\n"
              "        \"task\":\"医工連携ゼミに参加し、週1回講義を受ける\",\n"
              "        \"kpi\":\"修了テスト80点以上\",\n"
              "        \"deadline\":\"2026-01-31\",\n"
              "        \"resources\":[\"授業料4万円\",\"週3h\"],\n"
              "        \"risk\":\"学業との両立が困難→時間割調整\",\n"
              "        \"gap_ref\":\"医療業界の専門知識不足\"\n"
              "      }\n"
              "    ],\n"
              "    \"question\":\"上記プランで不安がある点はありますか？1つ教えてください\"\n"
              "  }\n"
              "}\n\n"
              "### 評価基準\n"
              "・各 timeframe で 1〜3 件\n"
              "・goal は 30 字以内、task は 60 字以内\n"
              "・deadline は YYYY-MM-DD 形式\n"
              "・kpi は \"数値 or 回数\" を含む\n"
              "・resources に金額 or 時間の記述が必須\n"
            ),
            **kwargs
        ) 

    async def interactive_plan(self, messages, session_id=None):
        """
        PlanningEngineで3つのサブタスク（select_gaps→draft_plan→validate_rank）を順次実行し、結果をまとめて返します。
        """
        from app.services.agents.monono_agent.components.planning_engine import SubTask, Plan
        tasks = [
            SubTask(
                id="select_gaps",
                description="severity≥4/urgency≥4を優先し、各 timeframe (short, mid, long) にギャップを配分し、選択結果を selected 配列で返してください。",
                depends_on=[]
            ),
            SubTask(
                id="draft_plan",
                description="selected のギャップを SMART タスク (Specific,Measurable,Achievable,Relevant,Time-bound) に変換し、各 timeframe ごとに plan_drafts 配列で返してください。",
                depends_on=["select_gaps"]
            ),
            SubTask(
                id="validate_rank",
                description="plan_drafts を受け取り、各プランの KPI、deadline、risk を検証し、優先度順にソートして final_plans 配列で返してください。",
                depends_on=["draft_plan"]
            ),
        ]
        results = []
        for sub in tasks:
            res = await self.planning_engine.execute_sub_task(sub, self, session_id)
            results.append({"id": sub.id, "result": res})
        plan = Plan(tasks=tasks)
        # 後処理: validate_rankの結果からfinal_plansを取得し期限を正規化、リソース管理とコストトラッキング
        validate_res = next((r["result"] for r in results if r["id"] == "validate_rank"), {})
        final_plans = validate_res.get("final_plans", [])
        # 期限の正規化
        for p in final_plans:
            if "deadline" in p:
                p["deadline"] = normalize_deadline(p.get("deadline", ""))
        # コスト見積もり
        total_cost = sum(cost_estimate(p.get("resources", [])) for p in final_plans)
        # per-timeframe costs を extra_cfg に保存
        plan_costs = {p.get("timeframe"): cost_estimate(p.get("resources", [])) for p in final_plans}
        self.extra_cfg["plan_costs"] = plan_costs
        # 予算チェック
        budget = self.resource_manager.cost_tracking.get("budget", float("inf"))
        if not self.resource_manager.can_execute("plan", total_cost):
            raise GuardrailViolationError(
                f"プランの総コスト{total_cost}円が予算{budget}円を超えました。コストを圧縮してください。"
            )
        # コストを ResourceManager に記録
        self.resource_manager.track_usage("tool:plan", {"cost": total_cost})
        # トレースロガーにも出力
        self.trace_logger.trace("plan_cost", {"total_cost": total_cost})
        # 結果に反映
        validate_res["final_plans"] = final_plans
        return {"plan": plan.dict(), "subtask_results": results}

    async def run(self, messages, session_id=None):
        return await self.interactive_plan(messages, session_id) 