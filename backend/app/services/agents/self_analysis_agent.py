from agents import Agent,WebSearchTool # OpenAI Agents SDK をインポート

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

# 自己分析エージェントを定義
self_analysis_agent = Agent(
    name="SelfAnalysisAdvisor",
    instructions=system_prompt.strip(),
    tools=[web_search_tool] # ツールが必要な場合はここに追加
) 