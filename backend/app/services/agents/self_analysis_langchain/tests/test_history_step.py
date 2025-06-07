import pytest
from unittest.mock import AsyncMock, patch, call
from langchain_core.agents import AgentAction, AgentFinish
import json

from app.services.agents.self_analysis_langchain.steps.history import HistoryStepAgent
from app.services.agents.self_analysis_langchain.prompts import HISTORY_PROMPT
from app.services.agents.self_analysis_langchain.tools import note_store, list_notes, render_markdown_timeline

@pytest.fixture
def history_step_agent_fixture():
    return HistoryStepAgent()

@pytest.mark.asyncio
async def test_history_step_agent_call_standard(history_step_agent_fixture):
    # TEST.MD: I.C-2-1, I.F-1 (ツール呼び出しなし)
    mock_final_response = AgentFinish(return_values={"output": {
        "chat": {
            "timeline": [{"year": 2023, "event": "テストイベント"}],
            "question": "次の質問は何ですか？"
        }
    }}, log="Final response")
    
    mock_internal_agent = AsyncMock()
    mock_internal_agent.ainvoke = AsyncMock(return_value=mock_final_response)

    with patch("app.services.agents.self_analysis_langchain.steps.history.build_step_agent", return_value=mock_internal_agent) as mock_build_step_agent:
        agent_to_test = HistoryStepAgent()
        input_params = {"messages": [{"role": "user", "content": "経歴について話したい"}], "session_id": "s_history_std"}
        result = await agent_to_test(input_params)

    mock_build_step_agent.assert_called_once()
    args, _ = mock_build_step_agent.call_args
    assert args[0] == HISTORY_PROMPT
    assert note_store in args[1]
    assert list_notes in args[1]
    # assert render_markdown_timeline in args[1] # 現状のHistoryStepAgentでは直接使われていない

    mock_internal_agent.ainvoke.assert_called_once_with({"input": input_params})
    assert result == mock_final_response.return_values["output"]

@pytest.mark.asyncio
async def test_history_step_agent_tool_interaction(history_step_agent_fixture):
    # TEST.MD: I.C-4, I.C-5, II.A (note_store ツール呼び出し)
    session_id = "s_history_tool"
    user_input = "私の職務経歴をノートに保存してください。内容は「A社でBに従事」です。"
    input_params = {"messages": [{"role": "user", "content": user_input}], "session_id": session_id, "current_step": "HISTORY"}

    tool_call_action = AgentAction(
        tool="note_store", 
        tool_input={"session_id": session_id, "current_step": "HISTORY", "note_content": json.dumps({"timeline_event": "A社でBに従事"})},
        log="LLM decided to use note_store for history"
    )
    final_response_after_tool = AgentFinish(
        return_values={"output": {"chat": {"timeline": [{"event": "A社でBに従事"}], "question": "保存しました。他にはありますか？"}}},
        log="LLM generated final response after tool call for history"
    )

    mock_internal_agent = AsyncMock()
    mock_internal_agent.ainvoke.side_effect = [[tool_call_action], final_response_after_tool]

    mock_note_store_tool_instance = AsyncMock(spec=note_store)
    mock_note_store_tool_instance.name = note_store.name
    mock_note_store_tool_instance.arun = AsyncMock(return_value="履歴ノートを保存しました。")

    def side_effect_build_step_agent(prompt, tools):
        modified_tools = [mock_note_store_tool_instance if t.name == "note_store" else t for t in tools]
        # テスト用モックを反映するため、toolsリストをインプレースで置き換え
        tools[:] = modified_tools
        return mock_internal_agent

    with patch("app.services.agents.self_analysis_langchain.steps.history.build_step_agent", side_effect=side_effect_build_step_agent) as mock_build_step_agent:
        agent_to_test = HistoryStepAgent()
        result = await agent_to_test(input_params)

    assert mock_internal_agent.ainvoke.call_count == 2
    mock_note_store_tool_instance.arun.assert_called_once_with(**tool_call_action.tool_input)
    expected_intermediate_step = (tool_call_action, "履歴ノートを保存しました。")
    second_ainvoke_call_args = mock_internal_agent.ainvoke.call_args_list[1]
    assert second_ainvoke_call_args[0][0]["intermediate_steps"] == [expected_intermediate_step]
    assert result == final_response_after_tool.return_values["output"]

@pytest.mark.asyncio
async def test_history_step_agent_invalid_input_type(history_step_agent_fixture):
    # TEST.MD: IV.A-1
    agent_to_test = history_step_agent_fixture
    with pytest.raises(TypeError): 
        await agent_to_test(None)

# TODO: (TEST.MD I.C-4, I.C-5) LLMレスポンス解析とツール呼び出しロジックのより詳細なテスト
# TODO: (TEST.MD A-1-3) HistoryStepAgent またはそのツールによるMarkdownタイムライン生成のテスト (render_markdown_timeline ツールの使用を検討)
# TODO: (TEST.MD IV.A, IV.C) その他のエラーケース（例：ツール実行時エラー）

# TODO: (TEST.MD I.C-4, I.C-5) LLMレスポンス解析とツール呼び出しロジックの詳細テスト
# TODO: (TEST.MD A-1-3) HistoryStepAgent またはそのツールによるMarkdownタイムライン生成のテスト
# TODO: (TEST.MD IV.A, IV.C) エラーケースのテスト 