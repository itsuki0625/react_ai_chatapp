from __future__ import annotations
from typing import List, Dict, Any, Optional
import uuid
import json
from pydantic import BaseModel

class ContextManager(BaseModel):
    # セッションごとのコンテキスト履歴: session_id -> list of context entries
    active_contexts: Dict[str, List[Dict[str, Any]]] = {}
    # 全セッション共通のグローバルコンテキスト
    global_context: Dict[str, Any] = {}
    # ユーザープロファイル: user_id -> profile data
    user_profiles: Dict[str, Dict[str, Any]] = {}
    
    def get_relevant_context(self, query: str, session_id: Optional[uuid.UUID] = None, user_id: Optional[str] = None) -> str:
        """
        セッション履歴、ユーザープロファイル、グローバルコンテキストから、
        現在のクエリに関連するコンテキスト文字列を構築して返します。
        """
        parts: List[str] = []
        # セッション履歴を追加
        if session_id:
            sid = str(session_id)
            entries = self.active_contexts.get(sid, [])
            for entry in entries:
                parts.append(f"SessionContext: {json.dumps(entry)}")
        # ユーザープロファイルを追加
        if user_id:
            profile = self.user_profiles.get(user_id)
            if profile:
                parts.append(f"UserProfile: {json.dumps(profile)}")
        # グローバルコンテキストを追加
        for key, value in self.global_context.items():
            parts.append(f"GlobalContext[{key}]: {value}")
        # クエリ情報を最後に付加
        parts.append(f"CurrentQuery: {query}")
        return "\n".join(parts)

    def update_context(self, session_id: uuid.UUID, new_context_data: Dict[str, Any]):
        """
        指定セッションのコンテキストにデータを追加し、グローバル/ユーザープロファイルも更新可能。
        """
        sid = str(session_id)
        # セッション履歴の更新
        if sid not in self.active_contexts:
            self.active_contexts[sid] = []
        self.active_contexts[sid].append(new_context_data)
        # ユーザープロファイルの更新（user_idキーがあれば）
        uid = new_context_data.get("user_id")
        if uid:
            # 新規プロファイル作成 or 既存にマージ
            existing = self.user_profiles.get(uid, {})
            existing.update(new_context_data)
            self.user_profiles[uid] = existing
        # グローバルコンテキストの更新（global_キーがあれば）
        global_updates = new_context_data.get("global_context")
        if isinstance(global_updates, dict):
            self.global_context.update(global_updates) 