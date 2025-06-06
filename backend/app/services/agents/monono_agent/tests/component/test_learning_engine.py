import pytest
from typing import Dict, Any
from app.services.agents.monono_agent.components.learning_engine import LearningEngine

class TestLearningEngine:

    def test_track_success_and_failure_logs(self):
        engine = LearningEngine()
        engine.track_success_patterns("Task1", {"method": "A"}, was_successful=True, user_feedback="Good")
        engine.track_success_patterns("Task2", {"method": "B"}, was_successful=False, user_feedback="Bad")
        # 成功ログの検証
        assert len(engine.success_logs) == 1
        assert engine.success_logs[0]["task_description"] == "Task1"
        assert engine.success_logs[0]["approach_details"] == {"method": "A"}
        assert engine.success_logs[0]["user_feedback"] == "Good"
        # 失敗ログの検証
        assert len(engine.failure_logs) == 1
        assert engine.failure_logs[0]["task_description"] == "Task2"
        assert engine.failure_logs[0]["approach_details"] == {"method": "B"}
        assert engine.failure_logs[0]["user_feedback"] == "Bad"

    def test_suggest_improvements_no_failures(self):
        engine = LearningEngine()
        msg = engine.suggest_improvements({"task_description": "NoTask"})
        expected = "過去の失敗データが不足しています。プロンプトを見直すか、別のアプローチを試してください。"
        assert msg == expected

    def test_suggest_improvements_with_failure(self):
        engine = LearningEngine()
        task = "FooTask"
        approach = {"step": 1}
        engine.track_success_patterns(task, approach, was_successful=False)
        msg = engine.suggest_improvements({"task_description": task})
        # タスク名とアプローチが含まれていること
        assert task in msg
        assert str(approach) in msg
        assert "プロンプトの再構成や別のツールの使用をお勧めします。" in msg

    def test_personalize_responses_default_and_with_preferences(self):
        engine = LearningEngine()
        # デフォルト設定では空の辞書を返す
        result1 = engine.personalize_responses("user1", [], None)
        assert result1 == {}
        # 新しい設定を適用
        prefs = {"tone": "formal", "verbosity": "low"}
        result2 = engine.personalize_responses("user1", [], prefs)
        assert result2 == prefs
        # 後続の呼び出しでも設定が保持されていること
        result3 = engine.personalize_responses("user1", [], None)
        assert result3 == prefs 