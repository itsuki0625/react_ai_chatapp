from typing import Any, Dict
import logging

class TraceLogger:
    """
    エージェントの処理ステップや内部状態、エラーなどをトレースログとして記録するコンポーネントです。
    """
    def __init__(self, logger: logging.Logger = None):
        # ロガーの初期化
        self.logger = logger or logging.getLogger("monono_agent.trace")
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("[TRACE] %(message)s"))
        # 重複したハンドラー追加を防止
        if not self.logger.handlers:
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def trace(self, event: str, data: Dict[str, Any]) -> None:
        """
        トレースイベントを記録します。

        Args:
            event: イベント名 (例: 'run_start', 'stream_chunk')
            data: イベントに関連するデータ
        """
        try:
            self.logger.info(f"{event}: {data}")
        except Exception:
            # ロギング中の例外はエージェント処理を阻害しない
            pass 