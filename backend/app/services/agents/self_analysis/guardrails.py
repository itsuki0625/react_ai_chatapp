import re
from app.services.agents.monono_agent.components.guardrail import BaseGuardrail, GuardrailViolationError
import json  # 追加: JSONパース用

class SelfAnalysisGuardrail(BaseGuardrail):
    """
    PII ブロックと一つだけ質問を含めることを enforce するガードレール
    """
    def __init__(self):
        config = {
            "max_plan_tokens": 120,
            "max_iterations": 3,
            "blocked_output_regex": [r"(?i)pii", r"\d{4}-\d{4}-\d{4}-\d{4}"],
        }
        super().__init__(config)

    async def check_output(self, response_chunk, agent_name=None, session_id=None, user_id=None):
        # 基底クラスのチェックを実行
        chunk = await super().check_output(response_chunk, agent_name, session_id, user_id)
        # 最終的な応答チャンクで質問数を検証
        data = chunk.get("data", {}) or {}
        content = data.get("content", "")
        if content:
            # 質問マークの数をカウント（「？」）
            q_count = content.count("?")
            if q_count != 1:
                raise GuardrailViolationError(
                    f"返答の質問数が{q_count}個です。必ず1つだけ質問してください。"
                )
        return chunk

class FutureGuardrail(SelfAnalysisGuardrail):
    """
    FutureAgent専用の出力フォーマット検証Guardrail: 値観3語固定・各単語4文字以内を強制
    """
    async def check_output(self, response_chunk, agent_name=None, session_id=None, user_id=None):
        # 基底のチェックを実行
        chunk = await super().check_output(response_chunk, agent_name, session_id, user_id)
        data = chunk.get("data", {}) or {}
        content = data.get("content", "")
        try:
            parsed = json.loads(content)
            values = parsed.get("chat", {}).get("values", [])
            if len(values) != 3 or any(len(v) > 4 for v in values):
                raise ValueError("valuesフォーマット不正")
        except Exception:
            raise GuardrailViolationError("出力フォーマット不正: 価値観は3語かつ各語4文字以内である必要があります。")
        return chunk

guardrail = SelfAnalysisGuardrail()  # シングルトンインスタンスとしてエクスポート
future_guardrail = FutureGuardrail()  # FutureAgent専用ガードレールインスタンス

class MotivationGuardrail(SelfAnalysisGuardrail):
    """
    MotivationAgent専用ガードレール: episode各フィールド非空、emotionは単語1語、insight<=40文字、questionは1文
    """
    async def check_output(self, response_chunk, agent_name=None, session_id=None, user_id=None):
        chunk = await super().check_output(response_chunk, agent_name, session_id, user_id)
        data = chunk.get("data", {}) or {}
        content = data.get("content", "")
        try:
            parsed = json.loads(content)
            chat = parsed.get("chat", {})
            episode = chat.get("episode", {})
            # 各episodeフィールドが非空か
            for field in ["when", "where", "who", "what", "why", "how", "emotion", "insight"]:
                if not episode.get(field):
                    raise ValueError(f"episode.{field} is empty")
            # emotion は単語1語
            if " " in episode["emotion"]:
                raise ValueError("emotion must be single word")
            # insight は 40文字以内
            if len(episode["insight"]) > 40:
                raise ValueError("insight too long")
            # question は ? を1つ含む
            question = chat.get("question", "")
            if question.count("?") != 1:
                raise ValueError("question must contain exactly one '?'")
        except Exception:
            raise GuardrailViolationError("MotivationAgent出力フォーマット不正: episodeやquestionの条件を確認してください。")
        return chunk

motivation_guardrail = MotivationGuardrail()  # MotivationAgent専用ガードレールインスタンス

class HistoryGuardrail(SelfAnalysisGuardrail):
    """
    HistoryAgent専用ガードレール: タイムラインの年は整数、昇順、skills/valuesの個数制限
    """
    async def check_output(self, response_chunk, agent_name=None, session_id=None, user_id=None):
        chunk = await super().check_output(response_chunk, agent_name, session_id, user_id)
        data = chunk.get("data", {}) or {}
        content = data.get("content", "")
        try:
            parsed = json.loads(content)
            tl = parsed.get("chat", {}).get("timeline", [])
            # 年が整数であること
            if not all(isinstance(e.get("year"), int) for e in tl):
                raise ValueError("year が整数でない")
            # 昇順であること
            if tl != sorted(tl, key=lambda x: x.get("year", 0)):
                raise ValueError("昇順でない")
            # skills/values の個数制限
            for e in tl:
                if len(e.get("skills", [])) > 3 or len(e.get("values", [])) > 3:
                    raise ValueError("tags 多すぎ")
        except Exception:
            raise GuardrailViolationError("HistoryAgent出力フォーマット不正: timelineを確認してください。")
        return chunk

history_guardrail = HistoryGuardrail()  # HistoryAgent専用ガードレールインスタンス

class GapGuardrail(SelfAnalysisGuardrail):
    """
    GapAnalysisAgent専用ガードレール: categoryの検証、severity/urgencyの範囲チェック
    """
    async def check_output(self, response_chunk, agent_name=None, session_id=None, user_id=None):
        chunk = await super().check_output(response_chunk, agent_name, session_id, user_id)
        data = chunk.get("data", {}) or {}
        content = data.get("content", "")
        try:
            parsed = json.loads(content)
            gaps = parsed.get("chat", {}).get("gaps", [])
            for g in gaps:
                cat = g.get("category")
                if cat not in ["knowledge","skill","resource","network","mindset"]:
                    raise ValueError("不正 category")
                sev = g.get("severity")
                urg = g.get("urgency")
                if not isinstance(sev, int) or not 1 <= sev <= 5:
                    raise ValueError("severity範囲外")
                if not isinstance(urg, int) or not 1 <= urg <= 5:
                    raise ValueError("urgency範囲外")
        except Exception:
            raise GuardrailViolationError("GapAgent出力フォーマット不正: categoryやscoreを確認してください。")
        return chunk

gap_guardrail = GapGuardrail()  # GapAnalysisAgent専用ガードレールインスタンス

class ActionGuardrail(SelfAnalysisGuardrail):
    """
    ActionPlanAgent専用ガードレール: timeframe と KPI の検証を行います。
    """
    async def check_output(self, response_chunk, agent_name=None, session_id=None, user_id=None):
        # 基底のチェックを実行
        chunk = await super().check_output(response_chunk, agent_name, session_id, user_id)
        data = chunk.get("data", {}) or {}
        content = data.get("content", "")
        try:
            parsed = json.loads(content)
            plans = parsed.get("chat", {}).get("plans", [])
            for p in plans:
                timeframe = p.get("timeframe")
                if timeframe not in ["short", "mid", "long"]:
                    raise ValueError("timeframe不正")
                kpi = p.get("kpi", "")
                if not any(ch.isdigit() for ch in kpi):
                    raise ValueError("KPIに数値なし")
        except Exception:
            raise GuardrailViolationError("ActionPlanAgent出力フォーマット不正: timeframeまたはKPIを確認してください。")
        return chunk

# ActionPlanAgent専用ガードレールインスタンス
action_guardrail = ActionGuardrail() 