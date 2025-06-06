# backend/app/services/agents/monono_agent/tests/component/test_guardrail.py
import pytest
from typing import List, Dict, Any, Optional
import uuid

from app.services.agents.monono_agent.components.guardrail import (
    BaseGuardrail,
    MyCustomGuardrail, # MyCustomGuardrail をインポート
    GuardrailViolationError
)

# --- BaseGuardrail Tests ---

@pytest.mark.asyncio
async def test_base_guardrail_initialization():
    """BaseGuardrailの初期化テスト。"""
    config = {"some_key": "some_value"}
    guardrail = BaseGuardrail(config=config)
    assert guardrail.config == config

    guardrail_no_config = BaseGuardrail()
    assert guardrail_no_config.config == {}

@pytest.mark.asyncio
async def test_base_guardrail_check_input_default():
    """BaseGuardrail.check_inputのデフォルト動作テスト。"""
    guardrail = BaseGuardrail()
    sample_messages: List[Dict[str, Any]] = [{"role": "user", "content": "Hello"}]
    
    processed_messages = await guardrail.check_input(
        messages=sample_messages,
        agent_name="TestAgent",
        session_id=uuid.uuid4(),
        user_id="test_user"
    )
    assert processed_messages == sample_messages # デフォルトでは何も変更しない

@pytest.mark.asyncio
async def test_base_guardrail_check_output_default():
    """BaseGuardrail.check_outputのデフォルト動作テスト。"""
    guardrail = BaseGuardrail()
    sample_chunk: Dict[str, Any] = {"type": "delta", "data": {"content": "Response part."}}
    
    processed_chunk = await guardrail.check_output(
        response_chunk=sample_chunk,
        agent_name="TestAgent",
        session_id=uuid.uuid4(),
        user_id="test_user"
    )
    assert processed_chunk == sample_chunk # デフォルトでは何も変更しない

@pytest.mark.asyncio
async def test_base_guardrail_can_execute_tool_default():
    """BaseGuardrail.can_execute_toolのデフォルト動作テスト。"""
    guardrail = BaseGuardrail()
    
    can_execute = await guardrail.can_execute_tool(
        tool_name="sample_tool",
        tool_args={"arg1": "value1"},
        agent_name="TestAgent",
        session_id=uuid.uuid4(),
        user_id="test_user",
        tool_registry=None # tool_registryはOptionalなのでNoneでも可
    )
    assert can_execute is True # デフォルトでは常に許可

# --- MyCustomGuardrail Tests ---

@pytest.mark.asyncio
async def test_my_custom_guardrail_initialization():
    """MyCustomGuardrailの初期化と設定読み込みテスト。"""
    config = {"restricted_tools": ["tool1", "tool2"], "log_level": "debug"}
    custom_guardrail = MyCustomGuardrail(config=config)
    assert custom_guardrail.config == config
    assert custom_guardrail.restricted_tools == ["tool1", "tool2"]

    custom_guardrail_no_config = MyCustomGuardrail()
    assert custom_guardrail_no_config.restricted_tools == []


@pytest.mark.asyncio
async def test_my_custom_guardrail_check_input_violation():
    """MyCustomGuardrail.check_inputで違反が発生するケース。"""
    custom_guardrail = MyCustomGuardrail()
    messages_with_violation: List[Dict[str, Any]] = [
        {"role": "user", "content": "This is a normal message."},
        {"role": "user", "content": "This message contains the stupid word."}
    ]
    
    with pytest.raises(GuardrailViolationError) as excinfo:
        await custom_guardrail.check_input(messages=messages_with_violation)
    
    assert "Input message contains prohibited word: stupid" in str(excinfo.value)
    assert excinfo.value.details == {"message_index": 1}

@pytest.mark.asyncio
async def test_my_custom_guardrail_check_input_no_violation():
    """MyCustomGuardrail.check_inputで違反がないケース。"""
    custom_guardrail = MyCustomGuardrail()
    safe_messages: List[Dict[str, Any]] = [
        {"role": "user", "content": "This is a perfectly fine message."},
        {"role": "assistant", "content": "So is this."}
    ]
    
    processed_messages = await custom_guardrail.check_input(messages=safe_messages)
    assert processed_messages == safe_messages

@pytest.mark.asyncio
async def test_my_custom_guardrail_can_execute_tool_denied():
    """MyCustomGuardrail.can_execute_toolでツール実行が拒否されるケース。"""
    config = {"restricted_tools": ["super_admin_tool", "delete_everything_tool"]}
    custom_guardrail = MyCustomGuardrail(config=config)
    
    # 制限されたツールの実行
    can_execute_restricted = await custom_guardrail.can_execute_tool(
        tool_name="super_admin_tool",
        tool_args={},
    )
    assert can_execute_restricted is False
    
    can_execute_another_restricted = await custom_guardrail.can_execute_tool(
        tool_name="delete_everything_tool",
        tool_args={"confirm": "false"}, # 引数はチェックに影響しない設定
    )
    assert can_execute_another_restricted is False

@pytest.mark.asyncio
async def test_my_custom_guardrail_can_execute_tool_allowed():
    """MyCustomGuardrail.can_execute_toolでツール実行が許可されるケース。"""
    config = {"restricted_tools": ["super_admin_tool"]}
    custom_guardrail = MyCustomGuardrail(config=config)

    # 制限されていないツールの実行
    can_execute_allowed = await custom_guardrail.can_execute_tool(
        tool_name="normal_tool",
        tool_args={"param": "value"},
    )
    assert can_execute_allowed is True

# --- GuardrailViolationError Test ---

def test_guardrail_violation_error_creation():
    """GuardrailViolationErrorのメッセージと詳細のテスト。"""
    message = "Test violation"
    details = {"key": "value", "code": 123}
    
    error_with_details = GuardrailViolationError(message, details=details)
    assert str(error_with_details) == message
    assert error_with_details.details == details
    
    error_no_details = GuardrailViolationError(message)
    assert str(error_no_details) == message
    assert error_no_details.details == {} 