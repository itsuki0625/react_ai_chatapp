from .base_prompt import BaseSelfAnalysisAgent

class VisionAgent(BaseSelfAnalysisAgent):
    """
    1行ビジョン確定を行うエージェント
    """
    def __init__(self, **kwargs):
        super().__init__(step_id="VISION", step_goal="1行ビジョン確定", **kwargs) 