from .base_prompt import BaseSelfAnalysisAgent, load_md
from ..guardrails import reflect_guardrail

class ReflectAgent(BaseSelfAnalysisAgent):
    """
    セッション最終振り返りを行うエージェント
    """
    STEP_ID = "REFLECT"
    STEP_GOAL = "各ステップの成果やプロセスを振り返り、自己理解が深まった点や新たな気づきを整理する（マイクロリフレクション）。また、自己分析全体を通じて得られた学びや、今後の行動への示唆をまとめる（マクロリフレクション）。"
    NEXT_STEP = "FIN"

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

    # interactive_plan は BaseSelfAnalysisAgent.run_with_plan が担うため削除
    # async def interactive_plan(self, messages, session_id=None):
    #     ...

    # run メソッドは BaseSelfAnalysisAgent.run_with_plan が担う (実質 interactive_plan を呼び出していた)
    # async def run(self, messages, session_id=None):
    #     return await self.interactive_plan(messages, session_id) 