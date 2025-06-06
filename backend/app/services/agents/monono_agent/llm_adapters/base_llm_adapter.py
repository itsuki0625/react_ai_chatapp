from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator, Union, Callable

class BaseLLMAdapter(ABC):
    """
    LLMプロバイダーとの通信を抽象化する基底クラス。
    """

    def __init__(self, model_name: str, api_key: Optional[str] = None, base_url: Optional[str] = None, **kwargs):
        """
        アダプターを初期化します。

        Args:
            model_name: 使用するLLMのモデル名。
            api_key: LLMプロバイダーのAPIキー。
            base_url: LLMプロバイダーのベースURL（セルフホストなどの場合）。
            **kwargs: その他のプロバイダー固有の設定。
        """
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.extra_params = kwargs
        self._latest_usage_info: Optional[Dict[str, int]] = None

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        **kwargs: Any  # プロバイダー固有の追加パラメータ
    ) -> Union[Dict[str, Any], AsyncIterator[Dict[str, Any]]]:
        """
        LLMにチャット補完リクエストを送信します。

        Args:
            messages: LLMに送信するメッセージのリスト。
            stream: ストリーミング応答を有効にするかどうか。
            tools: LLMが利用可能なツールのリスト (例: OpenAI Tool Calling)。
            tool_choice: LLMに特定のツールを使用させるかどうかの制御 (例: "auto", "none", {"type": "function", "function": {"name": "my_function"}})。
            temperature: 生成時のランダム性を制御する値。
            max_tokens: 生成するトークンの最大数。
            top_p: Top-pサンプリングの値。
            **kwargs: その他のプロバイダー固有のパラメータ。

        Returns:
            stream=Falseの場合: LLMからの完全な応答 (dict)。
            stream=Trueの場合: LLMからの応答チャンクを非同期に返すイテレータ (AsyncIterator[dict])。
        """
        raise NotImplementedError

    @abstractmethod
    def format_tool_call_response(
        self,
        tool_call_id: str,
        tool_name: str, # OpenAIのTool callingではnameは不要だが、一般的な形式として残す
        result: Any
    ) -> Dict[str, Any]:
        """
        ツールの実行結果をLLMに渡すためのメッセージ形式に整形します。

        Args:
            tool_call_id: 対応するツールコールのID。
            tool_name: 実行されたツールの名前 (情報として保持、LLMによっては不要)。
            result: ツールの実行結果 (通常は文字列化される)。

        Returns:
            LLMに送信するためのツール応答メッセージ (dict)。
        """
        raise NotImplementedError

    @abstractmethod
    def parse_llm_response_chunk(
        self,
        chunk: Dict[str, Any],
        prev_chunk_data: Optional[Dict[str, Any]] = None # 一部のLLM (Anthropic Tools)ではtool_useブロックの開始と入力が別チャンクのため
    ) -> Dict[str, Any]:
        """
        LLMからのストリーミング応答チャンクを、共通の内部形式 (delta, tool_callなど) にパースします。
        このメソッドは、BaseAgentが処理しやすいように、異なるLLMプロバイダーのチャンク形式の差異を吸収します。

        Args:
            chunk: LLMプロバイダーから受信した生の応答チャンク。
            prev_chunk_data: (オプション) 前のチャンクで不完全だったツールコール情報など。

        Returns:
            正規化されたチャンクデータ (dict)。例:
            - テキスト差分: {"type": "delta", "content": "text"}
            - ツールコール開始: {"type": "tool_call_start", "id": "call_abc", "name": "tool_name", "input_so_far": "{"arg"}
            - ツールコール入力差分: {"type": "tool_call_delta", "id": "call_abc", "input_delta": "ument":1"}
            - ツールコール完了: {"type": "tool_call_end", "id": "call_abc", "name": "tool_name", "arguments": "{"argument":1}"}
            - 使用状況: {"type": "usage", "prompt_tokens": X, "completion_tokens": Y}
            - エラー: {"type": "error", "message": "...", "code": ...}
            - その他メタ情報: {"type": "meta", ...}
        """
        raise NotImplementedError


    def get_latest_usage(self) -> Optional[Dict[str, int]]:
        """
        最後のAPI呼び出しでのトークン使用量などの情報を取得します。
        この情報は、`chat_completion` メソッドの実行中または実行後に更新されるべきです。

        Returns:
            トークン使用量情報 (例: {"prompt_tokens": X, "completion_tokens": Y, "total_tokens": Z})。
            情報がない場合はNone。
        """
        return self._latest_usage_info

    def _set_latest_usage(self, usage_info: Optional[Dict[str, int]]):
        """
        内部的に最新の利用状況情報を設定します。
        具象アダプターは、APIレスポンスからこの情報を抽出し、このメソッドを呼び出す必要があります。
        """
        self._latest_usage_info = usage_info

    # オプション: プロンプトテンプレート関連のヘルパーメソッド (具象クラスで実装またはオーバーライド)
    def apply_prompt_template(self, messages: List[Dict[str, Any]], template_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        (オプション) 指定されたテンプレート名に基づいてメッセージリストを加工します。
        デフォルトでは何もしません。具象アダプタは特定のLLMのプロンプト形式に合わせるためにこれをオーバーライドできます。
        """
        if template_name:
            print(f"[BaseLLMAdapter] apply_prompt_template called with template_name='{template_name}', but no specific template logic is implemented in the base class.")
        return messages

    async def close(self):
        """
        アダプターに関連するリソース（例: HTTPクライアントセッション）を解放します。
        デフォルトでは何もしませんが、具象クラスで必要に応じてオーバーライドします。
        """
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

# 型定義 (必要に応じて追加)
# class LLMResponseChunk(TypedDict):
#    type: Literal["delta", "tool_call_start", "tool_call_delta", "tool_call_end", "usage", "error", "meta"]
#    # ... other fields based on type