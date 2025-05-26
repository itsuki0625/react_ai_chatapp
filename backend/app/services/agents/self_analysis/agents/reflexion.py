from .base_prompt import BaseSelfAnalysisAgent

class PostSessionReflexionAgent(BaseSelfAnalysisAgent):
    """
    セッション全体のマクロリフレクションを行うエージェント
    """
    def __init__(self, **kwargs):
        super().__init__(step_id="ALL", step_goal="マクロリフレクション", **kwargs) 