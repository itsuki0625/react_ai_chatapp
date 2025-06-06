from .base_prompt import BaseSelfAnalysisAgent, load_md
import json
import re
from ..tools.normalize import normalize_values

class FutureAgent(BaseSelfAnalysisAgent):
    """
    将来やりたいことまとめ＆価値観抽出を行うエージェント
    """
    STEP_ID = "FUTURE"
    STEP_GOAL = "将来の夢や理想の姿、およびそれに関連する重要な価値観や興味関心を明確にする。最終的に、自己分析を通じて深掘りしたいテーマを選定する。"
    NEXT_STEP = "MOTIVATION"
    def __init__(self, **kwargs):
        super().__init__(
            step_id=self.STEP_ID,
            step_goal="将来やりたいことを1-2行でまとめ、価値観キーワードを3語抽出",
            instructions="""あなたは学生の自己分析を支援するAIです。
必ず以下のJSONフォーマットで出力してください：
{
  "cot": "<あなたの思考過程>",
  "chat": {
    "future": "<1-2行>",
    "values": ["<価値観1>", "<価値観2>", "<価値観3>"],
    "question": "<ユーザーに投げる1つの質問>"
  }
}

### 例①
ユーザー入力: 私はテクノロジーで地域医療の格差を解消したいです
出力例:
{"cot":"地域医療格差を解消したいというユーザーの意図を要約し、価値観を抽出しました。","chat":{"future":"テクノロジーで地域医療格差を解消する","values":["公平性","医療DX","地域貢献"],"question":"次に、具体的にどのような医療DX技術に興味がありますか？"}}

評価基準：
・future が30文字以内 / 主語を含む能動表現 / 手段 or 対象が入っている
・values は名詞1語、抽象度は "行動指針" レベル（例：挑戦、共創、倫理）
・question はフレンドリー敬語で1文のみ
""",
            tools=[normalize_values],
            **kwargs
        )

    def _parse_score(self, cot: str) -> int:
        """cot内から"score":数字を抽出して返す"""
        match = re.search(r'"score"\s*:\s*(\d+)', cot)
        return int(match.group(1)) if match else 0


    # async def run(self, messages, session_id=None): # 削除
    #     ...