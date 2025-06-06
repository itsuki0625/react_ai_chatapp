import pytest
import io
import logging

from app.services.agents.monono_agent.components.trace_logger import TraceLogger

# TraceLogger のデフォルトロガーへのログ記録テスト
def test_trace_logger_records_event_default(caplog):
    """TraceLogger がデフォルトのロガーでイベントを記録することを確認するテスト。"""
    # デフォルト logger 名 "monono_agent.trace" をキャプチャ
    caplog.set_level(logging.INFO, logger="monono_agent.trace")
    tl = TraceLogger()
    tl.trace("run_start", {"session": "12345"})
    # キャプチャされたログにイベント名とデータが含まれていることを確認
    assert any(
        rec.name == "monono_agent.trace" and "run_start" in rec.message and "session" in rec.message
        for rec in caplog.records
    )

# TraceLogger のカスタムロガーへのログ記録テスト
def test_trace_logger_records_event_custom():
    """TraceLogger がカスタムロガーのハンドラーにイベントを記録することを確認するテスト。"""
    # カスタム logger を準備
    stream = io.StringIO()
    custom_logger = logging.getLogger("custom_trace_logger")
    # 既存のハンドラーをクリア（テスト間の影響を防ぐため）
    custom_logger.handlers.clear()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("[TRACE] %(message)s"))
    custom_logger.addHandler(handler)
    custom_logger.setLevel(logging.INFO)

    tl = TraceLogger(logger=custom_logger)
    tl.trace("custom_event", {"foo": "bar"})
    handler.flush()
    log_output = stream.getvalue()
    # ログ出力にイベント名とデータが含まれていることを確認
    assert "custom_event" in log_output
    assert "foo" in log_output
