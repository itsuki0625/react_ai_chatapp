from __future__ import annotations
from typing import List, Dict, Any, Optional # TYPE_CHECKING は不要なので削除
import uuid
from pydantic import BaseModel, Field

# if TYPE_CHECKING: # BaseAgent を直接使わないので不要
#     from ..base_agent import BaseAgent

class ResourceManager(BaseModel):
    api_quotas: Dict[str, Dict[str, float]] = Field(default_factory=lambda: {"openai": {"limit": float("inf"), "used": 0.0}})
    compute_resources: Dict[str, Any] = Field(default_factory=lambda: {"cpu_limit": 0.8, "memory_limit_mb": 4096})
    cost_tracking: Dict[str, float] = Field(default_factory=lambda: {"budget": float("inf"), "spent": 0.0})
    token_cost_per_token: float = 0.00001  # USD per token

    def can_execute(self, tool_name: str, estimated_cost: float, required_resources: Optional[Dict] = None) -> bool:
        # 予算チェック
        cost = max(estimated_cost, 0.0)
        if self.cost_tracking["spent"] + cost > self.cost_tracking["budget"]:
            print(f"[ResourceManager] Budget exceeded: spent {self.cost_tracking['spent']} + cost {cost} > budget {self.cost_tracking['budget']}")
            return False
        # TODO: 必要に応じてCPUやメモリのチェックを追加
        return True

    def track_usage(self, component_name: str, usage_data: Dict):
        # ツール実行コストの追跡
        if component_name.startswith("tool:"):
            cost = usage_data.get("cost", 0.0)
            self.cost_tracking["spent"] += cost
            print(f"[ResourceManager] Tool '{component_name}' cost tracked: {cost}, total spent: {self.cost_tracking['spent']}")
        # LLMトークン利用の追跡
        elif component_name == "llm":
            prompt_tokens = usage_data.get("prompt_tokens", 0)
            completion_tokens = usage_data.get("completion_tokens", 0)
            tokens = prompt_tokens + completion_tokens
            cost = tokens * self.token_cost_per_token
            self.cost_tracking["spent"] += cost
            # OpenAIクォータの更新
            if "openai" in self.api_quotas:
                self.api_quotas["openai"]["used"] += tokens
            print(f"[ResourceManager] LLM usage tracked: tokens {tokens}, cost {cost}, total spent {self.cost_tracking['spent']}")
        else:
            # その他のコンポーネント利用もここで追跡可能
            pass 