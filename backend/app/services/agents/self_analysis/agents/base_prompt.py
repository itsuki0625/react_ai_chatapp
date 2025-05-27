import os
import logging
from pathlib import Path

from app.services.agents.monono_agent.base_agent import BaseAgent
from app.services.agents.monono_agent.llm_adapters.openai_adapter import OpenAIAdapter
from app.services.agents.monono_agent.components.guardrail import BaseGuardrail
from app.services.agents.monono_agent.components.trace_logger import TraceLogger
from app.services.agents.monono_agent.components.planning_engine import PlanningEngine
from ..adapters import openai_adapter
from ..guardrails import SelfAnalysisGuardrail
from ..context_resources import ctx_mgr, rm, trace


def load_md(relative_path: str) -> str:
    """
    markdown テンプレートを読み込むユーティリティ。
    """
    base_dir = Path(__file__).parent.parent  # self_analysis ディレクトリ
    md_path = base_dir / relative_path
    return md_path.read_text(encoding="utf-8")


def default_openai_adapter() -> OpenAIAdapter:
    """
    OpenAIAdapter をデフォルト設定で作成する。
    """
    api_key = os.getenv("OPENAI_API_KEY")
    return OpenAIAdapter(model_name="gpt-4o-mini", api_key=api_key)


def default_guardrail() -> BaseGuardrail:
    """
    守衛レール(ガードレール)をデフォルト設定で作成する。
    """
    config = {
        "max_plan_tokens": 120,
        "max_iterations": 3,
        "blocked_output_regex": [r"(?i)pii", r"\d{4}-\d{4}-\d{4}-\d{4}"],
    }
    return BaseGuardrail(config)


def default_trace() -> TraceLogger:
    """
    TraceLogger を自己分析用ロガー設定で作成する。
    """
    logger = logging.getLogger("self_analysis_trace")
    return TraceLogger(logger=logger)


class BaseSelfAnalysisAgent(BaseAgent):
    """
    自己分析フロー(Plan→ReAct→Reflexion)を共通化するベースエージェント。
    """
    prompt_tmpl = load_md("prompts/base_prompt.md")

    def __init__(self, *, step_id: str, step_goal: str, **kwargs):
        # Allow subclasses to override instructions without duplication
        custom_instructions = kwargs.pop("instructions", None)
        if custom_instructions is not None:
            full_instructions = custom_instructions
        else:
            # 日本語で敬語かつフレンドリーな口調で回答し、一度の返答につき質問は必ず1つだけ含めるようにしてください。
            tone_prefix = "日本語で、敬語かつフレンドリーな口調で回答してください。また、一度の返答につき質問は必ず1つだけ含めるようにしてください。\n"
            prompt = self.prompt_tmpl.replace("{step_id}", step_id).replace("{step_goal}", step_goal)
            full_instructions = tone_prefix + prompt

        # Pop subclass-provided guardrail to avoid passing duplicate
        custom_guardrail = kwargs.pop("guardrail", None)
        guardrail_to_use = custom_guardrail if custom_guardrail is not None else SelfAnalysisGuardrail()

        # Pop subclass-provided tools to avoid passing duplicate
        custom_tools = kwargs.pop("tools", None)
        tools_to_use = custom_tools if custom_tools is not None else []
        super().__init__(
            name=step_id.title(),
            instructions=full_instructions,
            model="gpt-4o-mini",
            tools=tools_to_use,  # allow subclass tools
            llm_adapter=openai_adapter,
            guardrail=guardrail_to_use,
            context_manager=ctx_mgr,
            resource_manager=rm,
            trace_logger=trace,
            planning_engine=PlanningEngine(llm_adapter=openai_adapter),
            **kwargs,
        ) 