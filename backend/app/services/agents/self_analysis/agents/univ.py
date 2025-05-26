from .base_prompt import BaseSelfAnalysisAgent

class UniversityMapperAgent(BaseSelfAnalysisAgent):
    """
    授業・ゼミ探索を行うエージェント
    """
    def __init__(self, **kwargs):
        super().__init__(step_id="UNIV", step_goal="授業・ゼミ探索", **kwargs) 