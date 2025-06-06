from .base_prompt import BaseSelfAnalysisAgent, load_md
import json
import re
from ..guardrails import motivation_guardrail

class MotivationAgent(BaseSelfAnalysisAgent):
    """
    モチベーション深掘りを行うエージェント
    """
    STEP_ID = "MOTIVATION"
    STEP_GOAL = "なぜその将来像を抱くようになったのか、具体的な出来事や経験（原体験）を5Whysなどの手法で深掘りし、動機の核心を明らかにする。"
    NEXT_STEP = "HISTORY"
    def __init__(self, **kwargs):
        super().__init__(
            step_id=self.STEP_ID,
            step_goal="原体験を深掘りし、動機づけの因果を可視化",
            instructions="""あなたは自己分析支援 AI です。ユーザーの過去経験から『なぜそれが心を動かしたのか？』を5W1Hと感情で分解し、JSON形式で出力してください。

### 出力フォーマット
{
  "cot": "<あなたの思考過程>",
  "chat": {
    "episode": {
      "when": "<年代・時期>",
      "where": "<場所・文脈>",
      "who": "<関与した人>",
      "what": "<出来事>",
      "why": "<当時の想い・背景>",
      "how": "<具体的行動>",
      "emotion": "<感情ラベル1語>",
      "insight": "<そこから得た学び1文>"
    },
    "question": "<次に聞く1つだけの質問>"
  }
}

### 例
ユーザー入力: 祖父の病院探しが大変で〜
出力例:
{"chat":{"episode":{"when":"高校2年の夏","where":"地方都市","who":"祖父と私","what":"病院探しに半日費やした","why":"適切な情報が無かった","how":"口コミサイトを徹底的に検索","emotion":"焦り","insight":"医療情報の非対称性が高齢者の負担になると痛感した"},"question":"その時最も大変だった瞬間を具体的に教えてください"}}

評価基準:
1. episode 各フィールドが非空
2. emotion は単語1つ (例: 喜び/悔しさ/焦り など)
3. insight は 40 字以内
4. question は敬語 1 文
""",
            guardrail=motivation_guardrail,
            **kwargs,
        )

    def _parse_score(self, cot: str) -> int:
        """cot内から"score":数字を抽出して返す"""
        match = re.search(r'"score"\s*:\s*(\d+)', cot)
        return int(match.group(1)) if match else 0

    def _grade_episode(self, data: dict) -> int:
        """サーバー側でepisode出力を評価し、4点満点でスコアを返す"""
        score = 0
        chat = data.get("chat", {})
        episode = chat.get("episode", {})
        if all(episode.get(f) for f in ["when","where","who","what","why","how","emotion","insight"]):
            score += 1
        if episode.get("emotion") and " " not in episode.get("emotion", ""):
            score += 1
        if episode.get("insight") and len(episode.get("insight", "")) <= 40:
            score += 1
        if chat.get("question", "").count("?") == 1:
            score += 1
        return score

    # async def run(self, messages, session_id=None): # 削除
    #     ...

    # async def interactive_plan(self, messages, session_id=None): # 削除
    #     ... 