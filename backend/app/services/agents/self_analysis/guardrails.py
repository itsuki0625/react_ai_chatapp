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

class ImpactGuardrail(SelfAnalysisGuardrail):
    """
    ImpactAgent専用ガードレール: confidenceとdomainの検証を行います。
    """
    async def check_output(self, response_chunk, agent_name=None, session_id=None, user_id=None):
        # 基底のチェックを実行
        chunk = await super().check_output(response_chunk, agent_name, session_id, user_id)
        data = chunk.get("data", {}) or {}
        content = data.get("content", "")
        try:
            parsed = json.loads(content)
            impacts = parsed.get("chat", {}).get("impacts", [])
            for imp in impacts:
                conf = imp.get("confidence")
                if not isinstance(conf, (int, float)) or not 0 <= conf <= 1:
                    raise ValueError("confidence範囲外")
                domain = imp.get("domain")
                if domain not in ["social","economic","environmental","personal","organizational"]:
                    raise ValueError("domain不正")
        except Exception:
            raise GuardrailViolationError("ImpactAgent出力フォーマット不正: confidenceまたはdomainを確認してください。")
        return chunk

# ImpactAgent専用ガードレールインスタンス
impact_guardrail = ImpactGuardrail()

class UnivGuardrail(SelfAnalysisGuardrail):
    """
    UniversityMapperAgent専用ガードレール: universities件数とfit範囲の検証を行います。
    """
    async def check_output(self, response_chunk, agent_name=None, session_id=None, user_id=None):
        # 基底のチェックを実行
        chunk = await super().check_output(response_chunk, agent_name, session_id, user_id)
        data = chunk.get("data", {}) or {}
        content = data.get("content", "")
        try:
            parsed = json.loads(content)
            unis = parsed.get("chat", {}).get("universities", [])
            # 大学件数の検証
            if not 3 <= len(unis) <= 5:
                raise ValueError("大学件数NG: 3～5件必要です。")
            # fitの範囲チェック
            for u in unis:
                fit = u.get("fit")
                if not isinstance(fit, (int, float)) or not 0 <= fit <= 1:
                    raise ValueError("fit範囲外")
        except Exception:
            raise GuardrailViolationError("UniversityMapperAgent出力フォーマット不正: universities件数またはfitを確認してください。")
        return chunk

# UniversityMapperAgent専用ガードレールインスタンス
univ_guardrail = UnivGuardrail()

class VisionGuardrail(SelfAnalysisGuardrail):
    """
    VisionAgent専用ガードレール: vision文字数、末尾、uniq_score検証を行います。
    """
    async def check_output(self, response_chunk, agent_name=None, session_id=None, user_id=None):
        # 基底のチェックを実行
        chunk = await super().check_output(response_chunk, agent_name, session_id, user_id)
        data = chunk.get("data", {}) or {}
        content = data.get("content", "")
        try:
            parsed = json.loads(content)
            chat = parsed.get("chat", {})
            v = chat.get("vision", "")
            # 30字以内チェック
            if len(v) > 30:
                raise ValueError("30字超過")
            # 末尾チェック
            if not v.endswith(("する", "なる")):
                raise ValueError("語尾NG")
            # uniq_scoreチェック
            uniq = chat.get("uniq_score", 0)
            if not isinstance(uniq, (int, float)) or uniq > 0.6:
                raise ValueError("独自性低")
        except Exception:
            raise GuardrailViolationError(
                "VisionAgent出力フォーマット不正: visionやuniq_scoreを確認してください。"
            )
        return chunk

# VisionAgent専用ガードレールインスタンス
vision_guardrail = VisionGuardrail()

class ReflectGuardrail(SelfAnalysisGuardrail):
    """
    ReflectAgent専用ガードレール: summary長さとinsights数を検証します。
    """
    async def check_output(self, response_chunk, agent_name=None, session_id=None, user_id=None):
        # 基底チェック
        chunk = await super().check_output(response_chunk, agent_name, session_id, user_id)
        data = chunk.get("data", {}) or {}
        content = data.get("content", "")
        try:
            parsed = json.loads(content)
            chat = parsed.get("chat", {})
            insights = chat.get("insights", [])
            summary = chat.get("summary", "")
            # insights数チェック
            if len(insights) < 3:
                raise ValueError("insights 少な過ぎ")
            # summary長さチェック
            if len(summary) > 140:
                raise ValueError("summary 長過ぎ")
        except Exception:
            raise GuardrailViolationError(
                "ReflectAgent出力フォーマット不正: insights数またはsummary長さを確認してください。"
            )
        return chunk

# ReflectAgent専用ガードレールインスタンス
reflect_guardrail = ReflectGuardrail()

class ReflexionGuardrail(SelfAnalysisGuardrail):
    """
    PostSessionReflexionAgent専用ガードレール: macro_summary長さとinsight_matrixスコア範囲を検証します。
    """
    async def check_output(self, response_chunk, agent_name=None, session_id=None, user_id=None):
        # 基底チェック
        chunk = await super().check_output(response_chunk, agent_name, session_id, user_id)
        data = chunk.get("data", {}) or {}
        content = data.get("content", "")
        try:
            parsed = json.loads(content)
            chat = parsed.get("chat", {})
            # macro_summary長さチェック
            macro_summary = chat.get("macro_summary", "")
            if len(macro_summary) > 200:
                raise ValueError("summary>200字")
            # insight_matrixスコア範囲チェック
            for item in chat.get("insight_matrix", []):
                score = item.get("score")
                if not isinstance(score, (int, float)) or not 1 <= score <= 5:
                    raise ValueError("score範囲外")
        except Exception:
            raise GuardrailViolationError(
                "PostSessionReflexionAgent出力フォーマット不正: summaryまたはscoreを確認してください。"
            )
        return chunk

# PostSessionReflexionAgent専用ガードレールインスタンス
reflexion_guardrail = ReflexionGuardrail() 