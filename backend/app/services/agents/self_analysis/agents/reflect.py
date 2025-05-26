from .base_prompt import BaseSelfAnalysisAgent

class ReflectAgent(BaseSelfAnalysisAgent):
    """
    セッション最終振り返りを行うエージェント
    """
    def __init__(self, **kwargs):
        super().__init__(step_id="REFLECT", step_goal="セッション最終振り返り", **kwargs) 