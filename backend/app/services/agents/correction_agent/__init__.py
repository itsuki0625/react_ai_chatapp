"""
志望理由書添削エージェント

このモジュールは志望理由書の添削を行うAIエージェントシステムを提供します。

主要コンポーネント:
- CorrectionOrchestrator: メインのオーケストレーター
- 各ステップエージェント: 分析、構成、内容、表現、一貫性、仕上げ
- ツール: 構造分析、差分生成、フィードバック保存
- プロンプト: 各ステップ用の専用プロンプト

使用例:
    from app.services.agents.correction_agent import CorrectionOrchestrator
    
    orchestrator = CorrectionOrchestrator()
    result = await orchestrator.run(
        statement_text="志望理由書の内容",
        messages=[{"content": "添削をお願いします", "role": "user"}],
        session_id="session_123",
        university_info="東京大学医学部",
        self_analysis_context="自己分析の結果"
    )
"""

from .main import CorrectionOrchestrator, CorrectionState
from .steps.analysis import AnalysisStepAgent
from .steps.structure import StructureStepAgent
from .steps.content import ContentStepAgent
from .steps.expression import ExpressionStepAgent
from .steps.coherence import CoherenceStepAgent
from .steps.polish import PolishStepAgent
from .tools import correction_tools
from .utils.agent_builder import (
    build_correction_agent, 
    build_interactive_correction_agent,
    build_diff_analysis_agent
)

__all__ = [
    "CorrectionOrchestrator",
    "CorrectionState",
    "AnalysisStepAgent",
    "StructureStepAgent", 
    "ContentStepAgent",
    "ExpressionStepAgent",
    "CoherenceStepAgent",
    "PolishStepAgent",
    "correction_tools",
    "build_correction_agent",
    "build_interactive_correction_agent",
    "build_diff_analysis_agent"
] 