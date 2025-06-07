from __future__ import annotations
from typing import List, Dict, Any, Optional
import uuid
from pydantic import BaseModel, Field
from collections import Counter

class CollaborationManager(BaseModel):
    # セッション共有の状態を保持: session_id -> user_ids
    shared_sessions: Dict[str, List[str]] = Field(default_factory=dict)
    # 人間へのタスク委譲情報を保持: delegation_id -> details
    delegated_tasks: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    async def share_session_with_users(self, session_id: uuid.UUID, user_ids_to_share_with: List[str]) -> bool:
        """指定されたユーザーIDリストとセッションを共有する"""
        sid = str(session_id)
        self.shared_sessions[sid] = user_ids_to_share_with
        print(f"[CollaborationManager] Shared session {sid} with users {user_ids_to_share_with}")
        return True
    
    async def delegate_task_to_human(self, task_details: Dict[str, Any], reason_for_delegation: str, human_expert_role: Optional[str] = None) -> Dict[str, Any]:
        """人間の専門家にタスクを委譲し、応答を返却する (プレースホルダー実装)"""
        delegation_id = str(uuid.uuid4())
        self.delegated_tasks[delegation_id] = {
            "task_details": task_details,
            "reason": reason_for_delegation,
            "role": human_expert_role
        }
        print(f"[CollaborationManager] Delegated task {delegation_id} to human role {human_expert_role}: {task_details}")
        # プレースホルダーとしての人間からの応答
        human_response = {
            "delegation_id": delegation_id,
            "response": "This is a placeholder response from human expert"
        }
        return human_response
    
    async def merge_agent_outputs(self, list_of_agent_results: List[Any], merge_strategy: str = "majority_vote") -> Any:
        """複数エージェントの結果を指定の戦略で統合する"""
        if not list_of_agent_results:
            return None
        if merge_strategy == "majority_vote":
            counts = Counter(list_of_agent_results)
            result, _ = counts.most_common(1)[0]
            return result
        elif merge_strategy == "summation":
            try:
                return sum(list_of_agent_results)
            except TypeError:
                return list_of_agent_results
        elif merge_strategy == "average":
            try:
                return sum(list_of_agent_results) / len(list_of_agent_results)
            except TypeError:
                return list_of_agent_results
        elif merge_strategy == "llm_based_synthesis":
            # プレースホルダーとして結果を連結
            return " ".join(map(str, list_of_agent_results))
        else:
            print(f"[CollaborationManager] Unknown merge strategy '{merge_strategy}', returning first result.")
            return list_of_agent_results[0] 