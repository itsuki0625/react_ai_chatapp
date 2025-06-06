import pytest
from unittest.mock import AsyncMock, patch, call
from langchain_core.agents import AgentAction, AgentFinish
import json

from app.services.agents.self_analysis_langchain.steps.future import FutureStepAgent
from app.services.agents.self_analysis_langchain.prompts import FUTURE_PROMPT
# tools.py から実際のツールオブジェクトをインポートして比較できるようにする
from app.services.agents.self_analysis_langchain.tools import note_store, list_notes

@pytest.fixture
def future_step_agent_fixture(): #  フィクスチャ名を変更
    return FutureStepAgent()

@pytest.mark.asyncio
async def test_future_step_agent_call_standard(future_step_agent_fixture):
    # TEST.MD: I.C-2-1, I.F-1 (ツール呼び出しなしの基本ケース)
    mock_final_response = AgentFinish(return_values={"output": {
        "chat": {
            "future": "テクノロジーで地域医療格差を解消する",
            "values": ["公平性", "医療DX", "地域貢献"],
            "question": "次に、具体的にどのような医療DX技術に興味がありますか？"
        }
    }}, log="Final response")
    
    mock_internal_agent = AsyncMock() # これは PlanAndExecute の agent_executor_for_chain に近いもの
    # ainvoke が直接 AgentFinish を返す場合 (ツール呼び出しなし)
    mock_internal_agent.ainvoke = AsyncMock(return_value=mock_final_response)

    with patch("app.services.agents.self_analysis_langchain.steps.future.build_step_agent", return_value=mock_internal_agent) as mock_build_step_agent:
        agent_to_test = FutureStepAgent()
        input_params = {"messages": [{"role": "user", "content": "自己分析を始めたいです"}], "session_id": "s1"}
        result = await agent_to_test(input_params) 

    mock_build_step_agent.assert_called_once()
    args, kwargs_call = mock_build_step_agent.call_args
    assert args[0] == FUTURE_PROMPT
    assert note_store in args[1]
    assert list_notes in args[1]

    mock_internal_agent.ainvoke.assert_called_once_with({"input": input_params})
    # FutureStepAgent.__call__ の返り値は AgentFinish の return_values["output"] になる想定
    assert result == mock_final_response.return_values["output"]


@pytest.mark.asyncio
async def test_future_step_agent_tool_interaction(future_step_agent_fixture):
    # TEST.MD: I.C-4, I.C-5, II.A (ツール呼び出しと再帰呼び出し)
    session_id = "test_session_tool_interaction"
    user_input = "私のビジョンをノートに保存してください。内容は「AIで世界を革新する」です。"
    input_params = {"messages": [{"role": "user", "content": user_input}], "session_id": session_id, "current_step": "FUTURE"}

    # 1. LLMがnote_storeツールを呼び出すことを決定 (AgentAction)
    tool_call_action = AgentAction(
        tool="note_store", 
        tool_input={"session_id": session_id, "current_step": "FUTURE", "note_content": json.dumps({"future": "AIで世界を革新する"})},
        log="LLM decided to use note_store"
    )
    # 2. ツール実行後、再度LLMが最終応答を生成 (AgentFinish)
    final_response_after_tool = AgentFinish(
        return_values={"output": {"chat": {"future": "AIで世界を革新する", "values": [], "question": "ノートに保存しました。他にはありますか？"}}},
        log="LLM generated final response after tool call"
    )

    mock_internal_agent = AsyncMock() # PlanAndExecute 内の agent_executor_for_chain (RunnableAgent) に相当
    # ainvoke が最初は AgentAction を、次に AgentFinish を返すように設定
    mock_internal_agent.ainvoke.side_effect = [
        [tool_call_action], # AgentExecutorはリストでActionを返すことがある
        final_response_after_tool
    ]

    # note_store ツール自体もモック (実際のDB書き込みを避ける)
    # tools.py の note_store は Tool.from_function で作られている。
    # そのため、ラップされた関数 (note_store_fn) をモックするか、Toolオブジェクトの .arun() をモックする。
    # ここでは Tool.arun() をモックする方が AgentExecutor の挙動に近い。
    mock_note_store_tool_instance = AsyncMock(spec=note_store)
    mock_note_store_tool_instance.name = note_store.name
    mock_note_store_tool_instance.description = note_store.description
    mock_note_store_tool_instance.arun = AsyncMock(return_value="ノートを保存しました。")

    # build_step_agent が返す agent_executor の中で、ツールが使われる。
    # 渡すツールリストの中に、このモックされたツールインスタンスを入れる必要がある。
    def side_effect_build_step_agent(prompt, tools):
        # tools の中の note_store をモックインスタンスに差し替える
        modified_tools = []
        for t in tools:
            if t.name == "note_store":
                modified_tools.append(mock_note_store_tool_instance)
            else:
                modified_tools.append(t)
        # テスト用モックを反映するため、toolsリストをインプレースで置き換え
        tools[:] = modified_tools
        # 実際の AgentExecutor (あるいはそれに類する runnable) を返す代わりに、
        # ainvoke が上記の side_effect を持つモックエージェントを返す
        return mock_internal_agent

    with patch("app.services.agents.self_analysis_langchain.steps.future.build_step_agent", side_effect=side_effect_build_step_agent) as mock_build_step_agent:
        agent_to_test = FutureStepAgent()
        result = await agent_to_test(input_params)

    assert mock_build_step_agent.call_count == 1 # PlanAndExecute は一度だけ構築される
    
    # 1回目のainvoke (LLMがツール使用を決定)
    # 2回目のainvoke (ツール結果を受けてLLMが最終応答)
    assert mock_internal_agent.ainvoke.call_count == 2
    
    # 1回目の呼び出しはユーザー入力を含む
    first_ainvoke_call_args = mock_internal_agent.ainvoke.call_args_list[0]
    assert first_ainvoke_call_args[0][0]["input"] == input_params
    
    # note_storeツールのarunが期待通り呼び出されたか
    mock_note_store_tool_instance.arun.assert_called_once_with(**tool_call_action.tool_input)

    # 2回目のainvoke呼び出し時の入力 (AgentExecutorが intermediate_steps を含める)
    second_ainvoke_call_args = mock_internal_agent.ainvoke.call_args_list[1]
    # ここで intermediate_steps の内容を検証する。
    # AgentExecutor は (AgentAction, ToolOutput) のタプルを intermediate_steps として渡す。
    expected_intermediate_step = (tool_call_action, "ノートを保存しました。")
    assert second_ainvoke_call_args[0][0]["intermediate_steps"] == [expected_intermediate_step]

    assert result == final_response_after_tool.return_values["output"]


@pytest.mark.asyncio
async def test_future_step_agent_invalid_input_type(future_step_agent_fixture):
    # TEST.MD: IV.A-1 (不正な入力タイプ)
    agent_to_test = future_step_agent_fixture
    with pytest.raises(TypeError, match="'NoneType' object is not subscriptable") as excinfo: # エラーメッセージは実装に依存
        await agent_to_test(None) # 不正な入力 (None)
    # または、より具体的なカスタム例外を期待する場合
    # with pytest.raises(YourCustomInvalidInputError):
    #     await agent_to_test({"wrong_key": "some_value"})

# TODO: (TEST.MD IV.A, IV.C) その他のエラーケースのテスト（不正な入力、ツール実行時エラー）

# TODO: (TEST.MD I.C-4, I.C-5) LLMレスポンス解析とツール呼び出しロジックの詳細テスト
# TODO: (TEST.MD IV.A, IV.C) エラーケースのテスト（不正な入力、ツール実行時エラー） 