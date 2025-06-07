from __future__ import annotations
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field
import asyncio
import time

if TYPE_CHECKING:
    from ..base_agent import BaseAgent

class ErrorRecoveryManager(BaseModel):
    # エラー回復ポリシー: component毎にmax_attemptsとdelayを設定
    retry_policies: dict[str, dict[str, float]] = Field(default_factory=lambda: {"default": {"max_attempts": 3, "delay": 1.0}})
    # フォールバック戦略: component名 -> 代替ツール名
    fallback_strategies: dict[str, str] = Field(default_factory=dict)
    # サーキットブレーカー: component毎の状態管理
    circuit_breakers: dict[str, dict[str, Any]] = Field(default_factory=dict)

    async def handle_failure(self, error: Exception, context_of_failure: dict, agent: 'BaseAgent') -> Any:
        """
        エラー発生時にリトライ、フォールバック、サーキットブレーカーを適用します。
        context_of_failureには最低限以下を含むことを想定:
          - tool_call: LLMからのツール呼び出し dict
          - session_id: UUID
        """
        # componentキー (ツール名または default)
        comp = context_of_failure.get("tool_call", {}).get("function", {}).get("name") or "default"
        # サーキットブレーカーが開いている場合は即エラー
        cb = self.circuit_breakers.get(comp)
        if cb and cb.get("is_open"):
            raise error
        # リトライポリシー取得
        policy = self.retry_policies.get(comp, self.retry_policies["default"])
        attempts = context_of_failure.get("attempts", 0)
        # リトライ
        if attempts < policy.get("max_attempts", 0):
            context = context_of_failure.copy()
            context["attempts"] = attempts + 1
            await asyncio.sleep(policy.get("delay", 0))
            try:
                return await agent._execute_tool_and_get_response(context["tool_call"], context.get("session_id"))
            except Exception as e:
                return await self.handle_failure(e, context, agent)
        # フォールバック
        fb = self.fallback_strategies.get(comp)
        if fb and "tool_call" in context_of_failure:
            fallback_call = context_of_failure["tool_call"].copy()
            fallback_call["function"]["name"] = fb
            try:
                return await agent._execute_tool_and_get_response(fallback_call, context_of_failure.get("session_id"))
            except Exception as e:
                error = e
        # サーキットブレーカーの更新
        if comp not in self.circuit_breakers:
            self.circuit_breakers[comp] = {"failure_count": 0, "failure_threshold": 3, "is_open": False}
        self.circuit_breakers[comp]["failure_count"] += 1
        if self.circuit_breakers[comp]["failure_count"] >= self.circuit_breakers[comp]["failure_threshold"]:
            self.circuit_breakers[comp]["is_open"] = True
        # 最終的にエラーを返却
        raise error 