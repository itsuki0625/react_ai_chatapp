import pytest
from unittest.mock import AsyncMock, patch, call
from langchain_core.agents import AgentAction, AgentFinish
import json

from app.services.agents.self_analysis_langchain.steps.vision import VisionStepAgent
from app.services.agents.self_analysis_langchain.prompts import VISION_PROMPT
from app.services.agents.self_analysis_langchain.tools import note_store, list_notes

@pytest.fixture
def vision_step_agent_fixture():
    return VisionStepAgent()

@pytest.mark.asyncio
async def test_vision_step_agent_call_standard(vision_step_agent_fixture):
    # TEST.MD: I.C-2-1, I.F-1 (ツール呼び出しなし)
    mock_final_response = AgentFinish(return_values={"output": {
        "chat": {
            "vision": "テストビジョン",
            "question": "次の質問は何ですか？"
        }
    }}, log="Final response")
    
    mock_internal_agent = AsyncMock()
    mock_internal_agent.ainvoke = AsyncMock(return_value=mock_final_response)

    with patch("app.services.agents.self_analysis_langchain.steps.vision.build_step_agent", return_value=mock_internal_agent) as mock_build_step_agent:
        agent_to_test = VisionStepAgent()
        input_params = {"messages": [{"role": "user", "content": "ビジョンについて考えたい"}], "session_id": "s_vision_std"}
        result = await agent_to_test(input_params)

    mock_build_step_agent.assert_called_once()
    args, _ = mock_build_step_agent.call_args
    assert args[0] == VISION_PROMPT
    assert note_store in args[1]
    assert list_notes in args[1]

    mock_internal_agent.ainvoke.assert_called_once_with({"input": input_params})
    assert result == mock_final_response.return_values["output"]

@pytest.mark.asyncio
async def test_vision_step_agent_tool_interaction(vision_step_agent_fixture):
    # TEST.MD: I.C-4, I.C-5, II.A
    session_id = "s_vision_tool"
    user_input = "私のキャリアビジョンをノートに保存して。内容は「技術で社会貢献」です。"
    input_params = {"messages": [{"role": "user", "content": user_input}], "session_id": session_id, "current_step": "VISION"}

    tool_call_action = AgentAction(
        tool="note_store", 
        tool_input={"session_id": session_id, "current_step": "VISION", "note_content": json.dumps({"vision_statement": "技術で社会貢献"})},
        log="LLM decided to use note_store for vision"
    )
    final_response_after_tool = AgentFinish(
        return_values={"output": {"chat": {"vision": "技術で社会貢献", "question": "保存しました。他にはありますか？"}}},
        log="LLM generated final response after tool call for vision"
    )

    mock_internal_agent = AsyncMock()
    mock_internal_agent.ainvoke.side_effect = [[tool_call_action], final_response_after_tool]

    mock_note_store_tool_instance = AsyncMock(spec=note_store)
    mock_note_store_tool_instance.name = note_store.name
    mock_note_store_tool_instance.arun = AsyncMock(return_value="ビジョンノートを保存しました。")

    def side_effect_build_step_agent(prompt, tools):
        modified_tools = [mock_note_store_tool_instance if t.name == "note_store" else t for t in tools]
        # テスト用モックを反映するため、toolsリストをインプレースで置き換え
        tools[:] = modified_tools
        return mock_internal_agent

    with patch("app.services.agents.self_analysis_langchain.steps.vision.build_step_agent", side_effect=side_effect_build_step_agent) as mock_build_step_agent:
        agent_to_test = VisionStepAgent()
        result = await agent_to_test(input_params)

    assert mock_internal_agent.ainvoke.call_count == 2
    mock_note_store_tool_instance.arun.assert_called_once_with(**tool_call_action.tool_input)
    expected_intermediate_step = (tool_call_action, "ビジョンノートを保存しました。")
    second_ainvoke_call_args = mock_internal_agent.ainvoke.call_args_list[1]
    assert second_ainvoke_call_args[0][0]["intermediate_steps"] == [expected_intermediate_step]
    assert result == final_response_after_tool.return_values["output"]

@pytest.mark.asyncio
async def test_vision_step_agent_invalid_input_type(vision_step_agent_fixture):
    # TEST.MD: IV.A-1
    agent_to_test = vision_step_agent_fixture
    with pytest.raises(TypeError): 
        await agent_to_test(None)

# TODO: (TEST.MD I.C-4, I.C-5) LLMレスポンス解析とツール呼び出しロジックのより詳細なテスト
# TODO: (TEST.MD IV.A, IV.C) その他のエラーケース

# TODO: (TEST.MD I.C-4, I.C-5) LLMレスポンス解析とツール呼び出しロジックの詳細テスト
# TODO: (TEST.MD IV.A, IV.C) エラーケースのテスト 