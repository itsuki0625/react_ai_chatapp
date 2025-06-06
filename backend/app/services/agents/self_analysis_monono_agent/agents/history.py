from .base_prompt import BaseSelfAnalysisAgent, load_md
import json
from ..guardrails import history_guardrail
from app.services.agents.monono_agent.components.learning_engine import LearningEngine

class HistoryAgent(BaseSelfAnalysisAgent):
    """
    過去の経験を時系列で整理・可視化を行うエージェント
    """
    STEP_ID = "HISTORY"
    STEP_GOAL = "過去の重要な出来事、学び、達成、失敗などを時系列で整理し、関連する感情や気づきも記録する。一見関係なさそうなアルバイト・趣味・家庭環境なども網羅的に質問し、Markdown形式の年表を生成する。"
    NEXT_STEP = "GAP"

    def __init__(self, **kwargs):
        # LearningEngineとHistory専用Guardrailを組み込み
        super().__init__(
            step_id=self.STEP_ID,
            step_goal="過去経験を年表形式で整理し、スキル／価値観もタグ付け",
            instructions="""あなたは自己分析支援AIです。ユーザーの過去経験を時系列で整理し、以下の JSON フォーマットで出力してください。

{
  "cot": "<思考過程>",
  "chat": {
    "timeline": [
      {
        "year": 2023,
        "event": "プログラミング部立ち上げ",
        "detail": "高校で医療レビューアプリを開発し全国大会入賞",
        "skills": ["Python","リーダーシップ"],
        "values": ["挑戦","協働"]
      },
      ...
    ],
    "question": "<次に聞く1文>"
  }
}

### 評価基準
・timeline は昇順ソート
・skills / values は 1 ～ 3 個ずつ
・question は敬語で 1 文のみ
年は整数、skills は英単語、values は日本語1語で出力してください。
""",
            guardrail=history_guardrail,
            learning_engine=LearningEngine(),
            **kwargs
        ) 

    def _grade_history(self, data: dict) -> int:
        score = 0
        chat = data.get("chat", {})
        timeline = chat.get("timeline", [])
        # 年は整数
        if all(isinstance(item.get("year"), int) for item in timeline): score += 1
        # 昇順ソート
        if all(timeline[i]["year"] <= timeline[i+1]["year"] for i in range(len(timeline)-1)): score += 1
        # skills は 1-3個, 重複なし
        if all(isinstance(item.get("skills"), list) and 1 <= len(item["skills"]) <= 3 and len(item["skills"]) == len(set(item["skills"])) for item in timeline): score += 1
        # values は 1-3個, 重複なし
        if all(isinstance(item.get("values"), list) and 1 <= len(item["values"]) <= 3 and len(item["values"]) == len(set(item["values"])) for item in timeline): score += 1
        # question は?が1つ
        question = chat.get("question", "")
        if question.count("?") + question.count("？") == 1: score += 1
        return score

    @staticmethod
    def _dedup_and_sort(timeline: list[dict]) -> list[dict]:
        seen = set()
        cleaned = []
        for item in timeline:
            key = (item.get("year"), item.get("event"))
            if key not in seen:
                cleaned.append(item)
                seen.add(key)
        return sorted(cleaned, key=lambda x: x.get("year", 0))

    @staticmethod
    def _format_markdown_table(timeline: list[dict]) -> str:
        header = "| 年 | 出来事 | スキル | 価値観 |\n|---|---|---|---|\n"
        rows = []
        for item in timeline:
            year = item.get("year", "")
            event = item.get("event", "")
            skills = ", ".join(item.get("skills", []))
            values = ", ".join(item.get("values", []))
            rows.append(f"| {year} | {event} | {skills} | {values} |")
        return header + "\n".join(rows) 