from .base_prompt import BaseSelfAnalysisAgent
import json
from ..guardrails import history_guardrail
from app.services.agents.monono_agent.components.learning_engine import LearningEngine

class HistoryAgent(BaseSelfAnalysisAgent):
    """
    過去の経験を時系列で整理・可視化を行うエージェント
    """
    STEP_ID = "HISTORY"
    NEXT_STEP = "GAP"

    def __init__(self, **kwargs):
        # LearningEngineとHistory専用Guardrailを組み込み
        super().__init__(
            step_id=self.STEP_ID,
            step_goal="過去経験を年表形式で整理し、スキル／価値観もタグ付け",
            instructions=(
                "あなたは自己分析支援AIです。ユーザーの過去経験を時系列で整理し、"
                "以下の JSON フォーマットで出力してください。\n\n"
                "{\n"
                "  \"cot\": \"<思考過程>\",\n"
                "  \"chat\": {\n"
                "    \"timeline\": [\n"
                "      {\n"
                "        \"year\": 2023,\n"
                "        \"event\": \"プログラミング部立ち上げ\",\n"
                "        \"detail\": \"高校で医療レビューアプリを開発し全国大会入賞\",\n"
                "        \"skills\": [\"Python\",\"リーダーシップ\"],\n"
                "        \"values\": [\"挑戦\",\"協働\"]\n"
                "      },\n"
                "      ...\n"
                "    ],\n"
                "    \"question\": \"<次に聞く1文>\"\n"
                "  }\n"
                "}\n\n"
                "### 評価基準\n"
                "• timeline は昇順ソート\n"
                "• skills / values は 1 ～ 3 個ずつ\n"
                "• question は敬語で 1 文のみ\n"
                "年は整数、skillsは英単語、valuesは日本語1語で出力してください。\n"
            ),
            guardrail=history_guardrail,
            learning_engine=LearningEngine(),
            **kwargs
        ) 

    async def interactive_plan(self, messages, session_id=None):
        """
        PlanningEngineで3つのサブタスク（収集→整形→タグ付け）に分解し、各サブタスクを順次実行して結果をまとめて返します。
        """
        from app.services.agents.monono_agent.components.planning_engine import SubTask, Plan
        # サブタスク定義
        tasks = [
            SubTask(id="collect_raw", description="小学校～現在までの主要経験を年代付きで全部教えてください", depends_on=[]),
            SubTask(id="normalize_order", description="以下リストを昇順に並べ替え、重複があればマージしてください", depends_on=["collect_raw"]),
            SubTask(id="tagging", description="各イベントに得たスキル2つ、価値観1語を付けてください", depends_on=["normalize_order"]),
        ]
        results = []
        # トレース: 計画サブタスク一覧を記録
        self.trace_logger.trace("history_interactive_plan", {"tasks": [t.id for t in tasks]})
        # 各サブタスクを順次実行
        for sub in tasks:
            res = await self.planning_engine.execute_sub_task(sub, self, session_id)
            # リソース使用量を記録
            usage = res.get("usage", {}) if isinstance(res, dict) else {}
            self.resource_manager.track_usage("llm", usage)
            results.append({"id": sub.id, "result": res})
        # Planオブジェクトを生成してdict化
        plan = Plan(tasks=tasks)
        return {"plan": plan.dict(), "subtask_results": results} 

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

    async def run(self, messages, session_id=None):
        system_msg = {"role": "system", "content": self.instructions}
        draft_resp = await self.llm_adapter.chat_completion(messages=[system_msg, *messages], stream=False)
        # ResourceManager: LLMトークン使用量を追跡
        self.resource_manager.track_usage("llm", draft_resp.get("usage", {}))
        try:
            data = json.loads(draft_resp.get("content", "{}"))
        except:
            data = {}
        # 自己採点
        score = self._grade_history(data)
        if score < 4:
            fix_msg = {"role": "user", "content": f"評価基準に照らして{score}点でした。条件を満たすように再度同じフォーマットで出力してください。"}
            final_resp = await self.llm_adapter.chat_completion(messages=[system_msg, *messages, fix_msg], stream=False)
            # 戻り値の使用量も追跡
            self.resource_manager.track_usage("llm", final_resp.get("usage", {}))
            try:
                data = json.loads(final_resp.get("content", "{}"))
            except:
                pass
        # 後処理: 重複排除 & ソート
        chat = data.get("chat", {})
        original_tl = chat.get("timeline", [])
        original_len = len(original_tl)
        cleaned = self._dedup_and_sort(original_tl)
        dedup_count = original_len - len(cleaned)
        chat["timeline"] = cleaned
        data["chat"] = chat
        # トレース: タイムライン長と重複除去数を記録
        self.trace_logger.trace("history_metrics", {"timeline_length": original_len, "dedup_count": dedup_count})
        # LearningEngine: スキル抽出ミスパターンを記録
        if self.learning_engine:
            self.learning_engine.track_success_patterns(
                task_description="history_timeline_processing",
                approach_details={"original_length": original_len, "dedup_count": dedup_count, "score": score},
                was_successful=(score >= 4 and dedup_count == 0)
            )
        # 表示用 Markdown テーブル整形
        markdown = self._format_markdown_table(chat["timeline"])
        return {
            "content": json.dumps({"cot": data.get("cot"), "chat": chat}, ensure_ascii=False),
            "final_notes": chat,
            "next_step": self.NEXT_STEP,
            "user_visible": markdown
        } 