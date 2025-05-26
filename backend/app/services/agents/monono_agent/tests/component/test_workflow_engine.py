import pytest
from typing import Any, Dict
import uuid

from app.services.agents.monono_agent.base_agent import BaseAgent

# ダミーツールの定義
def dummy_tool1():
    return "output1"

def dummy_tool2():
    return "output2"

def dummy_tool3():
    return "output3"

@pytest.fixture
def agent_with_dummy_tools():
    # LLMAdapter不要のためNoneを渡す
    agent = BaseAgent(name="TestAgent", instructions="TestInstructions", llm_adapter=None)
    agent.tool_registry.register_tool(dummy_tool1)
    agent.tool_registry.register_tool(dummy_tool2)
    agent.tool_registry.register_tool(dummy_tool3)
    return agent

@pytest.mark.asyncio
async def test_sequential_workflow(agent_with_dummy_tools):
    # step1実行後にstep2を依存付きで実行
    wf_def = {
        "workflow": {
            "steps": [
                {"name": "step1", "tool": "dummy_tool1"},
                {"name": "step2", "tool": "dummy_tool2", "depends_on": ["step1"]}
            ]
        }
    }
    result = await agent_with_dummy_tools.execute_workflow(wf_def, initial_data={}, session_id=None)
    # ワークフロー定義が返されていること
    assert result["workflow"] == wf_def["workflow"]
    # 結果マッピングの確認
    assert result["results"]["step1"] == "output1"
    assert result["results"]["step2"] == "output2"

@pytest.mark.asyncio
async def test_parallel_workflow(agent_with_dummy_tools):
    # 並列実行タスクを定義
    wf_def = {
        # top-level workflowラッパーがなくても動作する
        "steps": [
            {"name": "p1", "tool": "dummy_tool1", "parallel": True},
            {"name": "p2", "tool": "dummy_tool2", "parallel": True}
        ]
    }
    result = await agent_with_dummy_tools.execute_workflow(wf_def, initial_data={}, session_id=None)
    # 並列2タスクの結果確認
    assert result["results"]["p1"] == "output1"
    assert result["results"]["p2"] == "output2"

@pytest.mark.asyncio
async def test_condition_skip_workflow(agent_with_dummy_tools):
    # condition != always のステップはスキップされNoneになる
    wf_def = {
        "steps": [
            {"name": "skip", "tool": "dummy_tool3", "condition": "never"}
        ]
    }
    result = await agent_with_dummy_tools.execute_workflow(wf_def, initial_data={}, session_id=None)
    assert "skip" in result["results"]
    assert result["results"]["skip"] is None

@pytest.mark.asyncio
async def test_initial_data_and_parameters(agent_with_dummy_tools):
    # initial_dataを引き継ぐパラメータテスト
    # dummy_tool1,2,3は引数不要なのでinitial_dataのみ反映されないがパラメータ渡し動作確認
    # ここではparametersキーを含むステップを定義
    wf_def = {
        "workflow": {
            "steps": [
                {"name": "step1", "tool": "dummy_tool1", "parameters": {}},
                {"name": "step3", "tool": "dummy_tool3", "parameters": {}}
            ]
        }
    }
    result = await agent_with_dummy_tools.execute_workflow(wf_def, initial_data={"foo": "bar"}, session_id=None)
    assert result["results"]["step1"] == "output1"
    assert result["results"]["step3"] == "output3" 