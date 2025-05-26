from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import json

class LearningEngine(BaseModel):
    # 過去の成功/失敗ログを保持
    success_logs: List[Dict[str, Any]] = Field(default_factory=list)
    failure_logs: List[Dict[str, Any]] = Field(default_factory=list)
    # ユーザーごとの応答パーソナライズ設定
    user_preferences: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    def track_success_patterns(self, task_description: str, approach_details: Dict[str, Any], was_successful: bool, user_feedback: Optional[str] = None):
        """
        タスク実行の成否とアプローチの詳細を記録します。
        """
        log_entry = {
            "task_description": task_description,
            "approach_details": approach_details,
            "was_successful": was_successful,
            "user_feedback": user_feedback,
        }
        if was_successful:
            self.success_logs.append(log_entry)
        else:
            self.failure_logs.append(log_entry)

    def suggest_improvements(self, failed_task_context: Dict[str, Any]) -> str:
        """
        過去の失敗ログを参考に、改善策を提案します。
        """
        task_desc = failed_task_context.get("task_description")
        similar_failures = [f for f in self.failure_logs if f.get("task_description") == task_desc]
        if similar_failures:
            last = similar_failures[-1]
            return (
                f"タスク「{task_desc}」の失敗を踏まえ、アプローチ {last['approach_details']} の代替手法を検討してください。"
                "プロンプトの再構成や別のツールの使用をお勧めします。"
            )
        return "過去の失敗データが不足しています。プロンプトを見直すか、別のアプローチを試してください。"

    def personalize_responses(self, user_id: str, interaction_history: List[Dict[str, Any]], preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        ユーザーのフィードバックや設定に基づき、応答スタイルを調整するための情報を返します。
        """
        # 新しい設定があれば保存
        if preferences:
            self.user_preferences[user_id] = preferences
        prefs = self.user_preferences.get(user_id, {})
        result: Dict[str, Any] = {}
        # トーンや冗長性の設定を反映
        if "tone" in prefs:
            result["tone"] = prefs["tone"]
        if "verbosity" in prefs:
            result["verbosity"] = prefs["verbosity"]
        return result 