import pytest
from typing import Dict, Any, List, Optional

# テスト対象のOpenAIAdapterをインポート
# パスはプロジェクト構造に合わせて調整してください
from app.services.agents.monono_agent.llm_adapters.openai_adapter import OpenAIAdapter

# --- モックデータの準備 ---
# OpenAI APIからのストリーミングチャンクのサンプル

def create_openai_delta_chunk(content: Optional[str] = None, tool_calls: Optional[List[Dict[str, Any]]] = None, finish_reason: Optional[str] = None) -> Dict[str, Any]:
    """OpenAI形式のストリーミングチャンクを生成するヘルパー関数"""
    delta: Dict[str, Any] = {}
    if content is not None:
        delta["content"] = content
    if tool_calls is not None:
        delta["tool_calls"] = tool_calls
    
    choice = {"delta": delta}
    if finish_reason:
        choice["finish_reason"] = finish_reason
    
    return {
        "id": "chatcmpl-xxxxxxxxxxxxxxxxxxxxxxx",
        "object": "chat.completion.chunk",
        "created": 1700000000,
        "model": "gpt-4o-test",
        "choices": [choice]
    }

# --- テストケース ---

@pytest.fixture
def openai_adapter() -> OpenAIAdapter:
    """OpenAIAdapterのインスタンスを生成するフィクスチャ"""
    # APIキーはモックテストなので不要だが、初期化自体は行う
    return OpenAIAdapter(model_name="gpt-4o-test", api_key="fake_api_key")

def test_parse_text_delta(openai_adapter: OpenAIAdapter):
    """テキストデルタチャンクのパーステスト"""
    raw_chunk = create_openai_delta_chunk(content="Hello")
    accumulated_tool_calls: Dict[int, Dict[str, Any]] = {}
    tool_call_started_flags: Dict[int, bool] = {}
    
    parsed_chunk = openai_adapter.parse_llm_response_chunk(raw_chunk, accumulated_tool_calls, tool_call_started_flags)
    
    assert parsed_chunk is not None
    assert parsed_chunk.get("type") == "delta"
    assert parsed_chunk.get("content") == "Hello"

def test_parse_tool_call_start(openai_adapter: OpenAIAdapter):
    """ツールコール開始チャンクのパーステスト"""
    tool_call_delta = [
        {
            "index": 0,
            "id": "call_abc123",
            "type": "function",
            "function": {"name": "get_weather", "arguments": ""}
        }
    ]
    raw_chunk = create_openai_delta_chunk(tool_calls=tool_call_delta)
    accumulated_tool_calls: Dict[int, Dict[str, Any]] = {}
    tool_call_started_flags: Dict[int, bool] = {}

    parsed_chunk = openai_adapter.parse_llm_response_chunk(raw_chunk, accumulated_tool_calls, tool_call_started_flags)

    assert parsed_chunk is not None
    assert parsed_chunk.get("type") == "tool_call_start"
    assert parsed_chunk.get("id") == "call_abc123"
    assert parsed_chunk.get("name") == "get_weather"
    assert parsed_chunk.get("input_so_far") == ""
    assert 0 in accumulated_tool_calls
    assert accumulated_tool_calls[0]["id"] == "call_abc123"
    assert accumulated_tool_calls[0]["function"]["name"] == "get_weather"
    assert tool_call_started_flags[0] is True

def test_parse_tool_call_argument_delta(openai_adapter: OpenAIAdapter):
    """ツールコール引数デルタチャンクのパーステスト"""
    # 先にtool_call_startが処理されている状態を模倣
    accumulated_tool_calls: Dict[int, Dict[str, Any]] = {
        0: {"id": "call_xyz456", "type": "function", "function": {"name": "search_web", "arguments": "{\"query\":\""}}}
    tool_call_started_flags: Dict[int, bool] = {0: True}

    tool_call_delta = [
        {
            "index": 0,
            # "id": "call_xyz456", # idは最初のチャンクで来る想定だが、なくてもindexで引ける
            "function": {"arguments": "AI tools\"}"}
        }
    ]
    raw_chunk = create_openai_delta_chunk(tool_calls=tool_call_delta)
    
    parsed_chunk = openai_adapter.parse_llm_response_chunk(raw_chunk, accumulated_tool_calls, tool_call_started_flags)

    assert parsed_chunk is not None
    assert parsed_chunk.get("type") == "tool_call_delta"
    assert parsed_chunk.get("id") == "call_xyz456"
    assert parsed_chunk.get("input_delta") == "AI tools\"}"
    assert accumulated_tool_calls[0]["function"]["arguments"] == "{\"query\":\"AI tools\"}"

def test_parse_tool_call_finish_single(openai_adapter: OpenAIAdapter):
    """単一のツールコール完了チャンクのパーステスト"""
    accumulated_tool_calls: Dict[int, Dict[str, Any]] = {
        0: {"id": "call_end789", "type": "function", "function": {"name": "run_code", "arguments": "{\"code\":\"print('done')\"}"}}
    }
    tool_call_started_flags: Dict[int, bool] = {0: True}
    
    raw_chunk = create_openai_delta_chunk(finish_reason="tool_calls")
    
    parsed_chunk = openai_adapter.parse_llm_response_chunk(raw_chunk, accumulated_tool_calls, tool_call_started_flags)

    assert parsed_chunk is not None
    assert parsed_chunk.get("type") == "multi_chunk"
    assert isinstance(parsed_chunk.get("chunks"), list)
    chunks_list = parsed_chunk.get("chunks", [])
    assert len(chunks_list) == 1
    
    end_chunk = chunks_list[0]
    assert end_chunk.get("type") == "tool_call_end"
    assert end_chunk.get("id") == "call_end789"
    assert end_chunk.get("name") == "run_code"
    assert end_chunk.get("arguments") == "{\"code\":\"print('done')\"}"
    assert not accumulated_tool_calls # 完了後はクリアされる
    assert not tool_call_started_flags

def test_parse_tool_call_finish_multiple(openai_adapter: OpenAIAdapter):
    """複数のツールコール完了チャンクのパーステスト"""
    accumulated_tool_calls: Dict[int, Dict[str, Any]] = {
        0: {"id": "call_multi_A", "type": "function", "function": {"name": "tool_A", "arguments": "{}"}},
        1: {"id": "call_multi_B", "type": "function", "function": {"name": "tool_B", "arguments": "{\"param\":1}"}}
    }
    tool_call_started_flags: Dict[int, bool] = {0: True, 1: True}
    
    raw_chunk = create_openai_delta_chunk(finish_reason="tool_calls")
    
    parsed_chunk = openai_adapter.parse_llm_response_chunk(raw_chunk, accumulated_tool_calls, tool_call_started_flags)

    assert parsed_chunk is not None
    assert parsed_chunk.get("type") == "multi_chunk"
    chunks_list = parsed_chunk.get("chunks", [])
    assert len(chunks_list) == 2

    assert chunks_list[0].get("type") == "tool_call_end"
    assert chunks_list[0].get("id") == "call_multi_A"
    assert chunks_list[1].get("type") == "tool_call_end"
    assert chunks_list[1].get("id") == "call_multi_B"
    assert not accumulated_tool_calls
    assert not tool_call_started_flags


def test_parse_finish_reason_stop(openai_adapter: OpenAIAdapter):
    """finish_reason 'stop' のパーステスト"""
    raw_chunk = create_openai_delta_chunk(finish_reason="stop")
    accumulated_tool_calls: Dict[int, Dict[str, Any]] = {}
    tool_call_started_flags: Dict[int, bool] = {}

    parsed_chunk = openai_adapter.parse_llm_response_chunk(raw_chunk, accumulated_tool_calls, tool_call_started_flags)
    
    assert parsed_chunk is not None
    assert parsed_chunk.get("type") == "meta"
    assert parsed_chunk.get("finish_reason") == "stop"

def test_parse_finish_reason_length(openai_adapter: OpenAIAdapter):
    """finish_reason 'length' のパーステスト"""
    raw_chunk = create_openai_delta_chunk(finish_reason="length")
    accumulated_tool_calls: Dict[int, Dict[str, Any]] = {}
    tool_call_started_flags: Dict[int, bool] = {}
    
    parsed_chunk = openai_adapter.parse_llm_response_chunk(raw_chunk, accumulated_tool_calls, tool_call_started_flags)

    assert parsed_chunk is not None
    assert parsed_chunk.get("type") == "meta"
    assert parsed_chunk.get("finish_reason") == "length"
    assert "message" in parsed_chunk # lengthの場合はメッセージが含まれることを期待

# TODO:
# - ツールコールのIDや名前が途中で変わるような不正なケースのテスト
# - accumulated_tool_calls や tool_call_started_flags が空の場合の finish_reason="tool_calls" のテスト
# - IDやインデックスがない不正な tool_calls チャンクのテスト
# - _stream_chat_completion メソッド自体のテスト (モックした client.chat.completions.create を使用)
# - format_tool_call_response メソッドのテスト
# - chat_completion メソッド (非ストリーミング) のテスト
