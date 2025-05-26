from .base_prompt import BaseSelfAnalysisAgent

class ImpactAgent(BaseSelfAnalysisAgent):
    """
    インパクト深掘りを行うエージェント
    """
    def __init__(self, **kwargs):
        super().__init__(step_id="IMPACT", step_goal="インパクト深掘り", **kwargs) 