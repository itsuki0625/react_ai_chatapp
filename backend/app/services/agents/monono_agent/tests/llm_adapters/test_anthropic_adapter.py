import pytest
from typing import Dict, Any, List, Optional, Union

# テスト対象のAnthropicAdapterをインポート
from app.services.agents.monono_agent.llm_adapters.anthropic_adapter import AnthropicAdapter

# --- モックデータの準備 ---
# Anthropic APIからのストリーミングイベントのサンプル

def create_anthropic_event(event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Anthropic形式のストリーミングイベントを生成するヘルパー関数"""
    # 実際のイベント構造はもっと複雑だが、テストに必要な部分を簡略化
    event = {"type": event_type}
    if event_type == "message_start":
        event["message"] = data # message: {"id": ..., "usage": ...}
    elif event_type == "content_block_start":
        event["index"] = data.get("index")
        event["content_block"] = data.get("content_block") # content_block: {"type": "text" or "tool_use", "id": ..., "name": ...}
    elif event_type == "content_block_delta":
        event["index"] = data.get("index")
        event["delta"] = data.get("delta") # delta: {"type": "text_delta", "text": ...} or {"type": "input_json_delta", "partial_json": ...}
    elif event_type == "content_block_stop":
        event["index"] = data.get("index")
    elif event_type == "message_delta":
        event["delta"] = data.get("delta") # delta: {"stop_reason": ..., "stop_sequence": ...}
        event["usage"] = data.get("usage") # usage: {"output_tokens": ...} (message_deltaではinput_tokensは通常ない)
    elif event_type == "message_stop":
        pass # このイベントはtypeのみ
    elif event_type == "error":
        event["error"] = data # error: {"type": ..., "message": ...}
    return event

# --- テストケース ---

@pytest.fixture
def anthropic_adapter() -> AnthropicAdapter:
    """AnthropicAdapterのインスタンスを生成するフィクスチャ"""
    return AnthropicAdapter(model_name="claude-3-opus-test", api_key="fake_anthropic_key")

def test_parse_text_delta(anthropic_adapter: AnthropicAdapter):
    """text_delta イベントのパーステスト"""
    event_data = create_anthropic_event("content_block_delta", {
        "index": 0,
        "delta": {"type": "text_delta", "text": "Hello "}
    })
    accumulated_tool_uses: Dict[int, Dict[str, Any]] = {}
    tool_call_started_flags: Dict[int, bool] = {}
    
    parsed_chunk = anthropic_adapter.parse_llm_response_chunk(event_data, accumulated_tool_uses, tool_call_started_flags)
    
    assert parsed_chunk is not None
    if isinstance(parsed_chunk, list): # 複数のチャンクが返る可能性がある
        assert len(parsed_chunk) == 1
        parsed_chunk = parsed_chunk[0]

    assert parsed_chunk.get("type") == "delta"
    assert parsed_chunk.get("content") == "Hello "

def test_parse_tool_use_start_and_input_delta(anthropic_adapter: AnthropicAdapter):
    """tool_use 開始 (content_block_start) と input_json_delta のパーステスト"""
    accumulated_tool_uses: Dict[int, Dict[str, Any]] = {}
    tool_call_started_flags: Dict[int, bool] = {}

    # 1. content_block_start (tool_use)
    tool_use_start_event = create_anthropic_event("content_block_start", {
        "index": 0,
        "content_block": {"type": "tool_use", "id": "toolu_abc123", "name": "get_stock_price"}
    })
    parsed_chunks_start = anthropic_adapter.parse_llm_response_chunk(tool_use_start_event, accumulated_tool_uses, tool_call_started_flags)
    
    assert parsed_chunks_start is not None
    assert isinstance(parsed_chunks_start, list)
    assert len(parsed_chunks_start) == 1
    start_chunk = parsed_chunks_start[0]

    assert start_chunk.get("type") == "tool_call_start"
    assert start_chunk.get("id") == "toolu_abc123"
    assert start_chunk.get("name") == "get_stock_price"
    assert start_chunk.get("input_so_far") == ""
    assert 0 in accumulated_tool_uses
    assert accumulated_tool_uses[0]["id"] == "toolu_abc123"
    assert accumulated_tool_uses[0]["name"] == "get_stock_price"
    assert tool_call_started_flags[0] is True

    # 2. content_block_delta (input_json_delta)
    input_delta_event = create_anthropic_event("content_block_delta", {
        "index": 0,
        "delta": {"type": "input_json_delta", "partial_json": "{\"symbol\":\""}
    })
    parsed_chunks_delta1 = anthropic_adapter.parse_llm_response_chunk(input_delta_event, accumulated_tool_uses, tool_call_started_flags)
    
    assert parsed_chunks_delta1 is not None
    assert isinstance(parsed_chunks_delta1, list)
    assert len(parsed_chunks_delta1) == 1
    delta_chunk1 = parsed_chunks_delta1[0]

    assert delta_chunk1.get("type") == "tool_call_delta"
    assert delta_chunk1.get("id") == "toolu_abc123"
    assert delta_chunk1.get("input_delta") == "{\"symbol\":\""
    assert accumulated_tool_uses[0]["input"] == "{\"symbol\":\""

    # 3. 続きの input_json_delta
    input_delta_event_2 = create_anthropic_event("content_block_delta", {
        "index": 0,
        "delta": {"type": "input_json_delta", "partial_json": "NVDA\"}"}
    })
    parsed_chunks_delta2 = anthropic_adapter.parse_llm_response_chunk(input_delta_event_2, accumulated_tool_uses, tool_call_started_flags)

    assert parsed_chunks_delta2 is not None
    assert isinstance(parsed_chunks_delta2, list)
    assert len(parsed_chunks_delta2) == 1
    delta_chunk2 = parsed_chunks_delta2[0]

    assert delta_chunk2.get("type") == "tool_call_delta"
    assert delta_chunk2.get("input_delta") == "NVDA\"}"
    assert accumulated_tool_uses[0]["input"] == "{\"symbol\":\"NVDA\"}"


def test_parse_message_delta_tool_use_finish(anthropic_adapter: AnthropicAdapter):
    """message_delta で tool_use 完了を通知するイベントのパーステスト"""
    accumulated_tool_uses: Dict[int, Dict[str, Any]] = {
        0: {"id": "toolu_xyz456", "name": "calculate_sum", "input": "{\"numbers\":[1,2,3]}"}
    }
    tool_call_started_flags: Dict[int, bool] = {0: True}

    finish_event = create_anthropic_event("message_delta", {
        "delta": {"stop_reason": "tool_use", "stop_sequence": None},
        "usage": {"output_tokens": 10} # このusageはmessage_deltaイベントの一部
    })
    
    parsed_result = anthropic_adapter.parse_llm_response_chunk(finish_event, accumulated_tool_uses, tool_call_started_flags)

    assert parsed_result is not None
    assert isinstance(parsed_result, dict) # multi_chunkでラップされる想定
    assert parsed_result.get("type") == "multi_chunk"
    
    chunks_list = parsed_result.get("chunks", [])
    assert len(chunks_list) == 1 # tool_call_end のみのはず (usageは別途処理される)
    
    end_chunk = chunks_list[0]
    assert end_chunk.get("type") == "tool_call_end"
    assert end_chunk.get("id") == "toolu_xyz456"
    assert end_chunk.get("name") == "calculate_sum"
    assert end_chunk.get("arguments") == "{\"numbers\":[1,2,3]}"
    assert not accumulated_tool_uses
    assert not tool_call_started_flags

def test_parse_message_delta_stop_turn(anthropic_adapter: AnthropicAdapter):
    """message_delta で通常のターン終了 (end_turn) を通知するイベントのパーステスト"""
    event_data = create_anthropic_event("message_delta", {
        "delta": {"stop_reason": "end_turn", "stop_sequence": None},
        "usage": {"output_tokens": 50}
    })
    accumulated_tool_uses: Dict[int, Dict[str, Any]] = {}
    tool_call_started_flags: Dict[int, bool] = {}

    parsed_chunk = anthropic_adapter.parse_llm_response_chunk(event_data, accumulated_tool_uses, tool_call_started_flags)

    assert parsed_chunk is not None
    if isinstance(parsed_chunk, list):
        assert len(parsed_chunk) == 1
        parsed_chunk = parsed_chunk[0]
        
    assert parsed_chunk.get("type") == "meta"
    assert parsed_chunk.get("finish_reason") == "end_turn"

def test_parse_message_stop(anthropic_adapter: AnthropicAdapter):
    """message_stop イベントのパーステスト"""
    event_data = create_anthropic_event("message_stop", {})
    accumulated_tool_uses: Dict[int, Dict[str, Any]] = {}
    tool_call_started_flags: Dict[int, bool] = {}

    parsed_chunk = anthropic_adapter.parse_llm_response_chunk(event_data, accumulated_tool_uses, tool_call_started_flags)
    
    assert parsed_chunk is not None
    if isinstance(parsed_chunk, list):
        assert len(parsed_chunk) == 1
        parsed_chunk = parsed_chunk[0]

    assert parsed_chunk.get("type") == "meta"
    assert parsed_chunk.get("finish_reason") == "stream_end"

def test_parse_error_event(anthropic_adapter: AnthropicAdapter):
    """error イベントのパーステスト"""
    error_payload = {"type": "overloaded_error", "message": "Anthropic's API is temporarily overloaded."}
    event_data = create_anthropic_event("error", error_payload)
    accumulated_tool_uses: Dict[int, Dict[str, Any]] = {}
    tool_call_started_flags: Dict[int, bool] = {}

    parsed_chunk = anthropic_adapter.parse_llm_response_chunk(event_data, accumulated_tool_uses, tool_call_started_flags)

    assert parsed_chunk is not None
    if isinstance(parsed_chunk, list):
        assert len(parsed_chunk) == 1
        parsed_chunk = parsed_chunk[0]

    assert parsed_chunk.get("type") == "error"
    assert parsed_chunk.get("message") == "Anthropic's API is temporarily overloaded."
    assert parsed_chunk.get("code") == "overloaded_error"


# TODO:
# - 複数のツールコールが混在するケース
# - content_block_stop イベントのハンドリング (現状は何もしないが、それで正しいか確認)
# - message_start イベントのハンドリング (現状はNoneを返すが、usage情報をここで処理するならテスト追加)
# - _stream_chat_completion メソッド自体のテスト (モックした client.messages.stream を使用)
# - format_tool_call_response メソッドのテスト
# - chat_completion メソッド (非ストリーミング) のテスト 