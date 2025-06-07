import pytest
from typing import List, Dict, Any, Optional
import uuid
import json

from app.services.agents.monono_agent.base_agent import BaseAgent
# LLMAdapter の具体的な実装はテストに不要なため、モックやNoneで代替できるか検討
# from app.services.agents.monono_agent.llm_adapters.base_llm_adapter import BaseLLMAdapter 

from app.services.agents.monono_agent.components.guardrail import BaseGuardrail, GuardrailViolationError, MyCustomGuardrail # Guardrail関連をインポート
from app.services.agents.monono_agent.components.tool_registry import ToolExecutionError # ツール実行時のエラー用

# テスト用のダミーLLMAdapter (もしBaseAgentの初期化でNoneを許容しない場合)
class MockLLMAdapter:
    def __init__(self, model_name: str = "mock_model", api_key: Optional[str] = None, **kwargs):
        self.model_name = model_name
        self.api_key = api_key
        self._latest_usage = {}

    async def chat_completion(self, messages: List[Dict[str, Any]], stream: bool = False, **kwargs) -> Any:
        if stream:
            async def stream_response():
                yield {"type": "delta", "data": {"content": "Mock response"}}
                yield {"type": "usage", "data": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}}
            return stream_response()
        else:
            return {"role": "assistant", "content": "Mock response", "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}}

    def parse_llm_response_chunk(self, chunk: Any, prev_chunk_data: Optional[Dict] = None) -> Dict[str, Any]:
        return chunk # 簡単なモック

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return []
    
    def get_latest_usage(self) -> Dict[str, int]:
        return self._latest_usage
    
    def _set_latest_usage(self, usage_data: Dict[str, int]):
        self._latest_usage = usage_data


@pytest.fixture
def base_agent_default_memory() -> BaseAgent:
    """デフォルトのメモリ設定でBaseAgentを初期化するフィクスチャ。"""
    # BaseAgentの初期化にはllm_adapterが必須なのでモックを渡す
    return BaseAgent(name="TestAgent", instructions="Test Instructions", llm_adapter=MockLLMAdapter())

@pytest.fixture
def base_agent_custom_memory() -> BaseAgent:
    """カスタムのメモリ設定でBaseAgentを初期化するフィクスチャ。"""
    return BaseAgent(
        name="TestAgentCustom",
        instructions="Test Instructions Custom",
        extra_cfg={"max_memory_items": 3, "memory_window_size": 2},
        llm_adapter=MockLLMAdapter()
    )

class TestBaseAgentMemory:

    def test_memory_initialization_default(self, base_agent_default_memory: BaseAgent):
        """メモリ設定のデフォルト値確認。"""
        assert base_agent_default_memory.max_memory_items == 20
        assert base_agent_default_memory.memory_window_size == 5

    def test_memory_initialization_custom(self, base_agent_custom_memory: BaseAgent):
        """メモリ設定のカスタム値確認。"""
        assert base_agent_custom_memory.max_memory_items == 3
        assert base_agent_custom_memory.memory_window_size == 2

    def test_add_to_memory_simple_messages(self, base_agent_custom_memory: BaseAgent):
        """単純なメッセージのメモリ追加テスト。"""
        agent = base_agent_custom_memory
        msg1 = {"role": "user", "content": "Hello"}
        msg2 = {"role": "assistant", "content": "Hi there"}
        
        agent._add_to_memory(msg1)
        assert len(agent._memory) == 1
        assert agent._memory[0] == msg1
        
        agent._add_to_memory(msg2)
        assert len(agent._memory) == 2
        assert agent._memory[1] == msg2

    def test_add_to_memory_max_items_limit(self, base_agent_custom_memory: BaseAgent):
        """max_memory_itemsの上限テスト。"""
        agent = base_agent_custom_memory # max_memory_items = 3
        
        msg1 = {"role": "user", "content": "Message 1"}
        msg2 = {"role": "assistant", "content": "Message 2"}
        msg3 = {"role": "user", "content": "Message 3"}
        msg4 = {"role": "assistant", "content": "Message 4"}

        agent._add_to_memory(msg1)
        agent._add_to_memory(msg2)
        agent._add_to_memory(msg3)
        assert len(agent._memory) == 3
        assert agent._memory[0] == msg1

        agent._add_to_memory(msg4) # これでmsg1が追い出されるはず
        assert len(agent._memory) == 3
        assert agent._memory[0] == msg2
        assert agent._memory[1] == msg3
        assert agent._memory[2] == msg4
        
    def test_add_to_memory_with_tool_calls(self, base_agent_custom_memory: BaseAgent):
        """tool_callsを含むアシスタントメッセージの追加テスト。"""
        agent = base_agent_custom_memory
        tool_call_msg = {
            "role": "assistant", 
            "content": None, # contentがNoneでも可
            "tool_calls": [{"id": "call_123", "type": "function", "function": {"name": "get_weather", "arguments": "{\"location\": \"Tokyo\"}"}}]
        }
        agent._add_to_memory(tool_call_msg)
        assert len(agent._memory) == 1
        assert agent._memory[0]["role"] == "assistant"
        assert agent._memory[0]["content"] is None
        assert agent._memory[0]["tool_calls"] == tool_call_msg["tool_calls"]

    def test_add_to_memory_tool_message(self, base_agent_custom_memory: BaseAgent):
        """role='tool'のメッセージ追加テスト。"""
        agent = base_agent_custom_memory
        tool_response_msg = {
            "role": "tool",
            "tool_call_id": "call_123",
            "name": "get_weather",
            "content": "{\"temperature\": 25, \"unit\": \"celsius\"}"
        }
        agent._add_to_memory(tool_response_msg)
        assert len(agent._memory) == 1
        assert agent._memory[0]["role"] == "tool"
        assert agent._memory[0]["tool_call_id"] == "call_123"
        assert agent._memory[0]["name"] == "get_weather"
        assert agent._memory[0]["content"] == tool_response_msg["content"]

    def test_add_to_memory_missing_role_or_content(self, base_agent_custom_memory: BaseAgent):
        """不正なメッセージが追加されないことの確認。"""
        agent = base_agent_custom_memory
        agent._add_to_memory({"foo": "bar"}) # role も content/tool_calls もない
        assert len(agent._memory) == 0

        agent._add_to_memory({"role": "user"}) # content/tool_calls がない
        assert len(agent._memory) == 0


    def test_preprocess_messages_empty_memory(self, base_agent_custom_memory: BaseAgent):
        """メモリが空の場合の_preprocess_messagesテスト。"""
        agent = base_agent_custom_memory
        user_messages = [{"role": "user", "content": "Hello"}]
        
        processed = agent._preprocess_messages(user_messages)
        
        assert len(processed) == 2 # system + user
        assert processed[0]["role"] == "system"
        assert processed[0]["content"] == agent.instructions
        assert processed[1] == user_messages[0]

    def test_preprocess_messages_with_memory_window(self, base_agent_custom_memory: BaseAgent):
        """memory_window_sizeを考慮した_preprocess_messagesテスト。"""
        agent = base_agent_custom_memory # memory_window_size = 2, max_memory_items = 3
        
        mem_msg1 = {"role": "user", "content": "Memory 1"}
        mem_msg2 = {"role": "assistant", "content": "Memory 2"}
        mem_msg3 = {"role": "user", "content": "Memory 3"}
        
        agent._add_to_memory(mem_msg1)
        agent._add_to_memory(mem_msg2)
        agent._add_to_memory(mem_msg3) # メモリには [mem_msg1, mem_msg2, mem_msg3] がある
        
        current_user_msg = [{"role": "user", "content": "Current Question"}]
        processed = agent._preprocess_messages(current_user_msg)
        
        assert len(processed) == 1 + 2 + 1 # system + memory_window_size + current_user
        assert processed[0]["role"] == "system"
        # memory_window_size = 2 なので、mem_msg2 と mem_msg3 が含まれる
        assert processed[1] == mem_msg2 
        assert processed[2] == mem_msg3
        assert processed[3] == current_user_msg[0]

    def test_preprocess_messages_window_larger_than_memory(self, base_agent_default_memory: BaseAgent):
        """memory_window_sizeが実際のメモリ件数より大きい場合のテスト。"""
        agent = base_agent_default_memory # memory_window_size = 5
        
        mem_msg1 = {"role": "user", "content": "Memory 1"}
        mem_msg2 = {"role": "assistant", "content": "Memory 2"}
        
        agent._add_to_memory(mem_msg1)
        agent._add_to_memory(mem_msg2) # メモリには2件
        
        current_user_msg = [{"role": "user", "content": "Current Question"}]
        processed = agent._preprocess_messages(current_user_msg)
        
        assert len(processed) == 1 + 2 + 1 # system + (actual memory size) + current_user
        assert processed[0]["role"] == "system"
        assert processed[1] == mem_msg1
        assert processed[2] == mem_msg2
        assert processed[3] == current_user_msg[0]

    def test_preprocess_messages_zero_or_none_window_size(self):
        """memory_window_sizeが0またはNoneの場合(全メモリ使用)のテスト。"""
        agent_zero_window = BaseAgent(
            name="ZeroWindowAgent", instructions="Zero Test", 
            extra_cfg={"max_memory_items": 5, "memory_window_size": 0}, # window_size = 0
            llm_adapter=MockLLMAdapter()
        )
        agent_none_window = BaseAgent(
            name="NoneWindowAgent", instructions="None Test", 
            extra_cfg={"max_memory_items": 5, "memory_window_size": None}, # window_size = None
            llm_adapter=MockLLMAdapter()
        )

        agents_to_test = [agent_zero_window, agent_none_window]

        for agent in agents_to_test:
            mem_msg1 = {"role": "user", "content": "Memory 1 for " + agent.name}
            mem_msg2 = {"role": "assistant", "content": "Memory 2 for " + agent.name}
            mem_msg3 = {"role": "user", "content": "Memory 3 for " + agent.name}
            
            agent._add_to_memory(mem_msg1)
            agent._add_to_memory(mem_msg2)
            agent._add_to_memory(mem_msg3) # メモリに3件
            
            current_user_msg = [{"role": "user", "content": "Current Question for " + agent.name}]
            processed = agent._preprocess_messages(current_user_msg)
            
            assert len(processed) == 1 + 3 + 1 # system + (all memory) + current_user
            assert processed[0]["role"] == "system"
            assert processed[1] == mem_msg1
            assert processed[2] == mem_msg2
            assert processed[3] == mem_msg3
            assert processed[4] == current_user_msg[0] 


class TestBaseAgentGuardrail:

    @pytest.fixture
    def agent_with_no_guardrail(self) -> BaseAgent:
        return BaseAgent(name="NoGuardAgent", instructions="Test", llm_adapter=MockLLMAdapter())

    @pytest.fixture
    def agent_with_default_guardrail(self) -> BaseAgent:
        return BaseAgent(name="DefaultGuardAgent", instructions="Test", llm_adapter=MockLLMAdapter(), guardrail=BaseGuardrail())

    @pytest.mark.asyncio
    async def test_run_with_no_guardrail(self, agent_with_no_guardrail: BaseAgent):
        """Guardrailなしでの基本的なrunメソッドの動作確認。"""
        messages = [{"role": "user", "content": "Hello"}]
        response = await agent_with_no_guardrail.run(messages)
        assert response["role"] == "assistant"
        assert "Mock response" in response["content"]
        assert "error" not in response

    @pytest.mark.asyncio
    async def test_run_with_default_guardrail(self, agent_with_default_guardrail: BaseAgent):
        """デフォルトGuardrailでの基本的なrunメソッドの動作確認。"""
        messages = [{"role": "user", "content": "Hello"}]
        response = await agent_with_default_guardrail.run(messages)
        assert response["role"] == "assistant"
        assert "Mock response" in response["content"]
        assert "error" not in response

    @pytest.mark.asyncio
    async def test_input_guardrail_violation_run(self):
        """check_inputがエラーを発生させた場合のrunメソッドのテスト。"""
        guardrail = InputViolationGuardrail()
        agent = BaseAgent(name="InputGuardAgent", instructions="Test", llm_adapter=MockLLMAdapter(), guardrail=guardrail)
        messages = [{"role": "user", "content": "This message will trigger_input_violation"}]
        
        response = await agent.run(messages)
        
        assert response["role"] == "assistant"
        assert "error" in response
        assert response["error"]["type"] == "GuardrailViolationError"
        assert "Input violation triggered" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_input_guardrail_violation_stream(self):
        """check_inputがエラーを発生させた場合のstreamメソッドのテスト。"""
        guardrail = InputViolationGuardrail()
        agent = BaseAgent(name="InputGuardStreamAgent", instructions="Test", llm_adapter=MockLLMAdapter(), guardrail=guardrail)
        messages = [{"role": "user", "content": "This message will trigger_input_violation"}]
        
        error_chunk_received = False
        async for chunk in agent.stream(messages):
            if chunk.get("type") == "error":
                assert chunk["data"]["type"] == "GuardrailViolationError"
                assert "Input violation triggered" in chunk["data"]["message"]
                error_chunk_received = True
                break # エラーを受け取ったらループ終了
        assert error_chunk_received

    @pytest.mark.asyncio
    async def test_output_guardrail_violation_stream(self):
        """check_outputがエラーを発生させた場合のstreamメソッドのテスト。"""
        guardrail = OutputViolationGuardrail()
        # MockLLMAdapter が "Mock response" を返すので、それをトリガーワードに含める
        # ただし、MockLLMAdapterの応答を書き換えるか、Guardrailがそれを検知できるようにする
        class TriggeringMockLLMAdapter(MockLLMAdapter):
            async def chat_completion(self, messages: List[Dict[str, Any]], stream: bool = False, **kwargs) -> Any:
                if stream:
                    async def stream_response():
                        yield {"type": "delta", "data": {"content": "Part one, trigger_output_violation then more."}}
                        yield {"type": "usage", "data": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}}
                    return stream_response()
                return super().chat_completion(messages, stream, **kwargs) # runは非対応で良い

        agent = BaseAgent(name="OutputGuardStreamAgent", instructions="Test", llm_adapter=TriggeringMockLLMAdapter(), guardrail=guardrail)
        messages = [{"role": "user", "content": "Hello"}]
        
        error_chunk_received = False
        delta_received_before_error = False
        async for chunk in agent.stream(messages):
            if chunk.get("type") == "delta": # エラー前にdeltaが来るか (Guardrailによる)
                delta_received_before_error = True 
            if chunk.get("type") == "error":
                assert chunk["data"]["type"] == "GuardrailViolationError"
                assert "Output violation triggered" in chunk["data"]["message"]
                error_chunk_received = True
                break
        assert error_chunk_received
        # assert not delta_received_before_error # Guardrailがdeltaをブロックする場合。現状はdelta後にエラーになるのでTrue

    @pytest.mark.asyncio
    async def test_tool_execution_denied_by_guardrail_run(self):
        """can_execute_toolがFalseを返した場合のrunメソッドテスト。"""
        restricted_tool_name = "restricted_tool"
        guardrail = DenySpecificToolGuardrail(restricted_tool_name=restricted_tool_name)
        tools = [dummy_tool_allowed, dummy_tool_restricted]

        class DeniedToolCallMockLLMAdapter(MockLLMAdapter):
            async def chat_completion(self, messages: List[Dict[str, Any]], stream: bool = False, **kwargs) -> Any:
                last_message = messages[-1] if messages else {}
                # print(f"[DeniedToolCallMockLLMAdapter] Last message: {last_message}") # Debug
                if last_message.get("role") == "user":
                    # 最初の応答で restricted_tool を呼び出すようにする
                    tool_call_chunk_data = {"tool_calls": [{
                        "id": "call_deny_test001",
                        "type": "function",
                        "function": {"name": dummy_tool_restricted.__name__, "arguments": '{"secret_param": "test_value"}'}
                    }]}
                    if stream:
                        async def stream_user_phase():
                            yield {"type": "tool_calls", "data": tool_call_chunk_data}
                            yield {"type": "usage", "data": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}
                        return stream_user_phase()
                    return {"role": "assistant", "content": None, "tool_calls": tool_call_chunk_data["tool_calls"]}
                elif last_message.get("role") == "tool":
                    # ツール実行結果 (エラーのはず) を受け取ったら、エラー応答を返す
                    tool_content_str = last_message.get("content", "{}")
                    try:
                        tool_content_data = json.loads(tool_content_str)
                        error_detail = tool_content_data.get("error", "Unknown tool error")
                        error_type = tool_content_data.get("type", "ToolError")
                        response_content = f"Guardrail denied tool execution. Detail: {error_detail} ({error_type})"
                    except json.JSONDecodeError:
                        response_content = "Guardrail denied tool execution. Could not parse tool response."

                    if stream:
                        async def stream_tool_error_phase():
                            yield {"type": "delta", "data": {"content": response_content}}
                            yield {"type": "usage", "data": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}
                        return stream_tool_error_phase()
                    return {"role": "assistant", "content": response_content}
                else: # どの条件にも当てはまらない場合
                    if stream:
                        async def empty_stream():
                            if False: # 何もyieldしないことを明示
                                yield
                        return empty_stream()
                    return {"role": "assistant", "content": "Unexpected state in DeniedToolCallMockLLMAdapter"}


        agent = BaseAgent(
            name="ToolDenyAgent",
            instructions="Use tools",
            llm_adapter=DeniedToolCallMockLLMAdapter(), # 修正
            tools=tools,
            guardrail=guardrail
        )

        user_message = [{"role": "user", "content": f"Please use {restricted_tool_name}"}]
        response = await agent.run(user_message)

        assert response["role"] == "assistant"
        assert "error" in response
        assert response["error"]["type"] == "GuardrailViolationError" # BaseAgentが発行するエラー
        assert f"Execution of tool '{restricted_tool_name}' denied by Guardrail." in response["error"]["message"]
        assert response["error"]["details"]["tool_name"] == restricted_tool_name

    @pytest.mark.asyncio
    async def test_tool_execution_allowed_by_guardrail_run(self):
        """can_execute_toolがTrueを返した場合のrunメソッドテスト。"""
        allowed_tool_name = "dummy_tool_allowed"
        guardrail = DenySpecificToolGuardrail(restricted_tool_name="some_other_tool")
        tools = [dummy_tool_allowed, dummy_tool_restricted]

        class AllowedToolCallMockLLMAdapter(MockLLMAdapter):
            async def chat_completion(self, messages: List[Dict[str, Any]], stream: bool = False, **kwargs) -> Any:
                last_message = messages[-1] if messages else {}
                # print(f"[AllowedToolCallMockLLMAdapter] Last message: {last_message}") # Debug

                if last_message.get("role") == "user":
                    tool_call_data = {"tool_calls": [{
                        "id": "call_allow_test002",
                        "type": "function",
                        "function": {"name": allowed_tool_name, "arguments": '{"param": "allowed_value"}'}
                    }]}
                    if stream:
                        async def stream_user_phase():
                            yield {"type": "tool_calls", "data": tool_call_data}
                            yield {"type": "usage", "data": {"prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11}}
                        return stream_user_phase()
                    return {"role": "assistant", "content": None, "tool_calls": tool_call_data["tool_calls"]}

                elif last_message.get("role") == "tool":
                    tool_result_content_str = last_message.get("content", "{}")
                    response_content = f"Tool said: {tool_result_content_str}" # JSON文字列のまま結合
                    if stream:
                        async def stream_tool_result_phase():
                            yield {"type": "delta", "data": {"content": response_content}}
                            yield {"type": "usage", "data": {"prompt_tokens": 1, "completion_tokens": 10, "total_tokens": 11}}
                        return stream_tool_result_phase()
                    return {"role": "assistant", "content": response_content, "usage": {"prompt_tokens": 1, "completion_tokens": 10, "total_tokens": 11}}
                else: # どの条件にも当てはまらない場合
                    if stream:
                        async def empty_stream():
                            if False: # 何もyieldしないことを明示
                                yield
                        return empty_stream()
                    return {"role": "assistant", "content": "Unexpected state in AllowedToolCallMockLLMAdapter"}

        agent = BaseAgent(
            name="ToolAllowAgent",
            instructions="Use tools",
            llm_adapter=AllowedToolCallMockLLMAdapter(), # 修正
            tools=tools,
            guardrail=guardrail
        )

        user_message = [{"role": "user", "content": f"Please use {allowed_tool_name}"}]
        response = await agent.run(user_message)

        assert response["role"] == "assistant"
        assert "error" not in response, f"Expected no error, but got: {response.get('error')}"
        expected_tool_output = dummy_tool_allowed(param="allowed_value")
        # ツールからの出力はJSON文字列として返されるので、比較対象もJSON文字列にする
        assert f"Tool said: {json.dumps(expected_tool_output)}" in response["content"]

# --- テスト用のサンプルツール --- 
def dummy_tool_allowed(param: str = "default"):
    """常に許可されることを期待されるダミーのツール。"""
    return f"dummy_tool_allowed executed with {param}"

def dummy_tool_restricted(secret_param: str):
    """特定のGuardrailによって制限されることを期待されるダミーのツール。"""
    return f"dummy_tool_restricted executed with {secret_param}"

# --- テスト用のカスタムGuardrail --- 
class DenyAllToolsGuardrail(BaseGuardrail):
    async def can_execute_tool(self, tool_name: str, tool_args: Dict[str, Any], **kwargs) -> bool:
        print(f"[DenyAllToolsGuardrail] Denying execution for tool: {tool_name}")
        return False

class DenySpecificToolGuardrail(BaseGuardrail):
    def __init__(self, restricted_tool_name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.restricted_tool_name = restricted_tool_name

    async def can_execute_tool(self, tool_name: str, tool_args: Dict[str, Any], **kwargs) -> bool:
        if tool_name == self.restricted_tool_name:
            print(f"[DenySpecificToolGuardrail] Denying execution for tool: {tool_name}")
            return False
        return True

class InputViolationGuardrail(BaseGuardrail):
    async def check_input(self, messages: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        for msg in messages:
            if isinstance(msg.get("content"), str) and "trigger_input_violation" in msg["content"]:
                raise GuardrailViolationError("Input violation triggered by test guardrail", details={"content": msg["content"]})
        return messages

class OutputViolationGuardrail(BaseGuardrail):
    async def check_output(self, response_chunk: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        if response_chunk.get("type") == "delta" and \
           isinstance(response_chunk.get("data", {}).get("content"), str) and \
           "trigger_output_violation" in response_chunk["data"]["content"]:
            raise GuardrailViolationError("Output violation triggered by test guardrail", details=response_chunk)
        return response_chunk 