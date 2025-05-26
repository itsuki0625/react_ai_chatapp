import os
from agents import WebSearchTool  # 既存の WebSearchTool を再利用
from app.services.agents.monono_agent.base_agent import BaseAgent
from app.services.agents.monono_agent.llm_adapters.openai_adapter import OpenAIAdapter

# 自己分析用のシステムプロンプト
system_prompt = """
あなたは優秀なキャリアアドバイザーAIです。ユーザーが自己理解を深められるよう、対話を通じてサポートしてください。
以下の点に注意して応答を生成してください。
- ユーザーの発言を肯定的に受け止め、共感を示してください。
- 深掘りするための具体的な質問を投げかけてください。
- ユーザーの興味、価値観、強み、弱みなどを引き出すように努めてください。
- 一方的なアドバイスではなく、ユーザー自身が考え、気づきを得られるような対話を心がけてください。
- 簡潔で分かりやすい言葉遣いをしてください。
"""

web_search_tool = WebSearchTool()

# WebSearchTool を呼び出すラッパー関数
def web_search(query: str) -> str:
    """WebSearchTool を使って検索結果を返す"""
    return web_search_tool.run(query)

# OpenAIAdapter を作成 (環境変数から API キー取得)
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_adapter = OpenAIAdapter(model_name="gpt-4o", api_key=openai_api_key)

# 自己分析エージェントを定義 (monono_agent ベース)
self_analysis_agent = BaseAgent(
    name="SelfAnalysisAdvisor",
    instructions=system_prompt.strip(),
    llm_adapter=openai_adapter,
    tools=[web_search]
) 