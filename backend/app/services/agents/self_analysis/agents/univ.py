from .base_prompt import BaseSelfAnalysisAgent
from app.services.agents.monono_agent.components.learning_engine import LearningEngine
from ..tools.university import course_search, admission_stats, fit_score

class UniversityMapperAgent(BaseSelfAnalysisAgent):
    """
    大学・学部・ゼミのマッピングとフィット度評価を行うエージェント
    """
    STEP_ID = "UNIV"
    NEXT_STEP = "VISION"

    def __init__(self, **kwargs):
        super().__init__(
            step_id=self.STEP_ID,
            step_goal="大学・学部・ゼミのマッピングとフィット度評価",
            instructions="""あなたは進学アドバイザーAIです。FutureAgent・GapAnalysisAgent・ActionPlanAgent・ImpactAgent の結果を踏まえ、最適な大学/学部/ゼミを 3～5 件推奨してください。フォーマットは以下の JSON：

{
  "cot":"<思考過程>",
  "chat": {
    "universities":[
      {
        "name":"慶應義塾大学 総合政策学部",
        "program":"医療政策学Ⅱ（△△教授）",
        "fit":0.83,                       # 0–1
        "reasons":["医療DXカリキュラムが充実","地域医療の実証PJ多数"],
        "admission":{"偏差値":72,"募集人員":250,"倍率":4.1},
        "gap_to_fill":["TOEFL 90→現状 75","活動実績: 医療系インターン"],
        "next_step":"8月までに教授の研究室訪問予約"
      }
    ],
    "summary":"最もフィットするのは…(120字以内)",
    "question":"上記の大学のうち、特に気になるところはありますか？"
  }
}

### 評価基準
・universities 3～5 件
・fit 0～1、小数2桁
・reasons 1～3 文
・gap_to_fill 1～3 件
・question 敬語 1 文
""",
            tools=[course_search, admission_stats, fit_score],
            learning_engine=LearningEngine(),
            **kwargs
        )

    async def interactive_plan(self, messages, session_id=None):
        """
        PlanningEngineで4つのサブタスク（gather_criteria→search_catalog→score_and_rank→fill_gap_actions）を順次実行し、結果をまとめて返します。
        """
        from app.services.agents.monono_agent.components.planning_engine import SubTask, Plan
        tasks = [
            SubTask(
                id="gather_criteria",
                description="将来像・values・gap・impact をまとめて検索クエリ化",
                depends_on=[]
            ),
            SubTask(
                id="search_catalog",
                description="course_searchツール で DB/API から候補大学・学部・ゼミ取得",
                depends_on=["gather_criteria"]
            ),
            SubTask(
                id="score_and_rank",
                description="Fit Score (内容重み付け) ＋ Admission Feasibility を合算し、上位5件を選択して返してください",
                depends_on=["search_catalog"]
            ),
            SubTask(
                id="fill_gap_actions",
                description="各候補に不足項目と具体アクションを付与して返してください",
                depends_on=["score_and_rank"]
            ),
        ]
        results = []
        for sub in tasks:
            res = await self.planning_engine.execute_sub_task(sub, self, session_id)
            results.append({"id": sub.id, "result": res})
        plan = Plan(tasks=tasks)

        # 後処理: univ_mapping トレース & 学習
        fill_res = next((r["result"] for r in results if r["id"] == "fill_gap_actions"), {})
        if isinstance(fill_res, dict):
            unis = fill_res.get("universities", [])
        elif isinstance(fill_res, list):
            unis = fill_res
        else:
            unis = []
        avg_fit = sum(u.get("fit", 0) for u in unis) / len(unis) if unis else 0
        self.trace_logger.trace("univ_mapping", {"count": len(unis), "avg_fit": avg_fit})
        if self.learning_engine:
            self.learning_engine.track_success_patterns(
                task_description="univ_mapping",
                approach_details={"universities": unis},
                was_successful=True
            )
        return {"plan": plan.dict(), "subtask_results": results}

    async def run(self, messages, session_id=None):
        return await self.interactive_plan(messages, session_id) 