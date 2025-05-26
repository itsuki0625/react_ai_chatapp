from typing import List, Dict, Any, Optional
import uuid

class GuardrailViolationError(Exception):
    """Guardrailポリシー違反が発生した場合のエラー。"""
    def __init__(self, message, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details if details else {}

class BaseGuardrail:
    """Guardrailコンポーネントの基本インターフェース。"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config if config else {}
        print(f"Guardrail initialized with config: {self.config}")

    async def check_input(
        self, 
        messages: List[Dict[str, Any]], 
        agent_name: Optional[str] = None, 
        session_id: Optional[uuid.UUID] = None,
        user_id: Optional[str] = None # 将来的な拡張のため
    ) -> List[Dict[str, Any]]:
        """
        エージェントへの入力メッセージを検証・フィルタリングします。
        問題があれば GuardrailViolationError を発生させるか、メッセージを修正して返します。
        デフォルトでは何もせず、そのままメッセージを返します。
        """
        print(f"[Guardrail] Checking input for agent '{agent_name}' (session: {session_id}). Message count: {len(messages)}")
        # ここに具体的な入力チェックロジックを実装します。
        # 例: 有害コンテンツフィルタ、機密情報マスキングなど
        # for msg in messages:
        #     if "forbidden_keyword" in msg.get("content", "").lower():
        #         raise GuardrailViolationError("Input contains forbidden keyword.", details={"keyword": "forbidden_keyword"})
        return messages

    async def check_output(
        self, 
        response_chunk: Dict[str, Any], 
        agent_name: Optional[str] = None, 
        session_id: Optional[uuid.UUID] = None,
        user_id: Optional[str] = None # 将来的な拡張のため
    ) -> Dict[str, Any]:
        """
        エージェントからの出力チャンクを検証・フィルタリングします。
        問題があれば GuardrailViolationError を発生させるか、チャンクを修正して返します。
        デフォルトでは何もせず、そのままチャンクを返します。
        """
        # print(f"[Guardrail] Checking output chunk for agent '{agent_name}' (session: {session_id}). Chunk type: {response_chunk.get('type')}")
        # ここに具体的な出力チェックロジックを実装します。
        # 例: 有害コンテンツフィルタ、個人情報が含まれていないかの確認など
        # if response_chunk.get("type") == "delta" and response_chunk.get("data", {}).get("content"):
        #     if "sensitive_info" in response_chunk["data"]["content"].lower():
        #         # response_chunk["data"]["content"] = "[REDACTED]"
        #         raise GuardrailViolationError("Output contains sensitive information.", details={"chunk_type": response_chunk.get("type")})
        return response_chunk

    async def can_execute_tool(
        self, 
        tool_name: str, 
        tool_args: Dict[str, Any], 
        agent_name: Optional[str] = None, 
        session_id: Optional[uuid.UUID] = None,
        user_id: Optional[str] = None, # 将来的な拡張のため
        tool_registry: Optional[Any] = None # ツール定義やカテゴリ等を参照する場合
    ) -> bool:
        """
        指定されたツールの実行が許可されるかどうかを判断します。
        デフォルトでは常に True (許可) を返します。
        """
        print(f"[Guardrail] Checking tool execution permission for tool '{tool_name}' by agent '{agent_name}' (session: {session_id}). Args: {tool_args}")
        # ここに具体的なツール実行許可ロジックを実装します。
        # 例: 特定ツールの実行制限、引数の内容に基づく制限、TokenGuardのようなコストベースの制限など
        # if tool_name == "dangerous_tool":
        #     print(f"[Guardrail] Execution of tool '{tool_name}' DENIED by policy.")
        #     return False
        return True

# 具体的なGuardrailの実装例 (オプション)
class MyCustomGuardrail(BaseGuardrail):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.restricted_tools = self.config.get("restricted_tools", [])

    async def can_execute_tool(
        self, 
        tool_name: str, 
        tool_args: Dict[str, Any], 
        agent_name: Optional[str] = None, 
        session_id: Optional[uuid.UUID] = None,
        user_id: Optional[str] = None, 
        tool_registry: Optional[Any] = None
    ) -> bool:
        await super().can_execute_tool(tool_name, tool_args, agent_name, session_id, user_id, tool_registry) # 親クラスのログ等呼び出し
        if tool_name in self.restricted_tools:
            print(f"[MyCustomGuardrail] Execution of tool '{tool_name}' DENIED as it is in restricted list.")
            return False
        return True

    async def check_input(
        self, 
        messages: List[Dict[str, Any]], 
        agent_name: Optional[str] = None, 
        session_id: Optional[uuid.UUID] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        await super().check_input(messages, agent_name, session_id, user_id)
        # 例: 攻撃的な単語が含まれていないかチェック
        for i, msg in enumerate(messages):
            content = msg.get("content", "")
            if isinstance(content, str) and "stupid" in content.lower(): # 簡単な例
                # messages[i]["content"] = content.lower().replace("stupid", "s*****") # 修正する場合
                raise GuardrailViolationError(f"Input message contains prohibited word: stupid", details={"message_index": i})
        return messages 