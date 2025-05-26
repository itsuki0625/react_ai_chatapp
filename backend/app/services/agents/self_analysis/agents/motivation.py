from .base_prompt import BaseSelfAnalysisAgent
import json
import re
from ..guardrails import motivation_guardrail

class MotivationAgent(BaseSelfAnalysisAgent):
    """
    モチベーション深掘りを行うエージェント
    """
    STEP_ID = "MOTIVATION"
    NEXT_STEP = "HISTORY"
    def __init__(self, **kwargs):
        super().__init__(
            step_id=self.STEP_ID,
            step_goal="原体験を深掘りし、動機づけの因果を可視化",
            instructions=(
                "あなたは自己分析支援 AI です。ユーザーの過去経験から "
                "『なぜそれが心を動かしたのか？』を 5W1H と感情で分解し、"
                "JSON 形式で出力してください。\n\n"
                "### 出力フォーマット\n"
                "{\n"
                '  "cot": "<あなたの思考過程>",\n'
                '  "chat": {\n'
                '    "episode": {\n'
                '      "when": "<年代・時期>",\n'
                '      "where": "<場所・文脈>",\n'
                '      "who": "<関与した人>",\n'
                '      "what": "<出来事>",\n'
                '      "why": "<当時の想い・背景>",\n'
                '      "how": "<具体的行動>",\n'
                '      "emotion": "<感情ラベル1語>",\n'
                '      "insight": "<そこから得た学び1文>"\n'
                '    },\n'
                '    "question": "<次に聞く1つだけの質問>"\n'
                "  }\n"
                "}\n\n"
                "### 例\n"
                "ユーザー入力: 祖父の病院探しが大変で〜\n"
                "出力例:\n"
                '{"chat":{"episode":{"when":"高校2年の夏","where":"地方都市","who":"祖父と私","what":"病院探しに半日費やした","why":"適切な情報が無かった","how":"口コミサイトを徹底的に検索","emotion":"焦り","insight":"医療情報の非対称性が高齢者の負担になると痛感した"},"question":"その時最も大変だった瞬間を具体的に教えてください"}}\n\n'
                "評価基準:\n"
                "1. episode 各フィールドが非空\n"
                "2. emotion は単語1つ (例: 喜び/悔しさ/焦り など)\n"
                "3. insight は 40 字以内\n"
                "4. question は敬語 1 文\n",
            ),
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
        # 1. 各フィールド非空
        if all(episode.get(f) for f in ["when","where","who","what","why","how","emotion","insight"]):
            score += 1
        # 2. emotionは単語1語
        if episode.get("emotion") and " " not in episode.get("emotion", ""):
            score += 1
        # 3. insightは40字以内
        if episode.get("insight") and len(episode.get("insight", "")) <= 40:
            score += 1
        # 4. questionは?を1つ含む
        if chat.get("question", "").count("?") == 1:
            score += 1
        return score

    async def run(self, messages, session_id=None):
        # Planフェーズ: 最初の出力を取得
        system_msg = {"role": "system", "content": self.instructions}
        draft_resp = await self.llm_adapter.chat_completion(
            messages=[system_msg, *messages], stream=False
        )
        data = json.loads(draft_resp.get("content", "{}"))
        # サーバー側自己採点
        score = self._grade_episode(data)
        # Reactフェーズ: スコア不足なら再生成指示
        if score < 4:
            fix_msg = {"role": "user", "content": f"評価基準に照らして{score}点でした。条件を満たすように再度同じフォーマットで出力してください。"}
            final_resp = await self.llm_adapter.chat_completion(
                messages=[system_msg, *messages, fix_msg], stream=False
            )
            data = json.loads(final_resp.get("content", "{}"))
        # 次ステップと最終ノートを含めて返却
        return {
            "content": json.dumps({"cot": data.get("cot"), "chat": data.get("chat")}, ensure_ascii=False),
            "final_notes": data.get("chat"),
            "next_step": self.NEXT_STEP
        }

    async def interactive_plan(self, messages, session_id=None):
        """
        PlanningEngineで3つのサブタスク（原体験選択→感情取得→学び取得）に分解し、
        各サブタスクを順次実行して結果をまとめて返します。
        """
        # サブタスクを生成
        plan = await self.planning_engine.create_plan(messages, session_id)
        results = []
        for sub in plan.tasks:
            res = await self.planning_engine.execute_sub_task(sub, self, session_id)
            results.append({"id": sub.id, "result": res})
        return {"plan": plan.dict(), "subtask_results": results} 