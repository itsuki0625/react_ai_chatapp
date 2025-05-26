from .base_prompt import BaseSelfAnalysisAgent
from ..guardrails import gap_guardrail
import json

class GapAnalysisAgent(BaseSelfAnalysisAgent):
    """
    ギャップ&原因抽出を行うエージェント
    """
    STEP_ID = "GAP"
    NEXT_STEP = "ACTION"

    def __init__(self, **kwargs):
        super().__init__(
            step_id=self.STEP_ID,
            step_goal="目標 (FutureAgent) と現状 (HistoryAgent) の差分を抽出し、原因を特定",
            instructions=(
                "あなたは自己分析支援AIです。\n"
                "FutureAgent と HistoryAgent のアウトプットを踏まえ、"
                "ギャップを洗い出し、原因を 5Whys で深掘りしてください。\n\n"
                "### 出力フォーマット\n"
                "{\n"
                "  \"cot\":\"<思考過程>\",\n"
                "  \"chat\": {\n"
                "    \"gaps\":[\n"
                "      {\n"
                "        \"gap\":\"医療業界の専門知識不足\",\n"
                "        \"category\":\"knowledge\",            # knowledge / skill / resource / network / mindset\n"
                "        \"root_causes\":[\n"
                "          \"医療従事者ネットワークがない\",\n"
                "          \"学術論文を読む習慣が無い\"\n"
                "        ],\n"
                "        \"severity\":4,      # 1(低)–5(高) ＝ 目標達成への影響度\n"
                "        \"urgency\":3,       # 1(低)–5(高) ＝ 対応優先度\n"
                "        \"recommend\":\"医工連携ゼミ参加を今学期内に申し込む\"\n"
                "      }\n"
                "    ],\n"
                "    \"question\":\"上記の中で最も優先的に解決したいギャップはどれですか？1つ選んでください\"\n"
                "  }\n"
                "}\n\n"
                "### 評価基準\n"
                "1. gaps は 3〜6 件\n"
                "2. root_causes は各 gap につき 1〜3 件\n"
                "3. severity・urgency は整数 1–5\n"
                "4. category は定義語のみ\n"
                "5. question は敬語 1 文\n"
            ),
            guardrail=gap_guardrail,
            **kwargs
        ) 

    async def interactive_plan(self, messages, session_id=None):
        """
        PlanningEngineで3つのサブタスク（collect_diff→analyze_cause→score_rank）に分解し、結果を返します。
        """
        from app.services.agents.monono_agent.components.planning_engine import SubTask, Plan
        # サブタスク定義
        tasks = [
            SubTask(id="collect_diff", description="Future のゴール要素 × History の実績の差分を生成し、ギャップ候補をリストアップしてください", depends_on=[]),
            SubTask(id="analyze_cause", description="各ギャップについて5Whysで深掘りし、1〜3件の因子を抽出してください", depends_on=["collect_diff"]),
            SubTask(id="score_rank", description="各ギャップに対してseverityとurgencyを打点し、影響度×解決コストから推奨度を計算してください", depends_on=["analyze_cause"]),
        ]
        results = []
        for sub in tasks:
            res = await self.planning_engine.execute_sub_task(sub, self, session_id)
            results.append({"id": sub.id, "result": res})
        plan = Plan(tasks=tasks)
        return {"plan": plan.dict(), "subtask_results": results} 

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

    async def run(self, messages, session_id=None):
        system_msg = {"role": "system", "content": self.instructions}
        draft_resp = await self.llm_adapter.chat_completion(messages=[system_msg, *messages], stream=False)
        try:
            data = json.loads(draft_resp.get("content", "{}"))
        except:
            data = {}
        # 自己採点
        score = self._grade_gaps(data)
        if score < 5:
            fix_msg = {"role": "user", "content": f"評価基準に照らして{score}点でした。条件を満たすように再度同じフォーマットで出力してください。"}
            final_resp = await self.llm_adapter.chat_completion(messages=[system_msg, *messages, fix_msg], stream=False)
            try:
                data = json.loads(final_resp.get("content", "{}"))
            except:
                pass
        # 後処理: 重複排除 & スコア正規化
        chat = data.get("chat", {})
        gaps = chat.get("gaps", [])
        cleaned = self._dedup_gaps(gaps)
        normalized = self._normalize_scores(cleaned)
        gap_count = len(normalized)
        avg_severity = sum(g.get("severity", 0) for g in normalized) / gap_count if gap_count else 0
        chat["gaps"] = normalized
        data["chat"] = chat
        # トレース: gap_count / avg_severity を記録
        self.trace_logger.trace("gap_metrics", {"gap_count": gap_count, "avg_severity": avg_severity})
        return {
            "content": json.dumps({"cot": data.get("cot"), "chat": chat}, ensure_ascii=False),
            "final_notes": chat,
            "next_step": self.NEXT_STEP
        } 