import os
from app.services.agents.monono_agent.llm_adapters.openai_adapter import OpenAIAdapter

# モデル名と環境変数から取得した API キーを使ったアダプタ
openai_adapter = OpenAIAdapter(model_name="gpt-4.1", api_key=os.getenv("OPENAI_API_KEY")) 