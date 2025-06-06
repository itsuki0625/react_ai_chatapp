from .base_prompt import BaseSelfAnalysisAgent, load_md
from ..tools.vision import ngram_similarity, tone_score
from ..guardrails import vision_guardrail
from app.services.agents.monono_agent.components.learning_engine import LearningEngine

class VisionAgent(BaseSelfAnalysisAgent):
    """
    志望理由書の核となる1行ビジョンを確定するエージェント。
    """
    STEP_ID = "VISION"
    STEP_GOAL = "自己分析全体（将来像、動機、歴史、ギャップ）を踏まえ、大学で何を学び、社会で何を成し遂げたいのか、最も伝えたい核心的なメッセージを1行のビジョンとして言語化する。"
    NEXT_STEP = "REFLECT"

    def __init__(self, **kwargs):
        super().__init__(
            step_id=self.STEP_ID,
            step_goal="1 行ビジョン確定",
            instructions="""あなたはキャリアビジョン策定 AI です。
Future / Gap / Action / Impact / Univ すべてを踏まえ、30 字以内 1 文のビジョンを考案してください。

### 出力 JSON
{
  "cot":"<思考過程>",
  "chat": {
    "vision":"医療格差を AI でゼロにする",
    "tone_scores":{"excitement":6,"social":7,"feasible":5},
    "uniq_score":0.42,
    "alt_taglines":[
      "誰もが医療に届く社会を創る",
      "医療アクセスの壁を壊すAIリーダー"
    ],
    "question":"このビジョンはあなたの言葉としてしっくり来ますか？"
  }
}

### 評価基準
- vision 30 字以内、語尾は「する/なる」
- tone_scores 各 1–7
- uniq_score 0–1（低いほど独自）
- question 敬語 1 文
""",
            tools=[ngram_similarity, tone_score],
            learning_engine=LearningEngine(),
            guardrail=vision_guardrail,
            **kwargs
        )

    # interactive_plan は BaseSelfAnalysisAgent.run_with_plan が担うため削除
    # async def interactive_plan(self, messages, session_id=None):
    #     ...

    # run メソッドは BaseSelfAnalysisAgent.run_with_plan が担う (実質 interactive_plan を呼び出していた)
    # async def run(self, messages, session_id=None):
    #     return await self.interactive_plan(messages, session_id) 