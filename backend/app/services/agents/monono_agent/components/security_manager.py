from __future__ import annotations
from typing import List, Dict, Any, Optional
import re, logging, json
from pydantic import BaseModel, Field, ConfigDict

class SecurityManager(BaseModel):
    # Pydantic v2: 任意の型 (logging.Logger) を許可
    model_config = ConfigDict(arbitrary_types_allowed=True)
    # アクセス制御リスト: user_identity -> 許可アクションのリスト
    access_control_list: Dict[Any, List[str]] = Field(default_factory=dict)
    # PII検出用正規表現リスト
    pii_patterns: List[str] = Field(default_factory=list)
    # 監査ログ用ロガー
    audit_logger: logging.Logger = Field(default_factory=lambda: logging.getLogger("security_audit"))

    def sanitize_data(self, data: Any, pii_patterns: Optional[List[str]] = None) -> Any:
        """
        データからPIIを検出してマスキングまたは削除します。
        - data: 文字列、辞書、リストをサポート
        - pii_patternsに正規表現リストを指定可能（未指定時はインスタンス属性を使用）
        """
        patterns = pii_patterns if pii_patterns is not None else self.pii_patterns
        if isinstance(data, str):
            masked = data
            for pat in patterns:
                masked = re.sub(pat, "[REDACTED]", masked)
            return masked
        if isinstance(data, dict):
            return {k: self.sanitize_data(v, patterns) for k, v in data.items()}
        if isinstance(data, list):
            return [self.sanitize_data(item, patterns) for item in data]
        return data

    def check_permissions(self, user_identity: Any, action: str, resource_id: Any) -> bool:
        """
        ユーザーのアクション権限を検証します。
        - access_control_listにエントリがなければ許可
        - 指定ユーザーの許可アクションリストにactionが含まれる場合のみ許可
        """
        allowed = self.access_control_list.get(user_identity)
        if allowed is None:
            return True
        return action in allowed
    
    def log_audit_event(self, event_details: Dict):
        """
        セキュリティ関連イベントを監査ログに記録します。
        """
        try:
            msg = json.dumps(event_details, ensure_ascii=False)
        except Exception:
            msg = str(event_details)
        self.audit_logger.info(msg)
        return None 