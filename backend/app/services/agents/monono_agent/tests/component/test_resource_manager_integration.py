import pytest
import uuid
import json

from app.services.agents.monono_agent.base_agent import BaseAgent
from app.services.agents.monono_agent.components.resource_manager import ResourceManager
from app.services.agents.monono_agent.components.tool_registry import ToolExecutionError

# ダミーツール定義
def dummy_tool():
    return "ok"

@pytest.mark.asyncio
async def test_tool_execution_within_budget():
    # 予算3、コスト2のツールを実行可能
    resource_manager = ResourceManager(cost_tracking={"budget": 3.0, "spent": 0.0})
    agent = BaseAgent(
        name="Agent",
        instructions="test",
        llm_adapter=None,
        resource_manager=resource_manager,
        extra_cfg={"tool_costs": {"dummy_tool": 2.0}}
    )
    agent.tool_registry.register_tool(dummy_tool)

    # tool_callデータを準備
    tool_call = {"id": "1", "function": {"name": "dummy_tool", "arguments": "{}"}}
    # 実行前: spent=0
    assert resource_manager.cost_tracking["spent"] == 0.0

    # _execute_tool_and_get_responseを呼び出し
    llm_msg, chunk = await agent._execute_tool_and_get_response(tool_call, session_id=None)
    # 実行結果の検証
    assert json.loads(llm_msg["content"]) == "ok"
    # コスト追跡が行われていること
    assert resource_manager.cost_tracking["spent"] == pytest.approx(2.0)

@pytest.mark.asyncio
async def test_tool_execution_over_budget():
    # 予算1、コスト2のツールは拒否される
    resource_manager = ResourceManager(cost_tracking={"budget": 1.0, "spent": 0.0})
    agent = BaseAgent(
        name="Agent",
        instructions="test",
        llm_adapter=None,
        resource_manager=resource_manager,
        extra_cfg={"tool_costs": {"dummy_tool": 2.0}}
    )
    agent.tool_registry.register_tool(dummy_tool)

    tool_call = {"id": "1", "function": {"name": "dummy_tool", "arguments": "{}"}}
    # 実行するとToolExecutionErrorが発生
    with pytest.raises(ToolExecutionError):
        await agent._execute_tool_and_get_response(tool_call, session_id=None)
    # spentは変更されない
    assert resource_manager.cost_tracking["spent"] == 0.0

@pytest.mark.asyncio
async def test_llm_usage_tracking_in_stream(monkeypatch):
    # LLMAdapterからusageチャンクを返すモック
    class MockLLMAdapter:
        def __init__(self): self._latest_usage = {}
        async def chat_completion(self, messages, stream=True, **kwargs):
            async def gen():
                yield {"type": "usage", "data": {"prompt_tokens": 5, "completion_tokens": 5}}
            return gen()
        def parse_llm_response_chunk(self, chunk, prev_chunk_data=None): return chunk
        def _set_latest_usage(self, usage): self._latest_usage = usage
        def get_latest_usage(self): return self._latest_usage

    resource_manager = ResourceManager(cost_tracking={"budget": 1.0, "spent": 0.0})
    agent = BaseAgent(
        name="Agent",
        instructions="test",
        llm_adapter=MockLLMAdapter(),
        resource_manager=resource_manager
    )
    # streamを実行してusageチャンクを消費
    async for chunk in agent.stream([{"role": "user", "content": "hi"}], session_id=None):
        if chunk.get("type") == "usage":
            break
    # LLMトークン利用に基づくspent更新 (10 tokens * cost_per_token=0.00001 => 0.0001)
    assert resource_manager.cost_tracking["spent"] == pytest.approx(10 * agent.resource_manager.token_cost_per_token) 