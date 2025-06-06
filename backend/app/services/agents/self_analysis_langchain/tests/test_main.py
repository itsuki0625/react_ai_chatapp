import pytest
from unittest.mock import AsyncMock, patch, MagicMock, call
import json

from app.services.agents.self_analysis_langchain.main import (
    SelfAnalysisOrchestrator, 
    SelfAnalysisState,
    FutureStepAgent, 
    MotivationStepAgent, 
    HistoryStepAgent, 
    GapStepAgent, 
    VisionStepAgent, 
    ReflectStepAgent
)
from app.models.self_analysis import SelfAnalysisSession

# Helper to create a mock response for a step agent's __call__ method
# This simulates the agent adding its output to the messages list
# and potentially setting other state fields.
def create_step_mock_return_value(previous_messages: list, agent_name: str, output_data: dict, next_step_in_state: str | None = None):
    new_message = {"role": "assistant", f"{agent_name}_output": output_data} # Simplified message
    # Actual agent might produce a more complex chat structure, e.g. {"role": "assistant", "chat": output_data}
    # For GAP agent, output_data must contain "gaps" for conditional logic.
    if agent_name == "GAP":
        new_message = {"role": "assistant", "content": "Gap analysis output", "chat": output_data } 

    current_state_update = {
        "messages": previous_messages + [new_message]
    }
    if next_step_in_state:
        # This 'next_step' is if the agent itself tries to update the 'next_step' field in the state.
        # For DB logging, the 'next_step' from the *final* state of the graph matters.
        current_state_update["next_step"] = next_step_in_state 
    return current_state_update

@pytest.fixture
def orchestrator_fixture():
    # SelfAnalysisOrchestratorのインスタンスを返すフィクスチャ
    return SelfAnalysisOrchestrator()

@pytest.mark.asyncio
async def test_orchestrator_initial_run_mocked_ainvoke(orchestrator_fixture):
    # このテストは orchestrator.ainvoke 全体をモックする以前のものです。
    # 詳細な遷移テストを別途設けるため、名前を変更して残します。
    # TEST.MD: II. C-3 (部分的に関連), I. I-1
    initial_messages = [{"role": "user", "content": "自己分析を始めたいです"}]
    session_id = "test_session_initial_run_mocked_ainvoke"

    # Correctly mock AsyncSessionLocal to return an async context manager
    mock_db_context_manager = AsyncMock() 
    mock_db_operations = AsyncMock(spec=['get', 'add', 'commit', 'refresh']) 
    # Ensure db.get() itself is an AsyncMock that returns the desired value upon await
    mock_db_operations.get = AsyncMock(return_value=None) 
    mock_db_context_manager.__aenter__.return_value = mock_db_operations
    mock_db_context_manager.__aexit__ = AsyncMock(return_value=False) 
    
    mock_final_state_from_graph = SelfAnalysisState(
        messages=[{"role": "assistant", "content": "Some final output from graph"}], 
        session_id=session_id,
        next_step="FINAL_STEP_REACHED" # Graphの最終状態が持つnext_step
    )

    with patch("app.services.agents.self_analysis_langchain.main.AsyncSessionLocal", return_value=mock_db_context_manager), \
         patch.object(orchestrator_fixture.orchestrator, 'ainvoke', AsyncMock(return_value=mock_final_state_from_graph)) as mock_graph_ainvoke:
        
        result = await orchestrator_fixture.run(messages=initial_messages, session_id=session_id)

    assert result is not None
    assert result["next_step"] == "FINAL_STEP_REACHED"

    mock_graph_ainvoke.assert_called_once()
    call_args = mock_graph_ainvoke.call_args[0][0]
    assert call_args["messages"] == initial_messages
    assert call_args["session_id"] == session_id

    mock_db_operations.add.assert_called_once()
    added_instance = mock_db_operations.add.call_args[0][0]
    assert isinstance(added_instance, SelfAnalysisSession)
    assert added_instance.id == session_id
    assert added_instance.current_step == "FINAL_STEP_REACHED"
    mock_db_operations.commit.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_linear_flow_detailed_transitions(orchestrator_fixture):
    # TEST.MD: II.C-1 (直線的遷移)
    session_id = "test_linear_flow"
    initial_messages = [{"role": "user", "content": "Start analysis"}]

    mock_db_context_manager = AsyncMock()
    mock_db_operations = AsyncMock(spec=['get', 'add', 'commit', 'refresh'])
    mock_db_operations.get = AsyncMock(return_value=None) # New session
    mock_db_context_manager.__aenter__.return_value = mock_db_operations
    mock_db_context_manager.__aexit__ = AsyncMock(return_value=False)

    # Patch the __call__ method of each StepAgent class directly
    with patch.object(FutureStepAgent, '__call__', new_callable=AsyncMock) as mock_future_call, \
         patch.object(MotivationStepAgent, '__call__', new_callable=AsyncMock) as mock_motivation_call, \
         patch.object(HistoryStepAgent, '__call__', new_callable=AsyncMock) as mock_history_call, \
         patch.object(GapStepAgent, '__call__', new_callable=AsyncMock) as mock_gap_call, \
         patch.object(VisionStepAgent, '__call__', new_callable=AsyncMock) as mock_vision_call, \
         patch.object(ReflectStepAgent, '__call__', new_callable=AsyncMock) as mock_reflect_call:

        # モックの戻り値を設定 (状態の messages が徐々に構築されるように)
        future_out_messages = initial_messages + [{"role": "assistant", "content": "Future done"}]
        mock_future_call.return_value = {"messages": future_out_messages}

        motivation_out_messages = future_out_messages + [{"role": "assistant", "content": "Motivation done"}]
        mock_motivation_call.return_value = {"messages": motivation_out_messages}
        
        history_out_messages = motivation_out_messages + [{"role": "assistant", "content": "History done"}]
        mock_history_call.return_value = {"messages": history_out_messages}

        # GAP agent must return {"chat": {"gaps": [...]}} in its message for conditional logic
        gap_chat_output_with_gaps = {"gaps": [{"name": "gap1"}]}
        gap_out_messages = history_out_messages + [{"role": "assistant", "content": "Gap with gaps", "chat": gap_chat_output_with_gaps}]
        mock_gap_call.return_value = {"messages": gap_out_messages} 

        vision_out_messages = gap_out_messages + [{"role": "assistant", "content": "Vision done"}]
        mock_vision_call.return_value = {"messages": vision_out_messages}

        reflect_out_messages = vision_out_messages + [{"role": "assistant", "content": "Reflect done"}]
        # Reflect node sets the final 'next_step' for DB logging
        mock_reflect_call.return_value = {"messages": reflect_out_messages, "next_step": "ALL_STEPS_COMPLETED"}

        with patch("app.services.agents.self_analysis_langchain.main.AsyncSessionLocal", return_value=mock_db_context_manager):
            final_state = await orchestrator_fixture.run(messages=initial_messages, session_id=session_id)

        # Assertions
        mock_future_call.assert_called_once()
        mock_motivation_call.assert_called_once()
        mock_history_call.assert_called_once()
        mock_gap_call.assert_called_once()
        mock_vision_call.assert_called_once() # Should be called in linear flow
        mock_reflect_call.assert_called_once()

        # Check final state from orchestrator.run
        assert final_state["messages"][-1]["content"] == "Reflect done"
        assert final_state.get("next_step") == "ALL_STEPS_COMPLETED"

        # Check DB
        mock_db_operations.add.assert_called_once()
        added_db_instance = mock_db_operations.add.call_args[0][0]
        assert added_db_instance.current_step == "ALL_STEPS_COMPLETED"
        mock_db_operations.commit.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_conditional_skip_vision_detailed(orchestrator_fixture):
    # TEST.MD: II.C-1-3 (GAPからの条件分岐、VISIONスキップ)
    session_id = "test_conditional_skip"
    initial_messages = [{"role": "user", "content": "Start analysis for skip"}]

    mock_db_context_manager = AsyncMock()
    mock_db_operations = AsyncMock(spec=['get', 'add', 'commit', 'refresh'])
    mock_db_operations.get = AsyncMock(return_value=None)
    mock_db_context_manager.__aenter__.return_value = mock_db_operations
    mock_db_context_manager.__aexit__ = AsyncMock(return_value=False)

    # Patch the __call__ method of each StepAgent class directly
    with patch.object(FutureStepAgent, '__call__', new_callable=AsyncMock) as mock_future_call, \
         patch.object(MotivationStepAgent, '__call__', new_callable=AsyncMock) as mock_motivation_call, \
         patch.object(HistoryStepAgent, '__call__', new_callable=AsyncMock) as mock_history_call, \
         patch.object(GapStepAgent, '__call__', new_callable=AsyncMock) as mock_gap_call, \
         patch.object(VisionStepAgent, '__call__', new_callable=AsyncMock) as mock_vision_call, \
         patch.object(ReflectStepAgent, '__call__', new_callable=AsyncMock) as mock_reflect_call:

        future_out_messages = initial_messages + [{"role": "assistant", "content": "Future done"}]
        mock_future_call.return_value = {"messages": future_out_messages}

        motivation_out_messages = future_out_messages + [{"role": "assistant", "content": "Motivation done"}]
        mock_motivation_call.return_value = {"messages": motivation_out_messages}
        
        history_out_messages = motivation_out_messages + [{"role": "assistant", "content": "History done"}]
        mock_history_call.return_value = {"messages": history_out_messages}

        # GAP agent returns NO gaps for conditional logic
        gap_chat_output_no_gaps = {"gaps": []} # Empty list of gaps
        gap_out_messages = history_out_messages + [{"role": "assistant", "content": "Gap with no gaps", "chat": gap_chat_output_no_gaps}]
        mock_gap_call.return_value = {"messages": gap_out_messages}

        # Reflect node sets the final 'next_step'
        # Vision is skipped, so reflect_out_messages should follow gap_out_messages
        reflect_out_messages = gap_out_messages + [{"role": "assistant", "content": "Reflect after skip"}]
        mock_reflect_call.return_value = {"messages": reflect_out_messages, "next_step": "SKIPPED_VISION_COMPLETED"}

        with patch("app.services.agents.self_analysis_langchain.main.AsyncSessionLocal", return_value=mock_db_context_manager):
            final_state = await orchestrator_fixture.run(messages=initial_messages, session_id=session_id)

        mock_future_call.assert_called_once()
        mock_motivation_call.assert_called_once()
        mock_history_call.assert_called_once()
        mock_gap_call.assert_called_once()
        mock_vision_call.assert_not_called() # VISION should be skipped
        mock_reflect_call.assert_called_once()

        assert final_state["messages"][-1]["content"] == "Reflect after skip"
        assert final_state.get("next_step") == "SKIPPED_VISION_COMPLETED"

        mock_db_operations.add.assert_called_once()
        added_db_instance = mock_db_operations.add.call_args[0][0]
        assert added_db_instance.current_step == "SKIPPED_VISION_COMPLETED"
        mock_db_operations.commit.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_run_with_existing_session_mocked_ainvoke(orchestrator_fixture):
    # このテストは orchestrator.ainvoke 全体をモックする以前のものです。
    # 詳細な遷移テストを別途設けるため、名前を変更して残します。
    # TEST.MD: I. I-1, II. C-2
    session_id = "test_existing_session_mocked_ainvoke"
    initial_messages = [{"role": "user", "content": "続きからお願いします"}]
    
    existing_session = SelfAnalysisSession(id=session_id, current_step="HISTORY")
    
    mock_db_context_manager = AsyncMock()
    mock_db_operations = AsyncMock(spec=['get', 'add', 'commit', 'refresh'])
    # Ensure db.get() itself is an AsyncMock that returns the desired value upon await
    mock_db_operations.get = AsyncMock(return_value=existing_session) 
    mock_db_context_manager.__aenter__.return_value = mock_db_operations
    mock_db_context_manager.__aexit__ = AsyncMock(return_value=False)

    mock_final_state_from_graph = SelfAnalysisState(
        messages=[{"role": "assistant", "content": "Continuation output"}],
        session_id=session_id,
        next_step="CONTINUATION_COMPLETED"
    )

    with patch("app.services.agents.self_analysis_langchain.main.AsyncSessionLocal", return_value=mock_db_context_manager), \
         patch.object(orchestrator_fixture.orchestrator, 'ainvoke', AsyncMock(return_value=mock_final_state_from_graph)) as mock_graph_ainvoke:
        
        result = await orchestrator_fixture.run(messages=initial_messages, session_id=session_id)

    assert result["next_step"] == "CONTINUATION_COMPLETED"

    mock_db_operations.get.assert_called_once_with(SelfAnalysisSession, session_id)
    mock_db_operations.add.assert_called_once() 
    updated_instance = mock_db_operations.add.call_args[0][0]
    assert isinstance(updated_instance, SelfAnalysisSession)
    assert updated_instance.id == session_id
    assert updated_instance.current_step == "CONTINUATION_COMPLETED" 
    mock_db_operations.commit.assert_called_once()

# TODO: (TEST.MD IV, V) 異常系テスト（不正な入力、外部サービスエラーなど）
# TODO: (TEST.MD I.C, I.F) 各StepAgentのロジック（プロンプト、ツール呼び出し）のより詳細なユニットテスト (各test_XXX_step.pyにて) 