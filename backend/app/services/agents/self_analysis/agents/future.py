from .base_prompt import BaseSelfAnalysisAgent
import json
import re
from ..tools.normalize import normalize_values

class FutureAgent(BaseSelfAnalysisAgent):
    """
    将来やりたいことまとめ＆価値観抽出を行うエージェント
    """
    STEP_ID = "FUTURE"
    NEXT_STEP = "MOTIVATION"
    def __init__(self, **kwargs):
        super().__init__(
            step_id=self.STEP_ID,
            step_goal="将来やりたいことを1-2行でまとめ、価値観キーワードを3語抽出",
            instructions=(
                # ① 出力フォーマット固定
                "あなたは学生の自己分析を支援するAIです。\n"
                "必ず以下のJSONフォーマットで出力してください：\n"
                "{\n"
                '  "cot": "<あなたの思考過程>",\n'
                '  "chat": {\n'
                '    "future": "<1-2行>",\n'
                '    "values": ["<価値観1>", "<価値観2>", "<価値観3>"],\n'
                '    "question": "<ユーザーに投げる1つの質問>"\n'
                "  }\n"
                "}\n\n"
                # ② n-shot 例示
                "### 例①\n"
                "ユーザー入力: 私はテクノロジーで地域医療の格差を解消したいです\n"
                "出力例:\n"
                '{"future":"テクノロジーで地域医療格差を解消する","values":["公平性","医療DX","地域貢献"]}\n\n'
                # ③ 評価基準を先に示す
                "評価基準：\n"
                "・future が30文字以内 / 主語を含む能動表現 / 手段 or 対象が入っている\n"
                "・values は名詞1語、抽象度は \"行動指針\" レベル（例：挑戦、共創、倫理）\n"
                "・question はフレンドリー敬語で1文のみ\n",
            ),
            **kwargs
        )

    def _parse_score(self, cot: str) -> int:
        """cot内から"score":数字を抽出して返す"""
        match = re.search(r'"score"\s*:\s*(\d+)', cot)
        return int(match.group(1)) if match else 0

    async def run(self, messages, session_id=None):
        # Planフェーズ: ドラフト＋自己採点を取得
        plan_prompt = self.instructions + "\nさらにこの回答を5点満点で自己採点し、JSONで{cot,chat,score,critique}を返してください。"
        system_msg = {"role": "system", "content": plan_prompt}
        draft = await self.llm_adapter.chat_completion(
            messages=[system_msg, *messages], stream=False
        )
        # JSONパース
        data = json.loads(draft.get("content", "{}"))
        score = self._parse_score(draft.get("content", ""))
        # values 正規化
        chat = data.get("chat", {})
        if "values" in chat:
            normalized = await normalize_values(session_id, chat.get("values", []))
            chat["values"] = normalized
        # Reactフェーズ: スコアが満点でなければ修正要求
        if score < 5:
            fix_msg = {"role": "user", "content": f"自己採点は{score}点でした。理由を踏まえて再度同じJSONフォーマットで出力してください。"}
            final = await self.llm_adapter.chat_completion(
                messages=[system_msg, *messages, fix_msg], stream=False
            )
            result_json = json.loads(final.get("content", "{}"))
            # 修正版でも values 正規化
            chat = result_json.get("chat", {})
            if "values" in chat:
                normalized = await normalize_values(session_id, chat.get("values", []))
                chat["values"] = normalized
        else:
            result_json = data
        # 次ステップと最終ノートを含めて返却
        return {
            "content": json.dumps({"cot": result_json.get("cot"), "chat": result_json.get("chat")}, ensure_ascii=False),
            "final_notes": result_json.get("chat"),
            "next_step": self.NEXT_STEP
        }