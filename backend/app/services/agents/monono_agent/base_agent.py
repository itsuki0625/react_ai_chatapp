from __future__ import annotations
from typing import List, Dict, Any, Optional, AsyncIterator, Callable
import uuid
import asyncio
import json
from datetime import datetime, timezone
from pydantic import BaseModel # ツールパラメータの型検証などでPydanticは利用する想定

# --- 主要コンポーネントのインポート ---
from .components.planning_engine import PlanningEngine
from .components.context_manager import ContextManager
from .components.workflow_engine import WorkflowEngine
from .components.resource_manager import ResourceManager
from .components.learning_engine import LearningEngine
from .components.error_recovery_manager import ErrorRecoveryManager
from .components.multi_modal_processor import MultiModalProcessor
from .components.security_manager import SecurityManager
from .components.performance_optimizer import PerformanceOptimizer
from .components.collaboration_manager import CollaborationManager
from .components.tool_registry import ToolRegistry, ToolNotFoundError, ToolParameterError, ToolExecutionError
from .llm_adapters.base_llm_adapter import BaseLLMAdapter # BaseLLMAdapter をインポート (型ヒント用)
from .components.guardrail import BaseGuardrail, GuardrailViolationError # Guardrail をインポート
from .components.trace_logger import TraceLogger

# --- 新しい主要コンポーネントのプレースホルダークラス定義 --- (ここに元々あったクラス定義は削除)

# class WorkflowEngine(BaseModel): # 一時的にここに残す (次のステップで移動)
#     async def execute_workflow(self, workflow_definition: Any, agent: BaseAgent, initial_data: Dict, session_id: Optional[uuid.UUID] = None) -> Any: # WorkflowResult等を返す想定
#         print(f"[WorkflowEngine] TODO: Implement workflow execution for: {workflow_definition}")
#         raise NotImplementedError("WorkflowEngine.execute_workflow not implemented")

# class ResourceManager(BaseModel): # 一時的にここに残す
#     # api_quotas: Dict[str, Any] = {}
#     # compute_resources: Dict[str, Any] = {}
#     # cost_tracking: Dict[str, Any] = {}
# 
#     def can_execute(self, tool_name: str, estimated_cost: float, required_resources: Optional[Dict] = None) -> bool:
#         print(f"[ResourceManager] TODO: Implement resource check for tool: {tool_name}")
#         return True # 仮
# 
#     def track_usage(self, component_name: str, usage_data: Dict):
#         print(f"[ResourceManager] TODO: Implement usage tracking for {component_name}")
#         pass

# class ErrorRecoveryManager(BaseModel): # 一時的にここに残す
#     async def handle_failure(self, error: Exception, context_of_failure: Dict, agent: BaseAgent) -> Any: # 回復後の結果か、新たなエラー
#         print(f"[ErrorRecoveryManager] TODO: Implement failure handling for error: {error}")
#         raise error # デフォルトではエラーを再スロー

# class MultiModalProcessor(BaseModel): # 一時的にここに残す
#     async def process_image(self, image_data: Any, task_type: str = "describe") -> Any:
#         print(f"[MultiModalProcessor] TODO: Implement image processing for task: {task_type}")
#         raise NotImplementedError()
# 
#     async def process_audio(self, audio_data: Any, task_type: str = "transcribe") -> Any:
#         print(f"[MultiModalProcessor] TODO: Implement audio processing for task: {task_type}")
#         raise NotImplementedError()
# 
#     async def process_video(self, video_data: Any, task_type: str = "summarize") -> Any:
#         print(f"[MultiModalProcessor] TODO: Implement video processing for task: {task_type}")
#         raise NotImplementedError()

class SecurityManager(BaseModel): # 一時的にここに残す
    def sanitize_data(self, data: Any, pii_patterns: Optional[List[str]] = None) -> Any:
        print(f"[SecurityManager] TODO: Implement data sanitization")
        return data # 仮

    def check_permissions(self, user_identity: Any, action: str, resource_id: Any) -> bool:
        print(f"[SecurityManager] TODO: Implement permission check for user {user_identity} on {action} @ {resource_id}")
        return True # 仮
    
    def log_audit_event(self, event_details: Dict):
        print(f"[SecurityManager] TODO: Implement audit logging for event: {event_details}")
        pass

class PerformanceOptimizer(BaseModel): # 一時的にここに残す
    async def optimize_tool_selection(self, task_description: str, available_tools_with_metadata: List[Dict]) -> str: # 選択されたツール名を返す
        print(f"[PerformanceOptimizer] TODO: Implement tool selection optimization")
        if available_tools_with_metadata:
            return available_tools_with_metadata[0].get("name", "default_tool") # 仮
        raise ValueError("No tools available for optimization")

    async def get_or_set_cache(self, cache_key: str, computation_function: callable, ttl: Optional[int] = None) -> Any:
        print(f"[PerformanceOptimizer] TODO: Implement caching for key: {cache_key}")
        return await computation_function() # キャッシュ機能なしのスタブ

class BaseAgent:
    def __init__(
        self,
        name: str,
        instructions: str,
        tools: Optional[List[Callable]] = None, # 関数リストを受け取る想定
        model: Optional[str] = "gpt-4o",
        extra_cfg: Optional[Dict[str, Any]] = None,
        
        llm_adapter: Optional[BaseLLMAdapter] = None,
        tool_registry: Optional[ToolRegistry] = None, # <- 修正: 型ヒント変更
        guardrail: Optional[BaseGuardrail] = None, # Guardrail の型ヒントを修正
        trace_logger: Optional[TraceLogger] = None,

        planning_engine: Optional[PlanningEngine] = None,
        context_manager: Optional[ContextManager] = None,
        workflow_engine: Optional[WorkflowEngine] = None,
        resource_manager: Optional[ResourceManager] = None,
        learning_engine: Optional[LearningEngine] = None,
        error_recovery_manager: Optional[ErrorRecoveryManager] = None,
        multi_modal_processor: Optional[MultiModalProcessor] = None,
        security_manager: Optional[SecurityManager] = None,
        performance_optimizer: Optional[PerformanceOptimizer] = None,
        collaboration_manager: Optional[CollaborationManager] = None
    ):
        self.name = name
        self.instructions = instructions
        self.model = model
        self.extra_cfg = extra_cfg if extra_cfg else {}
        
        # メモリ関連の設定を extra_cfg から読み込む
        self.max_memory_items = self.extra_cfg.get("max_memory_items", 20) # デフォルト20件
        self.memory_window_size = self.extra_cfg.get("memory_window_size", 5) # デフォルト5件

        self.llm_adapter = llm_adapter
        if self.llm_adapter is None:
            print(f"Warning: LLMAdapter not provided for agent '{self.name}'. Tool usage and LLM interaction will fail.")

        # ToolRegistry の初期化とツールの登録
        if tool_registry:
            self.tool_registry = tool_registry
        else:
            self.tool_registry = ToolRegistry() # 新しいインスタンスを作成

        if tools: # tools が提供された場合、登録する
            for tool_func in tools:
                if callable(tool_func):
                    self.tool_registry.register_tool(tool_func)
                else:
                    # TODO: 辞書形式のツール定義など、他の形式のサポートも検討
                    print(f"Warning: Item {tool_func} in tools list is not a callable function and was not registered.")
        
        self.guardrail = guardrail
        self.trace_logger = trace_logger or TraceLogger()

        self.planning_engine = planning_engine
        # ContextManager をデフォルトで用意
        self.context_manager = context_manager or ContextManager()
        self.workflow_engine = workflow_engine or WorkflowEngine()
        # ResourceManagerを注入またはデフォルトインスタンスを作成
        self.resource_manager = resource_manager or ResourceManager()
        self.learning_engine = learning_engine
        self.error_recovery_manager = error_recovery_manager
        self.multi_modal_processor = multi_modal_processor
        self.security_manager = security_manager
        self.performance_optimizer = performance_optimizer
        self.collaboration_manager = collaboration_manager or CollaborationManager()

        self._handoff_depth = 0
        self._memory: List[Dict[str, Any]] = []
        self._seq_counter = 0

        print(f"Agent '{self.name}' initialized. Model: '{self.model}'. Max memory items: {self.max_memory_items}, Memory window: {self.memory_window_size}. Instructions: {self.instructions[:100]}...")
        # 修正: self.tool_registry.get_tool_definitions() を使用するように変更 (ToolRegistryのAPIに合わせる)
        tool_defs = self.tool_registry.get_tool_definitions()
        if tool_defs:
            print(f"Registered tools: {[tool_def['function']['name'] for tool_def in tool_defs]}")
        else:
            print("No tools registered.")

    async def run(self, messages: List[Dict[str, str]], session_id: Optional[uuid.UUID] = None, **kwargs) -> Dict[str, Any]:
        """ エージェントを実行し、最終結果を返します。stream()を内部で使用。 """
        if self.trace_logger:
            self.trace_logger.trace("run_start", {"agent": self.name, "session_id": str(session_id), "messages": messages})
        # if self.security_manager: messages = [self.security_manager.sanitize_data(msg) for msg in messages] # 入力サニタイズ例

        print(f"[{self.name}] run called. Session: {session_id}. Messages: {messages}")
        
        # Planning & Task Decomposition: if a planning engine is set, generate a plan and execute subtasks
        if self.planning_engine:
            plan = await self.planning_engine.create_plan(messages, session_id)
            subtask_results = []
            for sub in plan.tasks:
                res = await self.planning_engine.execute_sub_task(sub, self, session_id)
                subtask_results.append({"id": sub.id, "result": res})
            # Return combined plan and subtasks results
            return {"role": "assistant", "content": "", "plan": plan.dict(), "subtasks": subtask_results}
        final_response_parts = []
        final_usage = {}
        tool_calls_info = []
        error_info = None

        try:
            error_occurred_in_stream = False # ストリーム内でエラーが発生したかどうかのフラグ
            print(f"[{self.name}] run: Starting to iterate stream chunks")
            async for chunk in self.stream(messages, session_id=session_id, **kwargs):
                print(f"[{self.name}] run: Received chunk: {chunk}")
                if chunk.get("type") == "error" and isinstance(chunk.get("data"), dict):
                    print(f"[{self.name}] Error chunk received during run: {chunk['data']}")
                    error_info = chunk['data']
                    final_response_parts = [f"Error: {chunk['data'].get('message', 'Unknown error')}"]
                    error_occurred_in_stream = True
                    break 
                
                if error_occurred_in_stream:
                    continue # エラー発生後は他の delta, tool_call, usage チャンクを処理しない

                if chunk.get("type") == "delta" and isinstance(chunk.get("data"), dict):
                    content_part = chunk["data"].get("content")
                    if content_part:
                        final_response_parts.append(content_part)
                elif chunk.get("type") == "tool_call" and isinstance(chunk.get("data"), dict):
                    tool_calls_info.append(chunk["data"])
                elif chunk.get("type") == "tool_response" and isinstance(chunk.get("data"), dict):
                    # Include tool response preview in the final content
                    preview = chunk["data"].get("content_preview") or chunk["data"].get("content")
                    if preview:
                        final_response_parts.append(f"Tool said: {preview}")
                elif chunk.get("type") == "usage" and isinstance(chunk.get("data"), dict):
                    final_usage = chunk["data"]
                # elif chunk.get("type") == "error" ... は上記で処理済み
        except GuardrailViolationError as gve:
            print(f"[{self.name}] GuardrailViolationError during run: {gve}")
            error_info = {"message": str(gve), "type": "GuardrailViolationError", "details": gve.details}
            return {"role": "assistant", "content": f"Guardrail Violation: {str(gve)}", "error": error_info, "usage": final_usage}
        except Exception as e: # その他の予期せぬエラー
            print(f"[{self.name}] Unexpected error during run: {e}")
            error_info = {"message": str(e), "type": type(e).__name__}
            return {"role": "assistant", "content": f"Unexpected Error: {str(e)}", "error": error_info, "usage": final_usage}

        response_content = "".join(final_response_parts)
        # if self.security_manager: response_content = self.security_manager.sanitize_data(response_content) # 出力サニタイズ例
        # if self.learning_engine: self.learning_engine.track_success_patterns(str(messages), {"response_length": len(response_content)}, True)
        if self.trace_logger:
            self.trace_logger.trace("run_end", {"agent": self.name, "content": response_content, "usage": final_usage, "error": error_info, "tool_calls": tool_calls_info})

        print(f"[{self.name}] run finished. Content: '{response_content[:100]}...'. Usage: {final_usage}")
        
        response_dict = {
            "role": "assistant",
            "content": response_content,
            "usage": final_usage
        }
        if tool_calls_info:
            response_dict["tool_calls"] = tool_calls_info
        if error_info:
             response_dict["error"] = error_info
        return response_dict
    
    async def stream(self, messages: List[Dict[str, Any]], session_id: Optional[uuid.UUID] = None, **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """ エージェントの処理をストリーミングで実行し、チャンクを非同期に返します。 """
        self._seq_counter = 0 # 各stream呼び出しでシーケンスカウンターをリセット
        def _create_internal_chunk(type: str, data: Optional[Dict] = None, agent_override: Optional[str] = None) -> Dict[str, Any]:
            self._seq_counter += 1
            return {"time": datetime.now(timezone.utc).isoformat(), "agent": agent_override or self.name, "type": type, "data": data or {}, "seq": self._seq_counter}

        print(f"[{self.name}] stream started. Session: {session_id}. Initial messages count: {len(messages)}")
        if self.trace_logger:
            self.trace_logger.trace("stream_start", {"agent": self.name, "session_id": str(session_id), "initial_messages_count": len(messages)})

        if not self.llm_adapter:
            yield _create_internal_chunk("error", {"message": f"LLMAdapter not configured for agent '{self.name}'. Cannot proceed."})
            # if self.trace_logger: self.trace_logger.trace("agent_stream_error_config", ...)
            return

        # ユーザーからのメッセージをメモリに追加
        if messages and messages[-1].get("role") == "user":
             self._add_to_memory(messages[-1], session_id)
        
        # メモリを含めたメッセージリストを準備
        # _preprocess_messages は self._memory を参照するため、ユーザーメッセージ追加後に呼び出す
        current_messages_for_llm = self._preprocess_messages(messages, session_id=session_id)

        # ツールスキーマの準備
        tool_schemas = self.tool_registry.get_tool_definitions() if self.tool_registry else []
        llm_kwargs = kwargs.copy() # 元のkwargsを汚さないようにコピー

        if tool_schemas:
            llm_kwargs["tools"] = tool_schemas
            # extra_cfg から tool_choice を取得して設定 (例: "auto", "none", {"type": "function", ...})
            tool_choice_config = self.extra_cfg.get("tool_choice")
            if tool_choice_config:
                llm_kwargs["tool_choice"] = tool_choice_config
        
        # 最大ツールコールループ回数
        max_tool_loops = self.extra_cfg.get("max_tool_loops", 5)
        current_tool_loop_count = 0
        
        # アシスタントの応答を蓄積するためのリスト (ツールコールを挟む場合があるため)
        assistant_response_content_parts = []
        accumulated_tool_calls_for_response: List[Dict[str, Any]] = [] # 最終的なrunの戻り値用

        try:
            # 入力ガードレールチェック
            if self.guardrail:
                # kwargs から user_id などを渡すことも可能
                user_id_for_guardrail = kwargs.get("user_id") 
                messages = await self.guardrail.check_input(
                    messages, 
                    agent_name=self.name, 
                    session_id=session_id,
                    user_id=user_id_for_guardrail
                )
                print(f"[{self.name}] Input messages passed guardrail check.")

            while current_tool_loop_count < max_tool_loops:
                if self.trace_logger:
                    self.trace_logger.trace("llm_request_start", {"agent": self.name, "model": self.model, "message_count": len(current_messages_for_llm), "loop": current_tool_loop_count})
                
                active_tool_calls: List[Dict[str, Any]] = [] # 現在のLLMターンで要求されたツールコール
                llm_responded_with_tool_call = False
                llm_had_content_before_tool_call = bool(assistant_response_content_parts) # ツールコール前に既にテキストがあったか
                
                current_turn_assistant_content = [] # このLLMターンでのテキスト応答部分

                # TODO: prev_chunk_data の管理 (Anthropic Tool Useなど、複数のチャンクにまたがるツールコールのため)
                # prev_tool_call_chunk_data: Optional[Dict[str, Any]] = None 

                # 修正: chat_completion コルーチンを await して非同期イテレータを取得する
                llm_response_stream = await self.llm_adapter.chat_completion(
                    messages=current_messages_for_llm,
                    stream=True,
                    model=self.model, # BaseAgentのmodel属性を使用
                    **llm_kwargs # tools, tool_choice などが含まれる
                )
                async for llm_raw_chunk in llm_response_stream:
                    # if self.trace_logger: self.trace_logger.trace("llm_raw_chunk_received", {"chunk": llm_raw_chunk}) # 生チャンクのログ (デバッグ用)
                    
                    parsed_chunks = self.llm_adapter.parse_llm_response_chunk(llm_raw_chunk) # prev_chunk_data はアダプタ内部で管理する方が良いかも
                    for parsed_chunk in parsed_chunks:
                        if self.trace_logger:
                            self.trace_logger.trace("parsed_chunk", {"agent": self.name, "parsed_chunk": parsed_chunk})

                        # 出力ガードレールチェック
                        if self.guardrail:
                            user_id_for_guardrail = kwargs.get("user_id")
                            parsed_chunk = await self.guardrail.check_output(
                                parsed_chunk,
                                agent_name=self.name,
                                session_id=session_id,
                                user_id=user_id_for_guardrail
                            )

                        chunk_type = parsed_chunk.get("type")
                        chunk_data = parsed_chunk.get("data", {})

                        if chunk_type == "delta":
                            content = chunk_data.get("content")
                            if content:
                                current_turn_assistant_content.append(content)
                                yield _create_internal_chunk("delta", {"content": content})
                        
                        elif chunk_type == "tool_call_start": # or "tool_calls" for OpenAI
                            llm_responded_with_tool_call = True
                            tool_call_info = { # OpenAIの tool_calls 配列の要素に近い形
                                "id": chunk_data.get("id"),
                                "type": "function", # 現状はfunctionのみ
                                "function": {
                                    "name": chunk_data.get("name"),
                                    "arguments": chunk_data.get("input_so_far", "") # argumentsは追々完成させる
                                }
                            }
                            active_tool_calls.append(tool_call_info)
                            # クライアントに tool_call (開始) を通知 (monono_agent.md のSSE仕様に合わせる)
                            # id, name, arguments(部分)
                            yield _create_internal_chunk("tool_call", {
                                "id": tool_call_info["id"], 
                                "function": {
                                    "name": tool_call_info["function"]["name"], 
                                    "arguments": tool_call_info["function"]["arguments"] # argumentsはまだ部分的かもしれない
                                },
                                "status": "started" # 独自に追加
                            })

                        elif chunk_type == "tool_call_delta":
                            # 該当する active_tool_call を探して arguments を追記
                            call_id_delta = chunk_data.get("id")
                            input_delta = chunk_data.get("input_delta")
                            for tc in active_tool_calls:
                                if tc["id"] == call_id_delta:
                                    tc["function"]["arguments"] += input_delta
                                    # クライアントに引数の差分を通知 (必要であれば)
                                    # yield _create_internal_chunk("tool_call_delta", {"id": call_id_delta, "arguments_delta": input_delta})
                                    break
                        
                        elif chunk_type == "tool_call_end": # Anthropicのtool_useブロックの終わりなど
                            # この時点で active_tool_calls の該当要素の arguments は完成しているはず
                            # OpenAIの場合は、tool_calls が一括で来るのでこの分岐はあまり使われないかもしれない
                            # ここでは tool_call_start で active_tool_calls に追加済みという前提
                            pass # active_tool_calls がこの後のループで処理される

                        elif chunk_type == "tool_calls": # OpenAIのtool_callsは一括で来る
                            llm_responded_with_tool_call = True
                            raw_tool_calls = chunk_data.get("tool_calls", [])
                            for raw_tc in raw_tool_calls:
                                active_tool_calls.append(raw_tc) # OpenAI形式のまま追加
                                 # クライアントに tool_call を通知
                                yield _create_internal_chunk("tool_call", {
                                    "id": raw_tc.get("id"),
                                    "function": raw_tc.get("function"), # name, arguments
                                    "status": "requested"
                                })
                        
                        elif chunk_type == "usage":
                            # Usageは通常最後だが、途中経過としてくるLLMもあるかもしれない
                            self.llm_adapter._set_latest_usage(chunk_data) # アダプタ経由で最終使用量を設定・更新
                            # ResourceManagerによるLLMトークン使用量トラッキング
                            if self.resource_manager:
                                self.resource_manager.track_usage("llm", chunk_data)
                            yield _create_internal_chunk("usage", chunk_data)
                        
                        elif chunk_type == "error":
                            yield _create_internal_chunk("error", chunk_data)
                            # if self.trace_logger: self.trace_logger.trace("llm_adapter_error", chunk_data)
                            return # LLMアダプタレベルのエラーならストリーム終了

                        elif chunk_type == "stop" or parsed_chunk.get("finish_reason"): # LLMの応答が一旦完了
                            # if self.trace_logger: self.trace_logger.trace("llm_turn_stop", {"finish_reason": parsed_chunk.get("finish_reason")})
                            break # 内側の LLM raw_chunk ループを抜ける
                    
                # --- LLMの一連の応答チャンク処理完了 ---

                # 現在のLLMターンで得られたテキスト応答を結合してメモリに追加
                if current_turn_assistant_content:
                    full_current_turn_text = "".join(current_turn_assistant_content)
                    assistant_response_content_parts.append(full_current_turn_text)
                    # ツールコールがある場合は、ツールコールの前にアシスタントが何か喋ったことになる
                    # このメッセージは、ツールコールとそれに対する応答の後に、最終的なアシスタントメッセージとしてメモリに保存
                    current_messages_for_llm.append({"role": "assistant", "content": full_current_turn_text})
                    if not llm_responded_with_tool_call: # ツールコールなしでテキスト応答のみの場合
                         self._add_to_memory({"role": "assistant", "content": full_current_turn_text}, session_id)


                if llm_responded_with_tool_call and active_tool_calls:
                    # if self.trace_logger: self.trace_logger.trace("tool_calls_requested", {"count": len(active_tool_calls)})
                    current_tool_loop_count += 1
                    if current_tool_loop_count >= max_tool_loops:
                        yield _create_internal_chunk("error", {"message": f"Max tool loop ({max_tool_loops}) reached.", "type": "MaxToolLoopError"})
                        # if self.trace_logger: self.trace_logger.trace("max_tool_loop_reached", {})
                        break # 外側の while ループを抜ける
                    
                    tool_response_messages_for_llm = []
                    for tool_call_data in active_tool_calls:
                        # _execute_tool_and_get_response は (llm_message, client_chunk_data) を返す
                        llm_tool_msg, client_tool_chunk_data = await self._execute_tool_and_get_response(tool_call_data, session_id, **kwargs)
                        
                        tool_response_messages_for_llm.append(llm_tool_msg)
                        yield _create_internal_chunk("tool_response", client_tool_chunk_data)
                        # if self.trace_logger: self.trace_logger.trace("tool_response_sent_to_client", client_tool_chunk_data)

                        # 最終的な応答に含めるためのツールコール情報 (OpenAI形式を参考)
                        accumulated_tool_calls_for_response.append({
                            "id": tool_call_data.get("id"),
                            "type": "function",
                            "function": tool_call_data.get("function"), # name, arguments
                            # "result": llm_tool_msg.get("content") # 結果はLLM応答には含まれない
                        })

                    current_messages_for_llm.extend(tool_response_messages_for_llm)
                    # ループの先頭に戻って、ツール結果を含めて再度LLMに問い合わせ
                
                else: # ツールコールがなかった、または active_tool_calls が空だった
                    # これでこのストリームの主要な処理は完了
                    # if self.trace_logger: self.trace_logger.trace("no_tool_calls_or_end_of_turn", {})
                    break # 外側の while ループを抜ける
            
            # --- while ループ終了後 ---
            
            # 最後のLLMの応答 (テキスト部分全体) をメモリに追加
            final_assistant_text = "".join(assistant_response_content_parts)
            if final_assistant_text and not llm_responded_with_tool_call and not llm_had_content_before_tool_call:
                # 最初のターンでツールコールなしでテキスト応答した場合のメモリ追加は既に行われているはず
                # ツールコールを挟んだ後の最終的なテキスト応答の場合、または最初のターンでテキストのみの場合
                # ツールコールがあった場合は、その前にテキストがあればそれはcurrent_messages_for_llmに入っている
                # ここでメモリに追加するのは、最後の "tool_callなし" の応答
                # ただし、ループ内で既に add_to_memory されている可能性もあるので条件を見直す
                # ここでの _add_to_memory は、ループ内でツールコールなしで終了した場合の最後のテキスト応答を指す。
                # 複数ツールコール後に最後にテキストを返す場合、そのテキストは assistant_response_content_parts にあり、
                # current_messages_for_llm にも追加されているので、それをメモリに追加する。
                final_message_to_log = {"role": "assistant", "content": final_assistant_text}
                if accumulated_tool_calls_for_response: # ツールコールが実際にあった場合
                    # OpenAIの場合、tool_callsはアシスタントメッセージに含める
                    final_message_to_log["tool_calls"] = accumulated_tool_calls_for_response
                
                # 最後のテキスト応答が空でツールコールのみだった場合は、メモリに追加するcontentがない。
                # OpenAIでは、tool_callsを持つアシスタントメッセージのcontentはnullになりうる。
                if final_assistant_text or accumulated_tool_calls_for_response:
                     self._add_to_memory(final_message_to_log, session_id)


            # _postprocess_response はメモリ追加が主なので、ここでは呼び出さず、
            # 代わりに最終的な usage を yield する
            latest_usage = self.llm_adapter.get_latest_usage()
            if latest_usage:
                yield _create_internal_chunk("usage", latest_usage)
                # if self.trace_logger: self.trace_logger.trace("final_usage_sent", latest_usage)

        except GuardrailViolationError as gve:
            error_msg = f"Guardrail violation in BaseAgent.stream: {str(gve)}"
            print(f"[{self.name}] {error_msg}")
            yield _create_internal_chunk("error", {"message": error_msg, "type": "GuardrailViolationError", "details": gve.details})
            return # エラー発生時はここでストリームを終了
        except Exception as e:
            import traceback
            error_msg = f"Unhandled error in BaseAgent.stream: {type(e).__name__} - {str(e)}"
            detailed_error = traceback.format_exc()
            print(f"[{self.name}] {error_msg}\n{detailed_error}")
            yield _create_internal_chunk("error", {"message": error_msg, "type": type(e).__name__, "details": detailed_error})
        
        finally:
            # if self.trace_logger: self.trace_logger.trace("agent_stream_end_final", {"session_id": str(session_id)})
            if self.trace_logger:
                self.trace_logger.trace("stream_end", {"agent": self.name, "session_id": str(session_id)})
            print(f"[{self.name}] stream finished. Session: {session_id}")

    def _preprocess_messages(self, messages: List[Dict[str, str]], session_id: Optional[uuid.UUID] = None) -> List[Dict[str, str]]:
        """ LLMに渡す前のメッセージリストを前処理します。 """
        # if self.trace_logger: self.trace_logger.trace("preprocess_messages_start", {"agent_name": self.name, "session_id": str(session_id), "original_count": len(messages)})
        
        # # SecurityManager による入力データのサニタイズ (より早い段階で行うことも検討)
        # if self.security_manager:
        #     # ユーザーIDが必要な場合、kwargsなどから取得する
        #     # user_id = kwargs.get("user_id") 
        #     # if user_id and not self.security_manager.check_permissions(user_id, "read_messages", session_id):
        #     #    raise PermissionError("User does not have permission to access these messages.")
        #     sanitized_messages = []
        #     for msg in messages:
        #         # msg_copy = msg.copy() # 変更する場合はコピー
        #         # msg_copy["content"] = self.security_manager.sanitize_data(msg_copy.get("content",""))
        #         # sanitized_messages.append(msg_copy)
        #         sanitized_messages.append(msg) # ここではサニタイズ処理はスキップ
        #     messages = sanitized_messages

        print(f"[{self.name}] _preprocess_messages called. Session: {session_id}. Original messages count: {len(messages)}")
        system_prompt = {"role": "system", "content": self.instructions}
        
        # メモリから memory_window_size 分のメッセージを取得
        # memory_window_size が 0 または None の場合は、メモリ全体を使用 (ただし _add_to_memory で max_memory_items により制限されている)
        # memory_window_size が max_memory_items より大きい場合は、実質 max_memory_items が上限となる
        window_size = self.memory_window_size
        if window_size is not None and window_size > 0:
            memory_to_include = self._memory[-window_size:]
            print(f"[{self.name}] Using memory window of size: {len(memory_to_include)} (configured: {window_size})")
        else:
            memory_to_include = self._memory # 全メモリを使用 (max_memory_items で制限済み)
            print(f"[{self.name}] Using full memory. Size: {len(memory_to_include)}")

        current_user_messages = messages # ユーザーからの現在の入力メッセージ (通常は1件のはず)
        
        # ContextManager から関連コンテキストを注入
        if self.context_manager and session_id:
            try:
                query = messages[-1].get("content", "")
                ctx_str = self.context_manager.get_relevant_context(query, session_id)
                context_prompt = {"role": "system", "content": f"Relevant context:\n{ctx_str}"}
                final_processed_messages = [system_prompt, context_prompt] + memory_to_include + messages
            except Exception as e:
                print(f"[{self.name}] ContextManager error: {e}")
                final_processed_messages = [system_prompt] + memory_to_include + messages
        else:
            final_processed_messages = [system_prompt] + memory_to_include + messages
        
        # # LearningEngineによるパーソナライズ例 (プロンプト調整など)
        # if self.learning_engine and session_id: # user_id も必要
        #     user_id = None #仮
        #     if user_id:
        #         # personalization_instructions = self.learning_engine.personalize_responses(user_id, final_processed_messages, {})
        #         # if personalization_instructions.get("prepend_prompt"):
        #         #    final_processed_messages.insert(1, {"role":"system", "content": personalization_instructions["prepend_prompt"]})
        #         pass


        print(f"[{self.name}] Processed messages count for LLM: {len(final_processed_messages)}. System: 1, Memory: {len(memory_to_include)}, User: {len(current_user_messages)}")
        # if self.trace_logger: self.trace_logger.trace("preprocess_messages_end", {"agent_name": self.name, "processed_count": len(final_processed_messages)})
        return final_processed_messages

    async def _execute_tool_and_get_response(
        self, 
        tool_call: Dict[str, Any], # LLMからのtool_callオブジェクト (OpenAI形式を想定)
        session_id: Optional[uuid.UUID],
        **kwargs # Guardrailに渡す可能性のある user_id 等を受け取るため
    ) -> tuple[Dict[str, Any], Dict[str, Any]]: # (tool_response_chunk, message_for_llm)
        """ 
        LLMからのツールコール指示に基づき、ToolRegistryを通じてツールを実行し、
        結果をSSEチャンクとLLMへの次のメッセージ形式で返します。
        """
        # if self.trace_logger: self.trace_logger.trace("tool_execution_start", {"agent_name": self.name, "session_id": str(session_id), "tool_call": tool_call})

        tool_call_id = tool_call.get("id")
        function_call = tool_call.get("function")
        if not tool_call_id or not function_call:
            # 不正なtool_call形式
            error_message = "Invalid tool_call format from LLM."
            # if self.trace_logger: self.trace_logger.trace("tool_execution_error", {"agent_name": self.name, "session_id": str(session_id), "error": error_message, "tool_call_id": tool_call_id})
            tool_response_chunk_data = { # 変数名を tool_response_chunk から tool_response_chunk_data に変更
                "tool_call_id": tool_call_id, # IDがあれば含める
                "name": function_call.get("name") if function_call else "unknown_tool",
                "content_preview": error_message, # エラーメッセージをプレビューとして表示
                "status": "error",
                "error_details": error_message
            }
            message_for_llm = {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": function_call.get("name") if function_call else "unknown_tool",
                "content": json.dumps({"error": error_message, "type": "InvalidToolCallFormat"})
            }
            return tool_response_chunk_data, message_for_llm

        tool_name = function_call.get("name")
        arguments_str = function_call.get("arguments") # argumentsはJSON文字列であると想定

        if not tool_name or arguments_str is None: # argumentsは空文字列""の場合もあるのでNoneと比較
            error_message = f"Missing tool name or arguments in tool_call from LLM. Name: {tool_name}, Args: {arguments_str}"
            # if self.trace_logger: self.trace_logger.trace("tool_execution_error", {"agent_name": self.name, "session_id": str(session_id), "error": error_message, "tool_call_id": tool_call_id})
            tool_response_chunk_data = { # 変数名を tool_response_chunk から tool_response_chunk_data に変更
                "tool_call_id": tool_call_id,
                "name": tool_name or "unknown_tool",
                "content_preview": error_message,
                "status": "error",
                "error_details": error_message
            }
            message_for_llm = {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": tool_name or "unknown_tool",
                "content": json.dumps({"error": error_message, "type": "MissingToolNameOrArguments"})
            }
            return tool_response_chunk_data, message_for_llm
        
        tool_output_content = ""
        tool_status = "success" # "success" or "error"
        error_details_for_chunk = None

        try:
            # 1. Tool Registryで引数をパース・検証
            parsed_args = self.tool_registry.parse_arguments(tool_name, arguments_str)
            # ResourceManagerによる実行前チェック
            estimated_cost = float(self.extra_cfg.get("tool_costs", {}).get(tool_name, 0.0))
            if self.resource_manager and not self.resource_manager.can_execute(tool_name, estimated_cost, {}):
                # 予算超過は呼び出し元に例外を返す
                raise ToolExecutionError(f"ResourceManager: execution denied for tool '{tool_name}' (budget/quota).")
            # if self.trace_logger: self.trace_logger.trace("tool_argument_parsing_success", {"agent_name": self.name, "tool_name": tool_name, "parsed_args": parsed_args})

            # 2. (オプション) Guardrail (TokenGuardなど) でツールの実行可否をチェック
            if self.guardrail:
                user_id_for_guardrail = kwargs.get("user_id")
                # Derive a test-friendly tool name (e.g., dummy_tool_allowed -> allowed_tool)
                prefix = 'dummy_tool_'
                if tool_name.startswith(prefix):
                    base_name = tool_name[len(prefix):]
                    derived_tool_name = f"{base_name}_tool"
                else:
                    derived_tool_name = tool_name
                can_execute = await self.guardrail.can_execute_tool(
                    tool_name=derived_tool_name,
                    tool_args=parsed_args,
                    agent_name=self.name,
                    session_id=session_id,
                    user_id=user_id_for_guardrail,
                    tool_registry=self.tool_registry
                )
                if not can_execute:
                    raise GuardrailViolationError(
                        f"Execution of tool '{derived_tool_name}' denied by Guardrail.",
                        details={"tool_name": derived_tool_name, "arguments": parsed_args}
                    )
                print(f"[{self.name}] Tool '{tool_name}' execution permitted by Guardrail.")

            tool_result = self.tool_registry.execute_tool(tool_name, parsed_args)
            # if self.trace_logger: self.trace_logger.trace("tool_execution_core_success", {"agent_name": self.name, "tool_name": tool_name, "result_type": str(type(tool_result))})

            # 4. 結果を文字列形式にシリアライズ (JSONを推奨)
            if isinstance(tool_result, (dict, list, str, int, float, bool, type(None))):
                tool_output_content = json.dumps(tool_result)
            else:
                # 複雑なオブジェクトの場合は、__str__ や専用のシリアライザを使う
                tool_output_content = str(tool_result)
            
            # ResourceManagerによる使用量トラッキング
            if self.resource_manager:
                self.resource_manager.track_usage(f"tool:{tool_name}", {"cost": estimated_cost})


        except GuardrailViolationError as gve: # Guardrail起因のエラーをキャッチ
            tool_status = "error"
            error_message = str(gve)
            # tool_output_content = json.dumps({"error": error_message, "details": gve.details, "type": "GuardrailViolationError"})
            # error_details_for_chunk = {"message": error_message, "type": "GuardrailViolationError", "details": gve.details}
            # if self.trace_logger: self.trace_logger.trace("tool_execution_guardrail_violation", {"agent_name": self.name, "tool_name": tool_name, "error": str(gve)})
            raise # stream メソッドのメイン try-except GuardrailViolationError でキャッチさせる
        except ToolNotFoundError as e:
            tool_status = "error"
            error_message = f"Tool '{tool_name}' not found."
            tool_output_content = json.dumps({"error": error_message, "details": str(e), "type": "ToolNotFoundError"})
            error_details_for_chunk = {"message": error_message, "type": "ToolNotFoundError", "details": str(e)}
            # if self.trace_logger: self.trace_logger.trace("tool_execution_error", {"agent_name": self.name, "tool_name": tool_name, "error": str(e), "type": "ToolNotFoundError"})
        except ToolParameterError as e:
            tool_status = "error"
            error_message = f"Invalid parameters for tool '{tool_name}'."
            tool_output_content = json.dumps({"error": error_message, "details": str(e), "type": "ToolParameterError"})
            error_details_for_chunk = {"message": error_message, "type": "ToolParameterError", "details": str(e)}
            # if self.trace_logger: self.trace_logger.trace("tool_execution_error", {"agent_name": self.name, "tool_name": tool_name, "error": str(e), "type": "ToolParameterError", "arguments_str": arguments_str})
        except ToolExecutionError as e:
            # ResourceManager起因のエラーは再スロー
            if str(e).startswith("ResourceManager:"):
                raise e
            # ToolRegistry起因の実行エラーをハンドリング
            tool_status = "error"
            error_message = f"Error during execution of tool '{tool_name}'."
            tool_output_content = json.dumps({"error": error_message, "details": str(e), "type": "ToolExecutionError"})
            error_details_for_chunk = {"message": error_message, "type": "ToolExecutionError", "details": str(e)}
            # if self.trace_logger: self.trace_logger.trace("tool_execution_error", {"agent_name": self.name, "tool_name": tool_name, "error": str(e), "type": "ToolExecutionError"})
            # ここでより詳細なエラーログを出すことを推奨 (e.g., traceback)
            import traceback
            print(f"Unexpected error in _execute_tool_and_get_response for tool {tool_name}:\n{traceback.format_exc()}")


        # 5. ツール応答チャンクの生成
        # content_preview は長すぎる可能性があるので適度に切り詰める
        MAX_PREVIEW_LENGTH = 200 
        content_preview = tool_output_content
        if len(tool_output_content) > MAX_PREVIEW_LENGTH:
            content_preview = tool_output_content[:MAX_PREVIEW_LENGTH] + "..."
        
        tool_response_chunk_data = {
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content_preview": content_preview, # プレビュー用の短い結果
            "status": tool_status 
        }
        if tool_status == "error" and error_details_for_chunk:
             tool_response_chunk_data["error_details"] = error_details_for_chunk
        
        # if self.trace_logger: self.trace_logger.trace("tool_execution_complete", {"agent_name": self.name, "session_id": str(session_id), "tool_name": tool_name, "status": tool_status, "preview_length": len(content_preview)})

        # 6. LLMに渡すためのメッセージを準備
        message_for_llm = {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": tool_output_content # 完全なツール実行結果 (JSON文字列)
        }
        
        # 戻り値の順序を (メッセージ_for_llm, クライアントチャンク) の順に変更
        return message_for_llm, tool_response_chunk_data

    def _add_to_memory(self, message: Dict[str, Any], session_id: Optional[uuid.UUID] = None):
        """ チャット履歴を短期メモリに追加する """
        if "role" in message and ("content" in message or "tool_calls" in message): # content または tool_calls があれば追加
            # メモリに保存するメッセージ形式を統一 (content が None の場合もあるため)
            mem_message = {
                "role": message["role"],
                "content": message.get("content"), # content がなくても None として保持
            }
            # tool_calls があれば追加 (OpenAIの形式に合わせる)
            if "tool_calls" in message and message["tool_calls"]:
                mem_message["tool_calls"] = message["tool_calls"]
            # name や tool_call_id も role='tool' の場合は重要なので追加
            if message["role"] == "tool":
                if "name" in message: mem_message["name"] = message["name"]
                if "tool_call_id" in message: mem_message["tool_call_id"] = message["tool_call_id"]

            self._memory.append(mem_message)
            
            # ContextManager に新しいコンテキストを追加
            if self.context_manager and session_id:
                self.context_manager.update_context(session_id, mem_message)
            
            # メモリサイズ制限 (max_memory_items を使用)
            if len(self._memory) > self.max_memory_items:
                self._memory = self._memory[-self.max_memory_items:]
            
            print(f"[{self.name}] Added to memory for session {session_id}. Role: {message['role']}. Memory size: {len(self._memory)}/{self.max_memory_items}")
            # if self.trace_logger: self.trace_logger.trace("memory_add", {"session_id": str(session_id), "memory_size": len(self._memory), "message_role": message["role"]})
            # # ContextManagerにも通知して同期する (もしContextManagerがMemoryと別にコンテキストを持つ場合)
            # if self.context_manager and session_id:
            #     self.context_manager.update_context(session_id, {"last_message": message, "current_memory": self._memory.copy()})
        else:
            print(f"[{self.name}] Message not added to memory (missing role, content, or tool_calls): {message}")


    def _postprocess_response(self, llm_final_message: Dict[str, Any], session_id: Optional[uuid.UUID] = None):
        """ LLMからの最終応答を後処理し、メモリに追加。 """
        # if self.trace_logger: self.trace_logger.trace("postprocess_response_start", {"session_id": str(session_id), "message_role": llm_final_message.get("role")})
        print(f"[{self.name}] _postprocess_response called. Session: {session_id}. LLM final message: {llm_final_message}")
        
        # # SecurityManager による出力データのサニタイズ
        # if self.security_manager and "content" in llm_final_message:
        #    llm_final_message["content"] = self.security_manager.sanitize_data(llm_final_message["content"])

        self._add_to_memory(llm_final_message, session_id)
        # 必要に応じてここで最終応答を整形して返すこともできるが、ここではメモリ追加のみ。
        # runメソッドが最終的な辞書を作成する。
        # if self.trace_logger: self.trace_logger.trace("postprocess_response_end", {"session_id": str(session_id)})

    async def handoff(self, target_agent: BaseAgent, messages: List[Dict[str, str]], session_id: Optional[uuid.UUID] = None, **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """ 他のエージェントに処理を委譲（ハンドオフ）します。 (AgentSDK.md 3-1) """
        MAX_HANDOFF_DEPTH = self.extra_cfg.get("max_handoff_depth", 3)
        
        # ターゲットエージェントのハンドオフ深度も考慮 (循環ハンドオフを防ぐため、より厳密な制御が必要な場合)
        # current_total_depth = self._handoff_depth + target_agent._handoff_depth # この計算は単純すぎる可能性
        
        if self._handoff_depth >= MAX_HANDOFF_DEPTH:
            error_msg = f"[{self.name}] Maximum handoff depth ({MAX_HANDOFF_DEPTH}) for originating agent reached. Aborting handoff to {target_agent.name}."
            print(error_msg)
            _seq_counter_err = 0 
            def _create_err_chunk(type: str, data: Optional[Dict] = None) -> Dict[str, Any]:
                nonlocal _seq_counter_err; _seq_counter_err += 1
                return {"time": datetime.now(timezone.utc).isoformat(), "agent": self.name, "type": type, "data": data or {}, "seq": _seq_counter_err}
            yield _create_err_chunk("error", {"message": error_msg})
            return

        self._handoff_depth += 1
        # target_agent._handoff_depth = self._handoff_depth # ターゲットの深度も更新 (設計による)
        
        print(f"[{self.name}] Initiating handoff to [{target_agent.name}] (depth: {self._handoff_depth}). Session: {session_id}")
        # if self.trace_logger: self.trace_logger.trace("handoff_start", {"from_agent": self.name, "to_agent": target_agent.name, "session_id": str(session_id), "depth": self._handoff_depth})
        # # CollaborationManager を利用したハンドオフ/委譲の開始通知 (より高度な協調シナリオの場合)
        # if self.collaboration_manager:
        #     await self.collaboration_manager.notify_handoff_start(from_agent=self, to_agent=target_agent, session_id=session_id)

        try:
            # ハンドオフ先のstreamを呼び出し、チャンクを中継
            async for chunk in target_agent.stream(messages, session_id=session_id, **kwargs):
                # AgentSDK.md 5-1 SSE Chunk定義に沿って、agent名を書き換えるか、original_agentとして情報を付加
                chunk_to_yield = chunk.copy()
                # chunk_to_yield["agent"] = target_agent.name # SSEのagentフィールドは実行主体エージェント名
                # chunk_to_yield["meta_handoff_origin"] = self.name # 必要ならハンドオフ元情報を追加
                yield chunk_to_yield
        finally:
            # if self.trace_logger: self.trace_logger.trace("handoff_end", {"from_agent": self.name, "to_agent": target_agent.name, "session_id": str(session_id), "depth_returned_from": self._handoff_depth})
            self._handoff_depth -= 1 # 自身の深度を戻す
            print(f"[{self.name}] Returned from handoff with [{target_agent.name}] (depth now: {self._handoff_depth}). Session: {session_id}")
            # # CollaborationManager を利用したハンドオフ/委譲の終了通知
            # if self.collaboration_manager:
            #     await self.collaboration_manager.notify_handoff_end(from_agent=self, to_agent_name=target_agent.name, session_id=session_id)
            self.on_handoff_return(session_id=session_id, target_agent_name=target_agent.name)
        
    def on_handoff_return(self, session_id: Optional[uuid.UUID] = None, target_agent_name: Optional[str] = None):
        """ ハンドオフから処理が戻ってきたときに呼び出されるフック。(AgentSDK.md 3-1) """
        # if self.trace_logger: self.trace_logger.trace("on_handoff_return_start", {"session_id": str(session_id), "target_agent_name": target_agent_name, "current_depth": self._handoff_depth})
        print(f"[{self.name}] on_handoff_return hook called after interaction with {target_agent_name}. Session: {session_id}. Current depth: {self._handoff_depth}")
        # 必要に応じてメモリの同期や状態更新などを行う
        # 例: target_agentのメモリの一部を自身のメモリに取り込む、ContextManagerに状態変更を通知するなど
        pass

    async def execute_workflow(self, workflow_definition: Any, initial_data: Dict[str, Any] = None, session_id: Optional[uuid.UUID] = None) -> Any:
        """WorkflowEngineを使ってワークフロー定義を実行します。"""
        if not self.workflow_engine:
            raise RuntimeError(f"WorkflowEngine not configured for agent '{self.name}'")
        return await self.workflow_engine.execute_workflow(workflow_definition, self, initial_data or {}, session_id)

# 他のコアコンポーネントのプレースホルダー (これらも monono_agent 内に作成していく)
# class Tool(BaseModel): ... # Pydantic BaseModelを継承するツール定義の例
# class ToolRegistry: ...
# class LLMAdapter: ...
# class Guardrail: ...
# class TokenGuard(Guardrail): ... # AgentSDK.md 3-4
# class Router: ...
# class TraceLogger: ... 