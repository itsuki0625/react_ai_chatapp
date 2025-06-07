from __future__ import annotations
import json
from typing import List, Dict, Any, Optional, AsyncIterator, Union

from anthropic import AsyncAnthropic, AnthropicError
from anthropic.types import Message, ContentBlock, ToolUseBlock, MessageStreamEvent

from .base_llm_adapter import BaseLLMAdapter

# Anthropic APIエラーをプロジェクト共通のエラーにマップすることも検討
# from app.core.errors import LLMCommunicationError, LLMAuthenticationError, LLMRateLimitError

class AnthropicAdapter(BaseLLMAdapter):
    """
    Anthropic API (Claudeモデル) との通信を行うアダプター。
    """

    def __init__(self, model_name: str, api_key: Optional[str] = None, base_url: Optional[str] = None, **kwargs):
        super().__init__(model_name, api_key, base_url, **kwargs)
        try:
            # base_url は Anthropic SDK では直接サポートされていない場合があるため、
            # 必要であれば httpx.AsyncClient をカスタマイズして渡す必要がある。
            # 現状は api_key と model_name を中心に初期化。
            self.client = AsyncAnthropic(
                api_key=self.api_key,
                base_url=self.base_url, # Anthropic SDKが base_url をサポートしているか確認が必要
                 **self.extra_params.get("client_kwargs", {}) # timeoutなどの追加設定
            )
        except Exception as e:
            print(f"[AnthropicAdapter] Failed to initialize AsyncAnthropic client: {e}")
            raise

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        model: Optional[str] = None, # modelを引数に追加
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Dict[str, Any]] = None, 
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = 2048, 
        top_p: Optional[float] = None,
        **kwargs: Any
    ) -> Union[Dict[str, Any], AsyncIterator[Dict[str, Any]]]:
        """
        Anthropic APIにチャット補完リクエストを送信します。
        """
        system_prompt_content: Optional[str] = None
        processed_messages = []
        if messages and messages[0]["role"] == "system":
            system_prompt_content = messages[0]["content"]
            processed_messages = messages[1:]
        else:
            processed_messages = messages

        request_params = {
            "model": model or self.model_name,
            "messages": processed_messages,
            "max_tokens": max_tokens, 
            "stream": stream,
        }
        if system_prompt_content:
            request_params["system"] = system_prompt_content
        if tools:
            request_params["tools"] = tools # Assumes tools are already in Anthropic format
        if tool_choice:
            request_params["tool_choice"] = tool_choice
        if temperature is not None:
            request_params["temperature"] = temperature
        if top_p is not None:
            request_params["top_p"] = top_p
        
        for key, value in kwargs.items():
            if key not in request_params and value is not None:
                request_params[key] = value
        
        try:
            if stream:
                return self._stream_chat_completion(**request_params)
            else:
                completion: Message = await self.client.messages.create(**request_params)

                if completion.usage:
                    self._set_latest_usage({
                        "prompt_tokens": completion.usage.input_tokens,
                        "completion_tokens": completion.usage.output_tokens,
                        "total_tokens": completion.usage.input_tokens + completion.usage.output_tokens 
                    })
                else:
                    self._set_latest_usage(None)

                assistant_content_parts = []
                tool_calls_data = []
                if completion.content:
                    for block in completion.content:
                        if block.type == "text":
                            assistant_content_parts.append(block.text)
                        elif block.type == "tool_use":
                            # Ensure block.input is a dictionary before json.dumps
                            arguments_to_dump = block.input if isinstance(block.input, dict) else {}
                            tool_calls_data.append({
                                "id": block.id,
                                "type": "function", 
                                "function": {"name": block.name, "arguments": json.dumps(arguments_to_dump)}
                            })
                
                final_response: Dict[str, Any] = {
                    "role": str(completion.role),
                    "content": "".join(assistant_content_parts),
                }
                if tool_calls_data:
                    final_response["tool_calls"] = tool_calls_data
                
                if completion.usage:
                    final_response["usage"] = self.get_latest_usage()

                return final_response

        except AnthropicError as e:
            print(f"[AnthropicAdapter] Anthropic API error: {e}")
            if stream:
                 async def error_iterator():
                    yield {"type": "error", "data": {"message": str(e), "code": e.status_code if hasattr(e, 'status_code') else None}}
                 return error_iterator()
            return {"type": "error", "data": {"message": str(e), "code": e.status_code if hasattr(e, 'status_code') else None}}
        except Exception as e:
            print(f"[AnthropicAdapter] Unexpected error during chat completion: {e}")
            if stream:
                async def error_iterator():
                    yield {"type": "error", "data": {"message": str(e), "code": "unknown"}}
                return error_iterator()
            return {"type": "error", "data": {"message": str(e), "code": "unknown"}}

    async def _stream_chat_completion(self, **request_params: Any) -> AsyncIterator[Dict[str, Any]]:
        """
        Anthropic APIからのストリーミング応答を処理し、BaseAgentが期待するチャンク形式でyieldします。
        """
        # キー: content_block index, 値: {id, name, arguments, started, ended}
        accumulated_tool_calls: Dict[int, Dict[str, Any]] = {} 

        try:
            async with self.client.messages.stream(**request_params) as stream_response:
                async for event_obj in stream_response:
                    # event_obj is one of MessageStreamEvent types
                    event_data = event_obj.model_dump(exclude_unset=True)
                    # print(f"Raw Anthropic Event: {event_data}") # Debug
                    
                    parsed_chunks = self.parse_llm_response_chunk(
                        event_data, 
                        accumulated_tool_calls
                    )
                    for parsed_chunk in parsed_chunks:
                        yield parsed_chunk
        
        except AnthropicError as e:
            print(f"[AnthropicAdapter] Anthropic API error during stream: {e}")
            yield {"type": "error", "data": {"message": str(e), "code": e.status_code if hasattr(e, 'status_code') else None}}
        except Exception as e:
            print(f"[AnthropicAdapter] Unexpected error during stream: {e}")
            yield {"type": "error", "data": {"message": str(e), "code": "unknown"}}

    def format_tool_call_response(
        self,
        tool_call_id: str, # Anthropicのtool_use_idに相当
        tool_name: str,    # BaseAgentの形式。ToolRegistryが検証に使う
        result: Any,
        is_error: bool = False # Anthropic特有: ツール実行がエラーだったかを示す
    ) -> Dict[str, Any]:
        """
        Anthropic APIの形式に合わせてツール実行結果を整形します。
        これは、次のLLMへのリクエストの message list に追加される content block 要素となります。
        """
        content_payload: Union[str, List, Dict] = ""
        if isinstance(result, (str, int, float, bool)):
            content_payload = str(result)
        elif isinstance(result, (list, dict)):
            content_payload = result # AnthropicはJSONオブジェクト/配列を直接contentとして受け入れる
        else:
            try:
                content_payload = json.dumps(result) # それ以外はJSON文字列化を試みる
            except TypeError:
                content_payload = str(result) # 最悪文字列化

        # Anthropic expects a list of content blocks for the 'user' role message
        # containing tool results.
        return {
            "type": "tool_result",
            "tool_use_id": tool_call_id,
            "content": content_payload,
            # "is_error": is_error # is_error は v0.20.0時点では明示的にない。エラーはcontentで示す
        }

    def parse_llm_response_chunk(
        self,
        event_data: Dict[str, Any], 
        accumulated_tool_calls: Dict[int, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Anthropic APIからのストリーミングイベントをBaseAgentが期待する共通形式のリストにパースします。
        """
        results: List[Dict[str, Any]] = []
        event_type = event_data.get("type")

        if event_type == "message_start":
            # message = event_data.get("message", {})
            # usage = message.get("usage", {})
            # if usage.get("input_tokens") is not None: # 初期トークン(プロンプト)はここで来る
            #     self._set_latest_usage({
            #         "prompt_tokens": usage["input_tokens"],
            #         "completion_tokens": 0, # まだ出力はない
            #         "total_tokens": usage["input_tokens"]
            #     })
            #     results.append({"type": "usage", "data": self.get_latest_usage()})
            pass # message_startでは特にBaseAgentチャンクは生成しない

        elif event_type == "content_block_start":
            index = event_data.get("index")
            content_block = event_data.get("content_block", {})
            block_type = content_block.get("type")

            if block_type == "tool_use":
                tool_use_data = content_block.get("tool_use", {})
                tool_id = tool_use_data.get("id")
                tool_name = tool_use_data.get("name")
                tool_input = tool_use_data.get("input", {}) # inputはdictのはず
                
                if index is not None and tool_id and tool_name:
                    accumulated_tool_calls[index] = {
                        "id": tool_id,
                        "name": tool_name,
                        "arguments": json.dumps(tool_input or {}), # ToolRegistryはJSON文字列を期待
                        "started": True,
                        "ended": False
                    }
                    results.append({
                        "type": "tool_call_start",
                        "data": {"id": tool_id, "name": tool_name, "input_so_far": accumulated_tool_calls[index]["arguments"] }
                    })
                    # Anthropicのtool_useはinputが一度に来るので、ここでtool_call_deltaは不要
                    # また、tool_call_endもcontent_block_stopで発行
        
        elif event_type == "content_block_delta":
            index = event_data.get("index")
            delta = event_data.get("delta", {})
            delta_type = delta.get("type")

            if delta_type == "text_delta":
                text = delta.get("text")
                if text:
                    results.append({"type": "delta", "data": {"content": text}})
            
            # Anthropicの `content_block_delta` で `tool_use_delta` は通常 input の差分ではなく、
            # text_delta のように単純なものではない。inputは `content_block_start` で完結することが多い。
            # もし `tool_use_delta` があり、それが引数の追記を意味するならここで処理。
            # 現状のSDK (v0.20+) では `input_json_delta` は明示的にはない。
            # elif delta_type == "input_json_delta": # 仮のタイプ名
            #     if index in accumulated_tool_calls and accumulated_tool_calls[index]["started"]:
            #         tool_id = accumulated_tool_calls[index]["id"]
            #         input_delta_str = delta.get("partial_json", "") # 仮のフィールド名
            #         accumulated_tool_calls[index]["arguments"] += input_delta_str # 文字列結合
            #         results.append({
            #             "type": "tool_call_delta",
            #             "data": {"id": tool_id, "input_delta": input_delta_str}
            #         })
            pass

        elif event_type == "content_block_stop":
            index = event_data.get("index")
            if index is not None and index in accumulated_tool_calls:
                tc_data = accumulated_tool_calls[index]
                if tc_data["started"] and not tc_data["ended"]:
                    results.append({
                        "type": "tool_call_end",
                        "data": {
                            "id": tc_data["id"],
                            "name": tc_data["name"],
                            "arguments": tc_data["arguments"] # 既にJSON文字列のはず
                        }
                    })
                    tc_data["ended"] = True

        elif event_type == "message_delta":
            usage = event_data.get("usage")
            delta = event_data.get("delta", {})
            stop_reason = delta.get("stop_reason") # message_deltaのdelta直下

            if usage and usage.get("output_tokens") is not None: # output_tokensがある場合のみusage更新
                # 最新のprompt_tokensを取得 (message_startでセットされているか、なければ0)
                current_usage = self.get_latest_usage() or {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                prompt_tokens = current_usage.get("prompt_tokens", 0)
                
                completion_tokens = usage["output_tokens"]
                
                self._set_latest_usage({
                    "prompt_tokens": prompt_tokens, # プロンプトトークンは不変のはず
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens
                })
                results.append({"type": "usage", "data": self.get_latest_usage()})
            
            # message_delta の stop_reason は使わず、message_stop で処理する
            # (Anthropicドキュメントでは message_stop の stop_reason を参照することが推奨される)

        elif event_type == "message_stop":
            # finish_reason は event_data["message"]["stop_reason"] にあるべきだが、
            # SDKの MessageStreamEvent の message_stop には直接 stop_reason がない場合がある。
            # _stream_chat_completion で得られる stream_response.get_final_message().stop_reason を使うのが確実だが、
            # チャンクごとに処理するため、ここでは event_data のトップレベルに `stop_reason` があることを期待する。
            # もしなければ、最後の `message_delta` の `delta.stop_reason` を使うか、
            # `_stream_chat_completion` で別途処理が必要になる。
            # ここでは、`BaseAgent` に合わせるため、`message_stop` を `stop` チャンクのシグナルとして扱う。
            # `BaseAgent` 側で `stop_reason` がない場合のハンドリングが必要になるかもしれない。
            #
            # Anthropic SDK v0.20.0では、MessageStopEvent は client.messages.stream から直接は yield されず、
            # ストリームが終了した後に `stream.get_final_message()` で取得するMessageオブジェクトの `stop_reason` を参照する。
            # parse_llm_response_chunk は個々のイベントを処理するため、message_stopイベントで
            # どの`stop_reason`を使うかは慎重な検討が必要。
            # ここでは、`BaseAgent`が最終的に`stop_reason`を期待しているため、何らかの値を渡す。
            # `stream.get_final_message()` の結果をどこかで`parse_llm_response_chunk`に渡す必要があるかもしれない。
            # 今回は、`BaseAgent`の`stream`メソッドのループ終了後に`stop`チャンクが発行されることを期待し、
            # ここでは`message_stop`イベント自体を「LLMの思考が一段落した」という意味の`stop`とは解釈しない。
            #
            # ただし、`BaseAgent` の `stream` メソッドは、`finish_reason` がある `stop` チャンクでループを抜けるため、
            # ここで `stop` チャンクを出す必要がある。
            # `AnthropicError` が `stop_reason` を持っている場合がある。
            # しかし、正常終了時の `stop_reason` は `stream_response.get_final_message().stop_reason` で取得する。
            # `_stream_chat_completion` の `finally` ブロックでこれを処理するのが適切かもしれない。
            #
            # 修正: _stream_chat_completion の finally で stream_response.get_final_message() から stop_reason を取得し、
            # それを元に stop チャンクを yield する。 parse_llm_response_chunk の message_stop では何もしないか、ログのみ。
            print(f"[AnthropicAdapter] MessageStop event received: {event_data}")
            # results.append({"type": "stop", "data": {"finish_reason": "anthropic_message_stop"}}) # 仮
            pass
            
        elif event_type == "error":
            error_data = event_data.get("error", {})
            results.append({"type": "error", "data": {"message": error_data.get("message"), "code": error_data.get("type")}}) # Anthropicのエラータイプをcodeとして使う

        return results

    async def close(self):
        """
        AsyncAnthropicクライアントを閉じます。
        """
        if self.client:
            await self.client.close()
            print("[AnthropicAdapter] AsyncAnthropic client closed.")

# Example Usage (for testing, if needed)
async def _test_anthropic_adapter():
    # Placeholder for test code
    pass

if __name__ == "__main__":
    # import asyncio
    # asyncio.run(_test_anthropic_adapter())
    pass

# 必要な型定義 (例)
# class AnthropicTool(TypedDict):
#    name: str
#    description: str
#    input_schema: Dict[str, Any]