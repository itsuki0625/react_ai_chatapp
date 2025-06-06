import os
import logging
from pathlib import Path
import uuid
from typing import Optional

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
            model="gpt-4o",
            tools=tools_to_use,  # allow subclass tools
            llm_adapter=openai_adapter,
            guardrail=guardrail_to_use,
            context_manager=ctx_mgr,
            resource_manager=rm,
            trace_logger=trace,
            planning_engine=PlanningEngine(
                llm_adapter=openai_adapter,
                model="gpt-4o"
            ),
            **kwargs,
        )

    async def run_with_plan(self, messages: list, session_id: str | None = None, **kwargs) -> dict:
        """
        PlanningEngineを使用してプランを作成し、サブタスクを実行します。
        README.mdで言及されている run_with_plan() に相当します。
        """
        print(f"INSIDE BaseSelfAnalysisAgent.run_with_plan: messages = {messages}")
        print(f"INSIDE BaseSelfAnalysisAgent.run_with_plan: session_id = {session_id}")
        # ★デバッグプリント追加
        print(f"DEBUG PRINT in BaseSelfAnalysisAgent.run_with_plan: messages ARG = {messages}")
        print(f"DEBUG PRINT in BaseSelfAnalysisAgent.run_with_plan: session_id ARG = {session_id}")

        if not self.planning_engine:
            # monono_agent SDK の PlanningEngine は __init__ で必須で渡される想定
            # ここに来る場合は初期化ミスや、意図しない変更があった可能性
            logging.error(f"[{self.name}] PlanningEngine not configured. This should not happen if BaseSelfAnalysisAgent is initialized correctly.")
            raise RuntimeError(f"PlanningEngine not configured for agent '{self.name}'. Cannot run_with_plan.")

        if self.trace_logger:
            # 正しい session_id と messages_preview をログに出力
            log_session_id = str(session_id) if session_id else "N/A"
            log_messages_preview = []
            if isinstance(messages, list):
                # messages の各要素が辞書であることを確認し、contentキーが存在すればその値を使う
                for msg_item in messages[:2]: # 最初の2メッセージをプレビュー
                    if isinstance(msg_item, dict):
                        log_messages_preview.append({
                            "role": msg_item.get("role", "unknown"),
                            "content_preview": str(msg_item.get("content"))[:50] + ("..." if len(str(msg_item.get("content", ""))) > 50 else "")
                        })
                    else:
                        # messages の要素が辞書でないという予期せぬケース
                        log_messages_preview.append({"error": "Invalid message item format", "item_preview": str(msg_item)[:50]})
            elif isinstance(messages, str): # messagesが文字列の場合のフォールバック
                log_messages_preview = [{"role": "user", "content_preview": messages[:50] + ("..." if len(messages) > 50 else messages)}]
            else: # その他の予期しない型の場合
                log_messages_preview = [{"error": "Unknown messages type", "type": str(type(messages))}]

            self.trace_logger.trace(
                "run_with_plan_start",
                {
                    "agent": self.name,
                    "session_id": log_session_id, # 正しいセッションID
                    "messages_preview": log_messages_preview # 正しいメッセージプレビュー
                }
            )

        print(f"[{self.name}] run_with_plan called. Session: {session_id}. Messages count: {len(messages) if isinstance(messages, list) else 'N/A'}")

        plan_session_id_for_engine: Optional[uuid.UUID] = None
        if session_id:
            try:
                plan_session_id_for_engine = uuid.UUID(session_id)
            except ValueError:
                logging.warning(f"[{self.name}] run_with_plan received session_id='{session_id}' which is not a valid UUID for PlanningEngine. Passing None.")
                plan_session_id_for_engine = None # UUID形式でなければNone

        if not isinstance(messages, list) or not all(isinstance(m, dict) and "role" in m and "content" in m for m in messages):
            logging.error(f"[{self.name}] run_with_plan expects 'messages' to be List[Dict[str, str]] with 'role' and 'content' keys, but got non-compliant structure. Aborting plan creation.")
            # Orchestratorで形式を整えているはずだが、念のためチェック
            # ここでエラーを発生させるか、フォールバックするかは設計による
            # 例えば、空のプランやエラーを示す結果を返すなど
            # 今回は、plan_obj が後続で使われるため、エラーにせず警告に留め、空のタスクで進行試行 (PlanningEngine側で空応答になる想定)
            # しかし、より安全なのはここで例外を発生させることかもしれない
            # raise ValueError(f"Invalid messages format for run_with_plan: {messages}")
            # とりあえず、空のメッセージリストとしてエンジンに渡す試み (エンジン側で処理される)
            processed_messages = [] 
            logging.warning(f"[{self.name}] Proceeding with empty messages for PlanningEngine due to invalid input format.")
        else:
            processed_messages = messages

        plan_obj = await self.planning_engine.create_plan(processed_messages, plan_session_id_for_engine)
        
        # D: プランが作成できなかった場合は従来のrunで応答を返す
        if not getattr(plan_obj, 'tasks', None):
            logging.warning(f"[{self.name}] PlanningEngine returned no tasks, falling back to direct run.")
            original_engine = self.planning_engine
            self.planning_engine = None
            try:
                fallback_result = await super().run(messages, session_id=session_id, **kwargs)
            finally:
                self.planning_engine = original_engine
            return fallback_result
        
        subtask_results = []
        # plan_obj.tasks が存在し、リストであることを確認
        if hasattr(plan_obj, 'tasks') and isinstance(plan_obj.tasks, list):
            for sub_task_definition in plan_obj.tasks:
                # sub_task_definition の型が PlanningEngine.execute_sub_task の期待する型と一致するか確認
                # (例: SubTaskクラスのインスタンスなど)
                try:
                    res = await self.planning_engine.execute_sub_task(sub_task_definition, self, session_id)
                    subtask_id = getattr(sub_task_definition, 'id', f"subtask_{len(subtask_results)}_{messages[0].get('content', '')[:10]}") # IDがなければ簡易生成
                    subtask_results.append({"id": subtask_id, "result": res})
                except Exception as e:
                    logging.error(f"[{self.name}] Error executing sub_task {getattr(sub_task_definition, 'id', 'N/A')}: {e}", exc_info=True)
                    subtask_results.append({"id": getattr(sub_task_definition, 'id', 'N/A'), "result": {"error": str(e), "type": type(e).__name__}, "status": "failed"})

        # plan_obj の dict 化 (pydantic model なら .model_dump() or .dict())
        if hasattr(plan_obj, 'model_dump'):
            plan_dict = plan_obj.model_dump()
        elif hasattr(plan_obj, 'dict'):
            plan_dict = plan_obj.dict()
        elif hasattr(plan_obj, '__dict__'): # dataclassなど
            plan_dict = vars(plan_obj)
        else:
            plan_dict = str(plan_obj) # フォールバック
        
        final_notes_content = None
        user_visible_content = None
        raw_content_for_orchestrator = ""

        if subtask_results:
            last_subtask_result = subtask_results[-1].get("result")
            if isinstance(last_subtask_result, dict):
                if "chat" in last_subtask_result: #主に使われるfinal_notesの形式
                    final_notes_content = last_subtask_result["chat"]
                elif "content" in last_subtask_result and isinstance(last_subtask_result["content"], (dict, list, str)):
                     # サブタスクのcontentが構造化データや文字列の場合
                    final_notes_content = last_subtask_result["content"]
                
                if "question" in last_subtask_result: # user_visible の主要な源泉
                    user_visible_content = last_subtask_result["question"]
                elif "user_visible" in last_subtask_result: # サブタスクが明示的に指定
                     user_visible_content = last_subtask_result["user_visible"]
                elif isinstance(final_notes_content, str): # final_notes が文字列ならそれを user_visible にも
                    user_visible_content = final_notes_content
                
                # オーケストレータのフォールバック用 content
                if isinstance(last_subtask_result.get("content"), str):
                    raw_content_for_orchestrator = last_subtask_result.get("content", "")

        # D2: user_visible_contentが空の場合もフォールバック
        if not user_visible_content or (isinstance(user_visible_content, str) and not user_visible_content.strip()):
            logging.warning(f"[{self.name}] No user_visible content from subtasks, falling back to direct run.")
            original_engine = self.planning_engine
            self.planning_engine = None
            try:
                return await super().run(messages, session_id=session_id, **kwargs)
            finally:
                self.planning_engine = original_engine

        final_result = {
            "role": "assistant", 
            "content": raw_content_for_orchestrator, # オーケストレータのフォールバック用
            "plan": plan_dict, 
            "subtasks": subtask_results,
            "final_notes": final_notes_content, # オーケストレータが note_store に保存する用
            "user_visible": user_visible_content # オーケストレータがユーザーに直接返す用
        }

        if hasattr(self, 'NEXT_STEP'):
            final_result['next_step'] = self.NEXT_STEP
        else:
            # NEXT_STEP が定義されていない場合、現在のステップを維持するか、エラーとするか。
            # オーケストレータ側で現在のステップをデフォルト値として使うので、ここでは何もしなくても良い。
            logging.warning(f"[{self.name}] NEXT_STEP attribute is not defined for this agent.")
            # final_result['next_step'] = self.name # 自分自身を返すか、あるいはオーケストレータに任せる

        if self.trace_logger:
            # resultが大きすぎる場合があるので主要なキーのみ、または文字列長制限してログ
            result_preview = {
                "role": final_result["role"],
                "plan_type": type(plan_obj).__name__,
                "num_subtasks": len(subtask_results),
                "next_step": final_result.get("next_step"),
                "has_final_notes": final_notes_content is not None,
                "has_user_visible": user_visible_content is not None
            }
            self.trace_logger.trace("run_with_plan_end", {"agent": self.name, "result_preview": result_preview})
            
        return final_result 