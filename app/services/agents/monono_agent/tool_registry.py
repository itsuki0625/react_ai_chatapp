from typing import Callable, List, Dict, Any, Optional
import inspect
import json
from pydantic import BaseModel, create_model, ValidationError
from docstring_parser import parse

class ToolRegistry:
    def __init__(self, tools: Optional[List[Callable]] = None):
        self._tools: Dict[str, Callable] = {}
        self._tool_schemas: Dict[str, Dict[str, Any]] = {}
        if tools:
            for tool in tools:
                self.register_tool(tool)

    def register_tool(self, tool_func: Callable):
        tool_name = tool_func.__name__
        if tool_name in self._tools:
            # 実際のアプリケーションでは、より詳細なエラーハンドリングやロギングを行う
            print(f"Warning: Tool '{tool_name}' is already registered. Overwriting.")

        self._tools[tool_name] = tool_func
        self._tool_schemas[tool_name] = self._generate_tool_schema(tool_func)

    def _generate_tool_schema(self, tool_func: Callable) -> Dict[str, Any]:
        """
        関数からLLMフレンドリーなスキーマを生成します。
        OpenAIのFunction Calling/Tool Callingの形式に似たものを目指します。
        """
        tool_name = tool_func.__name__
        docstring = inspect.getdoc(tool_func)
        parsed_docstring = parse(docstring) if docstring else None

        description = parsed_docstring.short_description if parsed_docstring and parsed_docstring.short_description else ""
        if parsed_docstring and parsed_docstring.long_description:
            description += "\n" + parsed_docstring.long_description

        parameters_schema = {"type": "object", "properties": {}, "required": []}
        
        sig = inspect.signature(tool_func)
        param_descriptions = {p.arg_name: p.description for p in parsed_docstring.params} if parsed_docstring else {}

        for name, param in sig.parameters.items():
            if name == "self" or name == "cls":  # メソッドの第1引数はスキップ
                continue

            param_type = param.annotation
            
            # Pydanticモデルの場合、そのスキーマを利用
            if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                # TODO: Pydanticモデルのネストされたスキーマを適切に処理する
                # 現在はトップレベルのプロパティのみを想定
                model_schema = param_type.model_json_schema()
                # 'properties'と'required'をparameters_schemaにマージ
                # ここでは簡略化のため、引数が単一のPydanticモデルであることを想定
                # 複数の引数や、Pydanticモデル以外の型との混在はより複雑な処理が必要
                if 'properties' in model_schema:
                    parameters_schema["properties"].update(model_schema.get('properties', {}))
                if 'required' in model_schema:
                    parameters_schema["required"].extend(model_schema.get('required', []))
                # TODO: model_schemaのdescriptionをどう扱うか
                # この引数に対するdescriptionはparam_descriptions.get(name)で取れる
                # しかし、Pydanticモデル全体のdescriptionとの兼ね合い
                if name not in parameters_schema["properties"] and name not in sig.parameters:
                    # Pydanticモデル自体を引数とするケース
                    # (例: def my_tool(config: MyModel))
                    # この場合、LLMはconfigという名前のオブジェクトを渡す必要がある
                    # しかし、OpenAIのFunction Callingでは、モデルのフィールドを展開して渡す方が一般的
                    # ここは設計の選択肢がある。今回はPydanticモデルのフィールドを展開する方向で進める。
                    # 展開する場合、tool_funcの呼び出し時にどう再構築するかが課題。
                    # 一旦、Pydanticモデルは単一引数で、そのフィールドが直接展開されると仮定してスキーマを作る
                    # (つまり、Pydanticモデルの引数名はスキーマには現れない)
                    # ただし、これは関数のシグネチャとLLMへの提示方法に不整合を生む可能性があるため注意。
                    #
                    # より一般的なのは、関数側で `def my_tool(arg1: str, arg2: int)` のように個別の引数を定義し、
                    # LLMにはその引数リストを提示する。
                    # もしPydanticモデルを使いたいなら、ツール実行時に内部でモデルに変換する。
                    #
                    # ここでは、inspect.signatureに基づいて個々の引数を処理する。
                    # Pydanticモデル型アノテーションはその引数の型情報として使う。
                    pass


            # 通常の型アノテーションの場合
            type_name = "string" # デフォルト
            if param_type == str:
                type_name = "string"
            elif param_type == int:
                type_name = "integer"
            elif param_type == float:
                type_name = "number"
            elif param_type == bool:
                type_name = "boolean"
            elif param_type == list or param_type == List: # TODO: List[<type>] の内部型
                type_name = "array"
                # items_schema = {"type": "string"} # デフォルトはstringの配列
                # if hasattr(param_type, '__args__') and param_type.__args__:
                #     # TODO: List[int] などを正しく処理する
                #     pass
                # parameters_schema["properties"][name]["items"] = items_schema
            elif param_type == dict or param_type == Dict: # TODO: Dict[<key_type>, <value_type>]
                type_name = "object"
            elif inspect.isclass(param_type) and issubclass(param_type, BaseModel):
                # Pydanticモデルが引数の型として指定されている場合
                model_schema = param_type.model_json_schema()
                parameters_schema["properties"][name] = {
                    "type": "object", # Pydanticモデルはオブジェクトとして表現
                    "properties": model_schema.get("properties", {}),
                    "required": model_schema.get("required", []),
                    "description": param_descriptions.get(name, model_schema.get("description", ""))
                }
            else: # 未知の型やAnyの場合
                 parameters_schema["properties"][name] = {"description": param_descriptions.get(name, "")}
                 # typeを指定しない、または"any"のような型を許容するかどうか
                 # OpenAIは型指定を推奨している

            if name not in parameters_schema["properties"]: # Pydanticモデルでなければ個別に設定
                parameters_schema["properties"][name] = {"type": type_name, "description": param_descriptions.get(name, "")}

            if param.default == inspect.Parameter.empty:
                parameters_schema["required"].append(name)

        return {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": description,
                "parameters": parameters_schema,
            },
        }

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return list(self._tool_schemas.values())

    def get_tool(self, tool_name: str) -> Optional[Callable]:
        return self._tools.get(tool_name)

    def parse_arguments(self, tool_name: str, arguments_json_string: str) -> Dict[str, Any]:
        if tool_name not in self._tool_schemas:
            raise ValueError(f"Tool '{tool_name}' not found.")

        tool_func = self._tools[tool_name]
        sig = inspect.signature(tool_func)
        
        # LLMが生成した引数 (JSON文字列)
        try:
            raw_arguments = json.loads(arguments_json_string)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON arguments for tool '{tool_name}': {e}")

        # Pydanticモデルを使用してバリデーションと型変換を行うための動的モデルを作成
        # ここでは、関数の各パラメータに対応するフィールドを持つPydanticモデルを動的に作る
        fields = {}
        for name, param in sig.parameters.items():
            if name == "self" or name == "cls":
                continue
            
            param_type = param.annotation if param.annotation != inspect.Parameter.empty else Any
            default_value = param.default if param.default != inspect.Parameter.empty else ...
            
            # Pydanticモデルが直接引数の型として指定されている場合、そのモデルをそのまま使う
            # ただし、LLMが渡す引数は展開された形になることが多い。
            # 例: def func(user_info: UserPydanticModel)
            # LLMは {"user_info": {"name": "John", "age": 30}} を渡す
            #
            # ここでの実装は、LLMが引数をフラットに渡すことを想定
            # 例: def func(name: str, age: int)
            # LLMは {"name": "John", "age": 30} を渡す
            #
            # もし関数が def func(user_data: UserDataModel) のように単一のPydanticモデル引数を期待し、
            # LLMが {"name": "John", "age": 30} のようにフィールドを直接渡してきた場合、
            # raw_arguments を UserDataModel(**raw_arguments) のように変換する必要がある。
            # スキーマ生成との整合性が重要。現在のスキーマ生成は個々の引数を展開している。

            fields[name] = (param_type, default_value)

        # fieldsが空の場合は、引数なしのツールなので、バリデーションモデルは不要
        if not fields:
            if raw_arguments: # 引数なしのツールに引数が渡された
                 raise ValueError(f"Tool '{tool_name}' expects no arguments, but received: {raw_arguments}")
            return {}

        # 動的にバリデーション用のPydanticモデルを作成
        ValidationModel = create_model(
            f'{tool_name}Arguments',
            **fields,
            __config__=None, # 必要であればBaseConfigなどを指定
        )
        
        try:
            validated_args = ValidationModel(**raw_arguments)
            return validated_args.model_dump()
        except ValidationError as e:
            # エラーメッセージをLLMにも分かりやすい形に整形する工夫も可能
            raise ValueError(f"Argument validation failed for tool '{tool_name}':\n{e}")


    async def execute_tool(
        self, 
        tool_name: str, 
        arguments_json_string: str,
        # TODO: セッションIDやユーザー情報など、ツール実行に必要なコンテキスト情報を渡せるようにする
        # agent_context: Optional[Dict[str, Any]] = None 
    ) -> Any: # 実際にはツール実行結果の型。シリアライズ可能なものが望ましい
        if tool_name not in self._tools:
            raise ValueError(f"Tool '{tool_name}' not found.")

        try:
            parsed_args = self.parse_arguments(tool_name, arguments_json_string)
        except ValueError as e: # パースやバリデーションエラー
            # エラーを構造化して返すことも検討 (LLMが解釈しやすいように)
            return {"error": str(e), "tool_name": tool_name, "status": "argument_error"}

        tool_func = self._tools[tool_name]
        
        # ツールが非同期関数の場合は await する
        if inspect.iscoroutinefunction(tool_func):
            try:
                # ここで agent_context のようなものを渡す場合、tool_func のシグネチャと合わせる必要がある
                result = await tool_func(**parsed_args)
            except Exception as e:
                # ツール実行中の予期せぬエラー
                # より詳細なエラーレポートが必要
                # logging.exception(f"Error executing tool '{tool_name}'")
                return {"error": f"Execution error in '{tool_name}': {type(e).__name__} - {str(e)}", "status": "execution_error"}
        else:
            try:
                result = tool_func(**parsed_args)
            except Exception as e:
                return {"error": f"Execution error in '{tool_name}': {type(e).__name__} - {str(e)}", "status": "execution_error"}
        
        # ツール結果がPydanticモデルの場合、辞書に変換 (LLMに返すため)
        if isinstance(result, BaseModel):
            return result.model_dump()
        
        # TODO: 実行結果のシリアライズ処理の検討
        # (例: datetimeオブジェクトをISO文字列に変換するなど)
        # ここでは単純にそのまま返す
        return result

# --- Example Usage (テスト用) ---
if __name__ == '__main__':
    class SearchToolParams(BaseModel):
        query: str
        limit: Optional[int] = 10
        # category: str = Field(description="The category to search in") # Fieldは不要でした

    def search_online(params: SearchToolParams):
        """
        指定されたクエリでオンライン検索を実行します。

        オンライン上の情報を幅広く検索し、関連性の高い結果を返します。
        Args:
            params: 検索クエリとオプションのパラメータ。
        """
        print(f"Searching online for: '{params.query}' with limit {params.limit}")
        # ここで実際の検索処理を行う
        return {"results": [{"title": "Result 1", "snippet": "..."}], "query_used": params.query}

    def get_weather(location: str, unit: str = "celsius"):
        """
        指定された場所の現在の天気を取得します。

        Args:
            location: 天気を知りたい都市名 (例: "Tokyo, JP")。
            unit: 温度の単位 ("celsius" または "fahrenheit")。
        """
        print(f"Getting weather for {location} in {unit}")
        if "tokyo" in location.lower():
            return {"temperature": "15", "unit": unit, "condition": "Cloudy"}
        else:
            return {"temperature": "20", "unit": unit, "condition": "Sunny"}

    def no_args_tool():
        """引数なしのツールです。"""
        print("Executing no_args_tool")
        return {"status": "No args tool executed successfully"}

    registry = ToolRegistry()
    registry.register_tool(search_online)
    registry.register_tool(get_weather)
    registry.register_tool(no_args_tool)

    print("---- Tool Schemas ----")
    import json
    print(json.dumps(registry.get_tool_schemas(), indent=2))

    print("\n---- Testing search_online ----")
    # search_online の引数はPydanticモデルなので、LLMは展開された引数を渡してくる想定
    # しかし、現在のparse_argumentsは関数シグネチャに基づいて動的モデルを作る
    # search_online のシグネチャは (params: SearchToolParams)
    # スキーマは params: { type: object, properties: { query: ..., limit: ...}} となる
    # LLM が {"query": "AI", "limit": 5} を渡してきた場合、
    # parse_arguments は {"params": {"query": "AI", "limit": 5}} を期待する。
    # これを解決するには、
    # 1. スキーマ生成でPydanticモデルのフィールドを展開し、関数シグネチャもフラットにする
    #    def search_online(query: str, limit: Optional[int] = 10)
    # 2. parse_argumentsで、関数がPydanticモデルを期待する場合、LLMからのフラットな引数をモデルに詰める
    #
    # ここでは、スキーマ生成がPydanticモデルのフィールドを展開するように修正する必要がある。
    # 現状の _generate_tool_schema は、Pydanticモデルが引数の型の場合、
    # parameters_schema["properties"][name] = { "type": "object", "properties": model_schema.get("properties", {}), ... }
    # のように、引数名をキーとしてその下にモデルのスキーマを入れている。
    # これがOpenAIのTool Callingの標準的なやり方（ネストされた引数オブジェクト）。
    #
    # 動作確認
    print("Schema for search_online:", json.dumps(registry._tool_schemas["search_online"], indent=2))
    
    # LLMがこのように引数を渡してきたと仮定
    search_args_str_correct = '''
    {
        "params": {
            "query": "AI trends",
            "limit": 3
        }
    }
    '''
    # search_args_str_flat = '''
    # {
    #     "query": "AI trends",
    #     "limit": 3
    # }
    # '''
    # 上記の search_args_str_flat だと、現在のparse_argumentsではエラーになる。
    # なぜなら、search_onlineのシグネチャは `params` という名前の引数を一つ取るため。

    try:
        parsed = registry.parse_arguments("search_online", search_args_str_correct)
        print("Parsed search_online args:", parsed)
        # result = asyncio.run(registry.execute_tool("search_online", search_args_str_correct)) # execute_toolはasync
        # print("Execution result for search_online:", result)
    except ValueError as e:
        print(f"Error parsing/executing search_online: {e}")

    print("\n---- Testing get_weather ----")
    weather_args_str = '{"location": "London", "unit": "celsius"}'
    try:
        parsed = registry.parse_arguments("get_weather", weather_args_str)
        print("Parsed get_weather args:", parsed)
        # result = asyncio.run(registry.execute_tool("get_weather", weather_args_str))
        # print("Execution result for get_weather:", result)

        weather_args_missing_required_str = '{"unit": "fahrenheit"}' # locationがない
        # parsed_missing = registry.parse_arguments("get_weather", weather_args_missing_required_str)
        # print("Parsed (missing required):", parsed_missing) # これはValidationErrorになるはず
    except ValueError as e:
        print(f"Error parsing/executing get_weather: {e}")

    print("\n---- Testing no_args_tool ----")
    no_args_str = '{}'
    try:
        parsed = registry.parse_arguments("no_args_tool", no_args_str)
        print("Parsed no_args_tool args:", parsed)
        # result = asyncio.run(registry.execute_tool("no_args_tool", no_args_str))
        # print("Execution result for no_args_tool:", result)

        no_args_with_extra_str = '{"foo": "bar"}'
        # parsed_extra = registry.parse_arguments("no_args_tool", no_args_with_extra_str) # エラーになるはず
    except ValueError as e:
        print(f"Error parsing/executing no_args_tool: {e}")

    async def run_async_executions():
        print("\n---- Async Execution ----")
        registry = ToolRegistry()
        registry.register_tool(search_online) # search_online は同期関数
        registry.register_tool(get_weather)   # get_weather は同期関数

        async def async_tool_example(query: str):
            """非同期で何かを実行するツールの例"""
            print(f"Async tool started with query: {query}")
            # await asyncio.sleep(1) # ダミーの非同期処理
            print(f"Async tool finished with query: {query}")
            return {"status": "async tool completed", "query": query}
        
        registry.register_tool(async_tool_example)
        print("Async tool schema:", json.dumps(registry._tool_schemas["async_tool_example"], indent=2))

        res_sync_search = await registry.execute_tool("search_online", search_args_str_correct)
        print("Async exec of sync search_online:", res_sync_search)
        
        res_async_example = await registry.execute_tool("async_tool_example", '{"query": "test async"}')
        print("Async exec of async_tool_example:", res_async_example)

    # asyncio.run(run_async_executions()) # execute_toolがasyncになったので、テストもasyncで実行

    # Pydanticモデルを引数に取る場合のスキーマとパースの挙動について、再考が必要。
    # OpenAIのFunction Callingでは、引数にPydanticモデルを指定すると、
    # そのモデルのフィールドが展開されてparametersとして定義されることが多い。
    # 例:
    # def my_func(user: User): ...
    # スキーマ: parameters: { type: object, properties: { name: {type: string}, age: {type: integer} ... }}
    # LLMは: {"name": "John", "age": 30} を渡す。
    #
    # 現在の _generate_tool_schema は、
    # parameters_schema["properties"][name] = { "type": "object", "properties": model_schema.get("properties", {})... }
    # となっており、引数名(user)の下にモデルのプロパティがネストする形。
    # これ自体は間違いではないが、LLMが引数をどう渡してくるかと一致させる必要がある。
    #
    # `parse_arguments` の動的モデル作成部分は、LLMがフラットな引数群 (例: {"name": "John", "age": 30})
    # を渡してくることを前提としている。
    #
    # もし関数シグネチャが `def my_func(user: User)` で、スキーマも `user: { type: object, properties: ...}` となり、
    # LLMが `{"user": {"name": "John", "age": 30}}` を渡す場合、
    # `ValidationModel(**raw_arguments)` は `ValidationModel(user={"name": "John", "age": 30})` となり、
    # 正しく動作する。
    #
    # 問題は、LLMがフラットな引数 `{"name": "John", "age": 30}` を渡してきた場合に、
    # これを `User(name="John", age=30)` のように `user` 引数に割り当てる部分。
    # 現状の `parse_arguments` では、引数名とキーが一致しないとエラーになる。
    #
    # 解決策:
    # 1. 関数シグネチャでPydanticモデルを使う場合、LLMにはそのモデルのフィールドを展開したスキーマを提示する。
    #    `_generate_tool_schema` を修正し、`parse_arguments` はそのままで良い。
    #    ツール関数呼び出し時に、フラットな引数をPydanticモデルに再構築する。
    #    例: `tool_func(User(**parsed_args))`
    # 2. スキーマは現在のままで、LLMがネストした引数 (`{"user": {"name": ...}}`) を渡すことを期待する。
    #    この場合、`parse_arguments` はそのままで良い。
    #
    # OpenAIのドキュメントでは、トップレベルの `parameters` オブジェクトの `properties` に
    # 各引数の定義をフラットに記述する例が多い。
    # もし引数自体が複雑なオブジェクトなら、その引数の `type` を `object` とし、
    # その下に `properties` をネストする。
    #
    # 今回は、関数シグネチャの引数名をそのまま `parameters.properties` のキーとして使う方針で進める。
    # Pydanticモデルが型アノテーションされている引数については、その引数名の下に
    # objectとしてモデルのスキーマが入る形が最も素直で、`parse_arguments` も対応しやすい。

    # `_generate_tool_schema`でのPydanticモデルの扱いを修正し、
    # Pydanticモデルのフィールドを直接展開するのではなく、
    # 引数名をキーとして、その下にオブジェクトとしてPydanticモデルのスキーマを配置する。
    # (現在の実装がそうなっているはずなので、テストケースのargs_strを合わせる)
    #
    # `search_online` の引数 `params` は `SearchToolParams` 型なので、
    # スキーマは `parameters: { properties: { params: { type: object, properties: { query: ..., limit: ... } } } }`
    # となる。LLMは `{"params": {"query": "AI", "limit": 3}}` のように引数を渡す。
    # `parse_arguments`では、`ValidationModel(params=SearchToolParams(query="AI", limit=3))` のように
    # 検証・変換が行われる。
    # これが一番整合性が取れている。

    # execute_toolがasyncになったので、メインのテストもasyncで実行
    import asyncio
    async def main_test():
        registry = ToolRegistry()
        registry.register_tool(search_online)
        registry.register_tool(get_weather)
        registry.register_tool(no_args_tool)

        print("---- Tool Schemas (re-check) ----")
        print(json.dumps(registry.get_tool_schemas(), indent=2))

        print("\n---- Testing search_online (async) ----")
        search_args_str = '{"params": {"query": "AI trends for 2024", "limit": 2}}'
        try:
            result = await registry.execute_tool("search_online", search_args_str)
            print("Execution result for search_online:", result)
        except Exception as e:
            print(f"Error executing search_online: {e}")

        print("\n---- Testing get_weather (async) ----")
        weather_args_str = '{"location": "Kyoto, JP", "unit": "celsius"}'
        try:
            result = await registry.execute_tool("get_weather", weather_args_str)
            print("Execution result for get_weather:", result)
        except Exception as e:
            print(f"Error executing get_weather: {e}")
        
        print("\n---- Testing get_weather with validation error (async) ----")
        weather_args_invalid_str = '{"unit": "fahrenheit"}' # location is missing
        try:
            result = await registry.execute_tool("get_weather", weather_args_invalid_str)
            print("Execution result for get_weather (invalid):", result) # Should be an error
        except Exception as e: # execute_tool内でキャッチされ、エラーdictが返る
             print(f"Caught in test: {e}")


        print("\n---- Testing no_args_tool (async) ----")
        no_args_str = '{}'
        try:
            result = await registry.execute_tool("no_args_tool", no_args_str)
            print("Execution result for no_args_tool:", result)
        except Exception as e:
            print(f"Error executing no_args_tool: {e}")
        
        print("\n---- Testing no_args_tool with extra args (async) ----")
        no_args_extra_str = '{"unexpected_arg": 123}'
        try:
            result = await registry.execute_tool("no_args_tool", no_args_extra_str)
            print("Execution result for no_args_tool (extra):", result) # Should be an error
        except Exception as e:
             print(f"Caught in test: {e}")


        print("\n---- Testing non-existent tool (async) ----")
        try:
            result = await registry.execute_tool("non_existent_tool", '{}')
            print("Execution result for non_existent_tool:", result)
        except ValueError as e:
            print(f"Error (expected): {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")


    if __name__ == '__main__':
        asyncio.run(main_test()) 