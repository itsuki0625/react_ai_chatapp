# backend/app/services/agents/monono_agent/tests/test_tool_registry.py

import pytest
from typing import Optional, List
from pydantic import BaseModel, Field

# テスト対象のモジュールをインポート
from app.services.agents.monono_agent.components.tool_registry import (
    ToolRegistry,
    ToolNotFoundError,
    ToolParameterError,
    ToolExecutionError,
)

# --- テスト用のサンプルツール関数 ---
def sample_tool_no_args():
    """引数なしのサンプルツールです。"""
    return "no_args_tool_executed"

def sample_tool_simple_args(name: str, age: int):
    """簡単な引数を持つサンプルツールです。"""
    return f"Hello {name}, you are {age} years old."

class ComplexToolArgs(BaseModel):
    items: List[str]
    count: int
    is_active: Optional[bool] = Field(default=True, description="アクティブかどうか")

def sample_tool_complex_args_schema(args: ComplexToolArgs):
    """Pydanticモデルを引数として受け取るサンプルツールです。"""
    return f"Received {args.count} items: {', '.join(args.items)}. Active: {args.is_active}"

def sample_tool_complex_args_type_hint(name: str, items: List[str], count: int = 0):
    """型ヒントで複雑な引数を持つサンプルツールです。"""
    return f"Name: {name}, Items: {items}, Count: {count}"

def sample_tool_raises_exception():
    """実行中に例外を発生させるサンプルツールです。"""
    raise ValueError("This tool intentionally raises an error.")

# --- テストクラス ---
class TestToolRegistry:

    @pytest.fixture
    def tool_registry(self) -> ToolRegistry:
        """テスト用のToolRegistryインスタンスを返すフィクスチャ。"""
        return ToolRegistry()

    def test_register_tool_no_args(self, tool_registry: ToolRegistry):
        """引数なしツールの登録と定義取得テスト。"""
        tool_registry.register_tool(sample_tool_no_args)
        definitions = tool_registry.get_tool_definitions()
        assert len(definitions) == 1
        func_def = definitions[0]["function"]
        assert func_def["name"] == "sample_tool_no_args"
        assert func_def["description"] == "引数なしのサンプルツールです。"
        assert func_def["parameters"] == {"type": "object", "properties": {}} # 引数なし

    def test_register_tool_simple_args(self, tool_registry: ToolRegistry):
        """単純な引数を持つツールの登録と定義取得テスト。"""
        tool_registry.register_tool(sample_tool_simple_args)
        definitions = tool_registry.get_tool_definitions()
        assert len(definitions) == 1
        func_def = definitions[0]["function"]
        assert func_def["name"] == "sample_tool_simple_args"
        assert "name" in func_def["parameters"]["properties"]
        assert "age" in func_def["parameters"]["properties"]
        assert func_def["parameters"]["properties"]["name"]["type"] == "string"
        assert func_def["parameters"]["properties"]["age"]["type"] == "integer"
        assert "name" in func_def["parameters"]["required"]
        assert "age" in func_def["parameters"]["required"]

    def test_register_tool_with_explicit_schema(self, tool_registry: ToolRegistry):
        """明示的なPydanticスキーマを持つツールの登録テスト。"""
        tool_registry.register_tool(sample_tool_complex_args_schema, schema=ComplexToolArgs)
        definitions = tool_registry.get_tool_definitions()
        assert len(definitions) == 1
        func_def = definitions[0]["function"]
        assert func_def["name"] == "sample_tool_complex_args_schema" # 関数名が使われる
        # スキーマのプロパティをチェック (ComplexToolArgs に基づく)
        assert "items" in func_def["parameters"]["properties"]
        assert func_def["parameters"]["properties"]["items"]["type"] == "array"
        assert "count" in func_def["parameters"]["properties"]
        assert func_def["parameters"]["properties"]["is_active"]["description"] == "アクティブかどうか"


    def test_parse_arguments_valid(self, tool_registry: ToolRegistry):
        """引数の正常なパースとバリデーションテスト。"""
        tool_registry.register_tool(sample_tool_simple_args)
        args_str = '{"name": "Alice", "age": 30}'
        parsed_args = tool_registry.parse_arguments("sample_tool_simple_args", args_str)
        assert parsed_args == {"name": "Alice", "age": 30}

    def test_parse_arguments_invalid_json(self, tool_registry: ToolRegistry):
        """不正なJSON文字列での引数パースエラーテスト。"""
        tool_registry.register_tool(sample_tool_simple_args)
        args_str = '{"name": "Alice", "age": 30' # JSONが不完全
        with pytest.raises(ToolParameterError, match="Invalid JSON"):
            tool_registry.parse_arguments("sample_tool_simple_args", args_str)

    def test_parse_arguments_validation_error(self, tool_registry: ToolRegistry):
        """Pydanticバリデーションエラーテスト。"""
        tool_registry.register_tool(sample_tool_simple_args)
        args_str = '{"name": "Alice", "age": "thirty"}' # ageが文字列
        with pytest.raises(ToolParameterError, match="Argument validation failed"):
            tool_registry.parse_arguments("sample_tool_simple_args", args_str)
    
    def test_parse_arguments_missing_required(self, tool_registry: ToolRegistry):
        """必須引数欠如によるバリデーションエラーテスト。"""
        tool_registry.register_tool(sample_tool_simple_args)
        args_str = '{"name": "Alice"}' # age がない
        with pytest.raises(ToolParameterError, match="Argument validation failed"):
            tool_registry.parse_arguments("sample_tool_simple_args", args_str)

    def test_parse_arguments_no_args_tool_with_args(self, tool_registry: ToolRegistry):
        """引数なしツールに引数が渡された場合のエラーテスト。"""
        tool_registry.register_tool(sample_tool_no_args)
        args_str = '{"unexpected": "value"}'
        with pytest.raises(ToolParameterError, match="expects no arguments"):
            tool_registry.parse_arguments("sample_tool_no_args", args_str)

    def test_execute_tool_no_args(self, tool_registry: ToolRegistry):
        """引数なしツールの正常実行テスト。"""
        tool_registry.register_tool(sample_tool_no_args)
        result = tool_registry.execute_tool("sample_tool_no_args", {})
        assert result == "no_args_tool_executed"

    def test_execute_tool_simple_args(self, tool_registry: ToolRegistry):
        """引数ありツールの正常実行テスト。"""
        tool_registry.register_tool(sample_tool_simple_args)
        # parse_arguments を経由した引数を渡す想定
        parsed_args = {"name": "Bob", "age": 25}
        result = tool_registry.execute_tool("sample_tool_simple_args", parsed_args)
        assert result == "Hello Bob, you are 25 years old."

    def test_execute_tool_not_found(self, tool_registry: ToolRegistry):
        """存在しないツールの実行エラーテスト。"""
        with pytest.raises(ToolNotFoundError):
            tool_registry.execute_tool("non_existent_tool", {})

    def test_execute_tool_raises_exception(self, tool_registry: ToolRegistry):
        """ツール実行中の例外発生テスト。"""
        tool_registry.register_tool(sample_tool_raises_exception)
        with pytest.raises(ToolExecutionError, match="Error during execution"):
            tool_registry.execute_tool("sample_tool_raises_exception", {})

    def test_register_and_get_schema_for_complex_type_hints(self, tool_registry: ToolRegistry):
        """複雑な型ヒントを持つツールのスキーマ生成テスト。"""
        tool_registry.register_tool(sample_tool_complex_args_type_hint)
        definitions = tool_registry.get_tool_definitions()
        assert len(definitions) == 1
        func_def = definitions[0]["function"]
        assert func_def["name"] == "sample_tool_complex_args_type_hint"
        
        params = func_def["parameters"]["properties"]
        assert params["name"]["type"] == "string"
        assert params["items"]["type"] == "array"
        assert params["items"]["items"]["type"] == "string" # List[str] の中身もstring
        assert params["count"]["type"] == "integer"
        assert params["count"]["default"] == 0 # デフォルト値も反映される
        
        assert "name" in func_def["parameters"]["required"] # nameは必須
        assert "items" in func_def["parameters"]["required"] # itemsも必須 (デフォルト値なし)
        assert "count" not in func_def["parameters"].get("required", []) # countはデフォルト値があるので必須ではない

    def test_tool_with_default_values_parsing_and_execution(self, tool_registry: ToolRegistry):
        """デフォルト値を持つ引数のパースと実行テスト。"""
        tool_registry.register_tool(sample_tool_complex_args_type_hint)
        
        # count を省略して呼び出す
        args_str_partial = '{"name": "Charlie", "items": ["apple", "banana"]}'
        parsed_args_partial = tool_registry.parse_arguments("sample_tool_complex_args_type_hint", args_str_partial)
        assert parsed_args_partial == {"name": "Charlie", "items": ["apple", "banana"], "count": 0} # デフォルト値が補完される
        result_partial = tool_registry.execute_tool("sample_tool_complex_args_type_hint", parsed_args_partial)
        assert result_partial == "Name: Charlie, Items: ['apple', 'banana'], Count: 0"

        # count を明示的に指定して呼び出す
        args_str_full = '{"name": "David", "items": ["orange"], "count": 5}'
        parsed_args_full = tool_registry.parse_arguments("sample_tool_complex_args_type_hint", args_str_full)
        assert parsed_args_full == {"name": "David", "items": ["orange"], "count": 5}
        result_full = tool_registry.execute_tool("sample_tool_complex_args_type_hint", parsed_args_full)
        assert result_full == "Name: David, Items: ['orange'], Count: 5" 