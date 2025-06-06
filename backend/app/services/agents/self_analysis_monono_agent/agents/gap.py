from .base_prompt import BaseSelfAnalysisAgent, load_md
from ..guardrails import gap_guardrail
import json

class GapAnalysisAgent(BaseSelfAnalysisAgent):
    """
    ギャップ&原因抽出を行うエージェント
    """
    STEP_ID = "GAP"
    STEP_GOAL = "明確になった将来像と、年表で整理された現状の自分との間に存在するギャップ（知識、スキル、経験、実績など）を具体的に特定し、その根本原因を分析する。克服すべき課題に優先順位を付ける。"
    NEXT_STEP = "VISION"

    def __init__(self, **kwargs):
        super().__init__(
            step_id=self.STEP_ID,
            step_goal="目標 (FutureAgent) と現状 (HistoryAgent) の差分を抽出し、原因を特定",
            instructions="""あなたは自己分析支援AIです。
FutureAgent と HistoryAgent のアウトプットを踏まえ、ギャップを洗い出し、原因を 5Whys で深掘りしてください。

### 出力フォーマット
{
  "cot":"<思考過程>",
  "chat": {
    "gaps":[
      {
        "gap":"医療業界の専門知識不足",
        "category":"knowledge",            # knowledge / skill / resource / network / mindset
        "root_causes":[
          "医療従事者ネットワークがない",
          "学術論文を読む習慣が無い"
        ],
        "severity":4,      # 1(低)–5(高) ＝ 目標達成への影響度
        "urgency":3,       # 1(低)–5(高) ＝ 対応優先度
        "recommend":"医工連携ゼミ参加を今学期内に申し込む"
      }
    ],
    "question":"上記の中で最も優先的に解決したいギャップはどれですか？1つ選んでください"
  }
}

### 評価基準
1. gaps は 3〜6 件
2. root_causes は各 gap につき 1〜3 件
3. severity・urgency は整数 1–5
4. category は定義語のみ
5. question は敬語 1 文
""",
            guardrail=gap_guardrail,
            **kwargs
        ) 

    @staticmethod
    def _dedup_gaps(gaps: list[dict]) -> list[dict]:
        seen = set()
        res = []
        for g in gaps:
            key = g.get("gap")
            if key not in seen:
                res.append(g)
                seen.add(key)
        return res

    @staticmethod
    def _normalize_scores(gaps: list[dict]) -> list[dict]:
        for g in gaps:
            g["severity"] = min(max(int(g.get("severity", 1)), 1), 5)
            g["urgency"] = min(max(int(g.get("urgency", 1)), 1), 5)
        return gaps

    def _grade_gaps(self, data: dict) -> int:
        score = 0
        chat = data.get("chat", {})
        gaps = chat.get("gaps", [])
        # 1. gaps は 3〜6 件
        if 3 <= len(gaps) <= 6:
            score += 1
        # 2. root_causes は各 gap につき 1〜3 件
        if all(isinstance(g.get("root_causes"), list) and 1 <= len(g.get("root_causes")) <= 3 for g in gaps):
            score += 1
        # 3. severity・urgency は整数 1–5
        if all(isinstance(g.get("severity"), int) and 1 <= g.get("severity") <= 5 for g in gaps) and all(isinstance(g.get("urgency"), int) and 1 <= g.get("urgency") <= 5 for g in gaps):
            score += 1
        # 4. category は定義語のみ
        allowed = {"knowledge", "skill", "resource", "network", "mindset"}
        if all(g.get("category") in allowed for g in gaps):
            score += 1
        # 5. question は敬語 1 文 (？が1つ)
        question = chat.get("question", "")
        if question.count("?") == 1:
            score += 1
        return score

    # run メソッドは BaseSelfAnalysisAgent.run_with_plan が担うため削除
    # async def run(self, messages, session_id=None):
    #     ...

    # interactive_plan は BaseSelfAnalysisAgent.run_with_plan が担うため削除
    # async def interactive_plan(self, messages, session_id=None):
    #     ... 