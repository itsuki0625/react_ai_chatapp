from __future__ import annotations
import json
from typing import List, Dict, Any, Optional, AsyncIterator, Union

from openai import AsyncOpenAI, OpenAIError # OpenAIライブラリ
from openai.types.chat import ChatCompletionMessageToolCall, ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall

from .base_llm_adapter import BaseLLMAdapter

# OpenAI APIエラーをプロジェクト共通のエラーにマップすることも検討
# from app.core.errors import LLMCommunicationError, LLMAuthenticationError, LLMRateLimitError

class OpenAIAdapter(BaseLLMAdapter):
    """
    OpenAI API (gpt-4o, gpt-3.5-turboなど) との通信を行うアダプター。
    """

    def __init__(self, model_name: str, api_key: Optional[str] = None, base_url: Optional[str] = None, **kwargs):
        super().__init__(model_name, api_key, base_url, **kwargs)
        try:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                **self.extra_params.get("client_kwargs", {}) # http_clientなどの追加設定
            )
        except Exception as e:
            # ここで初期化失敗をログに記録したり、カスタム例外を発生させたりできる
            print(f"[OpenAIAdapter] Failed to initialize AsyncOpenAI client: {e}")
            raise # または raise LLMInitializationError(f"Failed to initialize OpenAI client: {e}") from e

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        model: Optional[str] = None, # modelを引数に追加
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        **kwargs: Any
    ) -> Union[Dict[str, Any], AsyncIterator[Dict[str, Any]]]:
        """
        OpenAI APIにチャット補完リクエストを送信します。
        """
        request_params = {
            "model": model or self.model_name, # 引数のmodelを優先
            "messages": messages,
            "stream": stream,
        }
        if tools:
            request_params["tools"] = tools
        if tool_choice:
            request_params["tool_choice"] = tool_choice
        if temperature is not None:
            request_params["temperature"] = temperature
        if max_tokens is not None:
            request_params["max_tokens"] = max_tokens
        if top_p is not None:
            request_params["top_p"] = top_p
        
        # kwargs から直接渡せるパラメータをマージ (例: 'response_format', 'seed'など)
        # ただし、上記で明示的に処理したパラメータは上書きしないように注意
        for key, value in kwargs.items():
            if key not in request_params and value is not None:
                request_params[key] = value

        try:
            if stream:
                # ストリーミング処理は _stream_chat_completion ヘルパーメソッドで行う
                return self._stream_chat_completion(**request_params)
            else:
                # 非ストリーミング処理
                completion = await self.client.chat.completions.create(**request_params)
                
                # トークン使用量を取得して保存
                if completion.usage:
                    self._set_latest_usage({
                        "prompt_tokens": completion.usage.prompt_tokens,
                        "completion_tokens": completion.usage.completion_tokens,
                        "total_tokens": completion.usage.total_tokens,
                    })
                else:
                    self._set_latest_usage(None)

                # BaseAgentが期待する形式にレスポンスを変換 (parse_llm_response_chunkと似たロジックが必要)
                # ここでは簡略化のため、主要な情報を抽出して返す
                # 実際のレスポンス形式はOpenAIのAPIドキュメントを参照
                response_message = completion.choices[0].message
                
                # BaseAgentが期待する形式に近い辞書を返す
                # "type" は "delta" や "tool_calls" ではなく、単一の応答メッセージとして扱う
                # run メソッド側で最終的な content や tool_calls を組み立てる
                final_response: Dict[str, Any] = {
                    "role": response_message.role, # "assistant"
                    "content": response_message.content or "",
                }
                if response_message.tool_calls:
                    final_response["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": tc.type, 
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                        }
                        for tc in response_message.tool_calls
                    ]
                
                # 非ストリーミングの場合でも、usage情報をレスポンスに含める
                # BaseAgentのrunメソッドはusageチャンクを期待するが、非ストリームではここでusageを返す
                if completion.usage:
                     final_response["usage"] = self.get_latest_usage()

                return final_response

        except OpenAIError as e:
            # OpenAIライブラリ固有のエラーを処理
            # TODO: より詳細なエラーハンドリング (レート制限、認証エラーなど)
            print(f"[OpenAIAdapter] OpenAI API error: {e}")
            # raise LLMCommunicationError(f"OpenAI API error: {e}") from e
            # ストリーミング中のエラーは parse_llm_response_chunk で "error" タイプとしてyieldされるべき
            # 非ストリーミングの場合は、ここでエラー情報を整形して返すか、例外を投げる
            if stream:
                 # ストリームの場合は、エラーをチャンクとして返す
                 # _stream_chat_completion内で処理されるので、ここでは再raiseしない
                 # 代わりにエラーを示すチャンクを生成する
                 # しかし、この箇所に到達する場合、_stream_chat_completion呼び出し前なので、
                 # _stream_chat_completion内部のエラーハンドリングに任せる方が一貫する。
                 # ここでは、呼び出し元がAsyncIteratorを期待しているため、エラーをラップしたイテレータを返すか、
                 # 例外をそのまま投げる。
                 # BaseAgentはllm_adapter.chat_completionを直接呼び出すため、
                 # stream=Trueの場合はAsyncIteratorが期待される。
                 async def error_iterator():
                    yield {"type": "error", "data": {"message": str(e), "code": e.code if hasattr(e, 'code') else None}}
                 return error_iterator()
            return {"type": "error", "data": {"message": str(e), "code": e.code if hasattr(e, 'code') else None}} # 非ストリーム時
        except Exception as e:
            # その他の予期せぬエラー
            print(f"[OpenAIAdapter] Unexpected error during chat completion: {e}")
            # raise LLMCommunicationError(f"Unexpected error: {e}") from e
            if stream:
                async def error_iterator():
                    yield {"type": "error", "data": {"message": str(e), "code": "unknown"}}
                return error_iterator()
            return {"type": "error", "data": {"message": str(e), "code": "unknown"}}

    async def _stream_chat_completion(self, **request_params: Any) -> AsyncIterator[Dict[str, Any]]:
        """
        OpenAI APIからのストリーミング応答を処理し、BaseAgentが期待するチャンク形式でyieldします。
        """
        # ツールコールの情報を蓄積 (index -> tool_call_data)
        # tool_call_data: {"id": str, "name": str, "arguments": str, "started": bool, "ended": bool}
        accumulated_tool_calls: Dict[int, Dict[str, Any]] = {}

        try:
            stream_response = await self.client.chat.completions.create(**request_params)
            async for chunk_obj in stream_response: # chunk_obj is ChatCompletionChunk
                chunk = chunk_obj.model_dump(exclude_unset=True) # Pydanticモデルをdictに変換
                
                parsed_chunks = self.parse_llm_response_chunk(
                    chunk,
                    accumulated_tool_calls
                )
                for parsed_chunk in parsed_chunks: # parse_llm_response_chunkはリストを返すように変更
                    yield parsed_chunk
        
        except OpenAIError as e:
            print(f"[OpenAIAdapter] OpenAI API error during stream: {e}")
            yield {"type": "error", "data": {"message": str(e), "code": e.code if hasattr(e, 'code') else None}}
        except Exception as e:
            print(f"[OpenAIAdapter] Unexpected error during stream: {e}")
            yield {"type": "error", "data": {"message": str(e), "code": "unknown"}}

    def format_tool_call_response(
        self,
        tool_call_id: str,
        tool_name: str, 
        result: Any
    ) -> Dict[str, Any]:
        """
        OpenAI APIの形式に合わせてツール実行結果を整形します。
        BaseAgentの_execute_tool_and_get_responseがこの形式のメッセージを生成する際に利用します。
        LLMに送るメッセージ形式です。
        """
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            # "name": tool_name, # OpenAIのtool role messageはnameフィールドを持たない
            "content": json.dumps(result) if not isinstance(result, str) else result,
        }

    def parse_llm_response_chunk(
        self,
        chunk: Dict[str, Any], # ChatCompletionChunk model_dump
        accumulated_tool_calls: Dict[int, Dict[str, Any]] = None # 変更: 状態をここで管理、デフォルトをNone許容
    ) -> List[Dict[str, Any]]: # 常にリストを返すように変更 (複数のチャンクを一度に生成する可能性があるため)
        if accumulated_tool_calls is None:
            accumulated_tool_calls = {}

        results: List[Dict[str, Any]] = []
        choice = chunk.get("choices", [{}])[0]
        delta = choice.get("delta", {}) # delta: Optional[ChoiceDelta]
        finish_reason = choice.get("finish_reason")

        # 1. テキストデルタの処理
        if delta.get("content"):
            results.append({"type": "delta", "data": {"content": delta["content"]}})

        # 2. ツールコールデルタの処理
        # delta.tool_calls は Optional[List[ChoiceDeltaToolCall]]
        if "tool_calls" in delta and delta["tool_calls"] is not None:
            for tc_delta in delta["tool_calls"]: # tc_delta: ChoiceDeltaToolCall
                index = tc_delta.get("index")
                if index is None: continue 

                tool_call_id_delta = tc_delta.get("id")
                function_delta = tc_delta.get("function", {}) # function: Optional[ChoiceDeltaToolCallFunction]
                func_name_delta = function_delta.get("name")
                func_args_delta = function_delta.get("arguments")

                # accumulated_tool_calls[index] が存在しない場合 (このindexの最初のチャンク)
                if index not in accumulated_tool_calls:
                    if tool_call_id_delta and func_name_delta: # IDと名前が初回で揃うことを期待
                        accumulated_tool_calls[index] = {
                            "id": tool_call_id_delta,
                            "name": func_name_delta,
                            "arguments": func_args_delta or "", # 初回からargsがある場合も
                            "started": True,
                            "ended": False # まだ終了していない
                        }
                        results.append({
                            "type": "tool_call_start",
                            "data": {"id": tool_call_id_delta, "name": func_name_delta}
                        })
                        if func_args_delta: # 初回チャンクに引数も含まれていたらdeltaも発行
                             results.append({
                                "type": "tool_call_delta",
                                "data": {"id": tool_call_id_delta, "input_delta": func_args_delta}
                            })
                    elif tool_call_id_delta: # IDのみの場合 (名前は後続チャンクで来る想定)
                         accumulated_tool_calls[index] = {
                            "id": tool_call_id_delta,
                            "name": "", # 仮置き
                            "arguments": func_args_delta or "",
                            "started": False, # nameが来るまで started としない
                            "ended": False
                        }
                         if func_args_delta: # IDのみでも引数があれば、一旦deltaは出せるが、startが先の方が良い
                             # このケースは設計次第。ここではnameが来てからstartとする。
                             pass
                    # 他のケース (idやnameが初回で来ない) は一旦無視またはエラーログ

                else: # 既に index が存在する (追従チャンク)
                    current_tc = accumulated_tool_calls[index]
                    if not current_tc["started"] and func_name_delta:
                        current_tc["name"] = func_name_delta
                        current_tc["started"] = True
                        results.append({
                            "type": "tool_call_start",
                            "data": {"id": current_tc["id"], "name": current_tc["name"]}
                        })
                        # start発行時に、既に溜まっていた引数があればそれもdeltaとして出す
                        if current_tc["arguments"]:
                             results.append({
                                "type": "tool_call_delta",
                                "data": {"id": current_tc["id"], "input_delta": current_tc["arguments"]}
                            })


                    if func_args_delta:
                        current_tc["arguments"] += func_args_delta
                        if current_tc["started"]: # start済みならdeltaを発行
                            results.append({
                                "type": "tool_call_delta",
                                "data": {"id": current_tc["id"], "input_delta": func_args_delta}
                            })
        
        # 3. 終了理由の処理
        if finish_reason:
            if finish_reason == "tool_calls":
                # 蓄積されたすべてのツールコールに対して tool_call_end を発行
                for index, tc_data in accumulated_tool_calls.items():
                    if tc_data["started"] and not tc_data["ended"]:
                        results.append({
                            "type": "tool_call_end",
                            "data": {
                                "id": tc_data["id"],
                                "name": tc_data["name"],
                                "arguments": tc_data["arguments"]
                            }
                        })
                        tc_data["ended"] = True # 処理済みマーク
                
                results.append({"type": "stop", "data": {"finish_reason": "tool_calls"}})
            
            else: # "stop", "length", etc.
                # もし進行中のツールコールがあれば、ここで強制的に終了させるかエラーとするか検討
                # 通常、finish_reason="stop" の前に tool_calls の処理は完了しているはず
                results.append({"type": "stop", "data": {"finish_reason": finish_reason}})

        # 4. 使用量情報の処理 (OpenAIでは通常、最後のチャンクにusageが含まれる)
        # chunk (ChatCompletionChunk) には直接 usage がない。
        # streamオブジェクトの最後のイベントとして `completion.usage` を処理する必要があるが、
        # `AsyncOpenAI().chat.completions.create()` のストリームでは、
        # 各チャンクにはusageは含まれず、ストリーム完了後に別途取得する形ではない。
        # (例: `stream.final_usage` のようなプロパティがあるわけではない)
        # Anthropicのように `message_delta` イベントで `usage` が来るわけでもない。
        #
        # 通常、OpenAIのストリーミングでは、`finish_reason` がある最後のチャンクの後に
        # `usage`情報が単独で送られてくることはありません。
        # `BaseLLMAdapter`の`_set_latest_usage`と`get_latest_usage`は
        # 非ストリーミング時や、ストリーミングでもLLMが明示的にusageチャンクを返す場合に使われます。
        # OpenAIのストリーミングの場合、`BaseAgent`側で`run`メソッド完了時に`llm_adapter.get_latest_usage()`を
        # 呼び出すことで、そのリクエスト全体のトークン数を取得することは可能です（非ストリーミングの場合と同様）。
        # ストリーミング中に`usage`チャンクを生成することはOpenAIの標準的な振る舞いではありません。
        # よって、ここでは`usage`チャンクを生成しません。
        # `BaseAgent`の`stream`メソッドの最後で`llm_adapter.get_latest_usage()`を呼び出して`usage`チャンクをyieldする
        # 設計になっているため、このアダプタで明示的に`usage`チャンクを生成する必要はありません。

        return results

    async def close(self):
        """
        AsyncOpenAIクライアントを閉じます。
        """
        if self.client:
            await self.client.close()
            print("[OpenAIAdapter] AsyncOpenAI client closed.")
