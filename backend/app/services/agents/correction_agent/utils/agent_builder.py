from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import PromptTemplate
import logging

logger = logging.getLogger(__name__)

def build_correction_agent(step_prompt: str, tools: list):
    """
    志望理由書添削用のエージェントを構築します。
    """

    template_content = f"""{step_prompt}

--- 志望理由書添削エージェント用コンテキスト ---
志望理由書本文 (passed as 'statement_text'):
{{statement_text}}

メッセージ履歴 (passed as 'messages'):
{{messages}}

セッションID (passed as 'session_id'):
{{session_id}}

志望大学情報 (passed as 'university_info'):
{{university_info}}

自己分析コンテキスト (passed as 'self_analysis_context'):
{{self_analysis_context}}

エージェント作業領域 (for agent's internal thoughts and tool usage):
{{agent_scratchpad}}
"""

    prompt = PromptTemplate(
        template=template_content, 
        input_variables=[
            "statement_text", 
            "messages", 
            "session_id", 
            "university_info", 
            "self_analysis_context", 
            "agent_scratchpad"
        ]
    )

    # 志望理由書添削に最適化されたLLM設定
    llm = ChatOpenAI(
        model="gpt-4o", 
        temperature=0.3,  # 創造性と一貫性のバランス
        max_retries=3,
        request_timeout=120,  # 長文分析のためタイムアウトを延長
        streaming=False,
        max_tokens=2000,  # 詳細な分析のため増加
    )
    
    # Function agent作成
    func_agent = create_openai_functions_agent(
        llm=llm, 
        tools=tools, 
        prompt=prompt
    )
    
    # 志望理由書添削用に最適化されたAgent Executor
    agent_executor = AgentExecutor(
        agent=func_agent,
        tools=tools,
        return_intermediate_steps=False,
        handle_parsing_errors=True,
        max_iterations=5,  # 複雑な分析のため反復回数を増加
        early_stopping_method="force",
        verbose=False
    )
    
    return agent_executor

def build_interactive_correction_agent(step_prompt: str, tools: list):
    """
    インタラクティブな添削用エージェントを構築します。
    ユーザーとの対話を重視した設定。
    """

    template_content = f"""{step_prompt}

--- インタラクティブ添削モード ---
現在の志望理由書:
{{statement_text}}

ユーザーからのリクエスト:
{{user_request}}

会話履歴:
{{messages}}

追加情報:
- セッションID: {{session_id}}
- 志望大学: {{university_info}}
- 自己分析結果: {{self_analysis_context}}

エージェント作業領域:
{{agent_scratchpad}}

重要: ユーザーの主体性を尊重し、提案は選択可能な形で提示してください。
"""

    prompt = PromptTemplate(
        template=template_content, 
        input_variables=[
            "statement_text", 
            "user_request",
            "messages", 
            "session_id", 
            "university_info", 
            "self_analysis_context", 
            "agent_scratchpad"
        ]
    )

    # インタラクティブ用LLM設定
    llm = ChatOpenAI(
        model="gpt-4o", 
        temperature=0.7,  # 対話において自然さを重視
        max_retries=2,
        request_timeout=90,
        streaming=True,  # リアルタイム対話のためストリーミング有効
        max_tokens=1500,
    )
    
    func_agent = create_openai_functions_agent(
        llm=llm, 
        tools=tools, 
        prompt=prompt
    )
    
    agent_executor = AgentExecutor(
        agent=func_agent,
        tools=tools,
        return_intermediate_steps=True,  # 対話では中間ステップも重要
        handle_parsing_errors=True,
        max_iterations=3,  # 対話では素早いレスポンスを重視
        early_stopping_method="force",
        verbose=True  # デバッグのため詳細ログ有効
    )
    
    return agent_executor

def build_diff_analysis_agent(tools: list):
    """
    文章の差分分析に特化したエージェントを構築します。
    """
    
    diff_prompt = """あなたは志望理由書の差分分析専門家です。
元の文章と修正提案を比較し、変更点とその効果を詳細に分析してください。

元の文章:
{original_text}

修正提案:
{suggested_text}

分析観点:
1. 文章構造の変化
2. 表現力の向上
3. 論理的な流れの改善
4. 読み手への影響

分析結果をJSON形式で出力し、ユーザーが理解しやすい形で説明してください。

エージェント作業領域:
{agent_scratchpad}
"""

    prompt = PromptTemplate(
        template=diff_prompt,
        input_variables=["original_text", "suggested_text", "agent_scratchpad"]
    )

    llm = ChatOpenAI(
        model="gpt-4o", 
        temperature=0.1,  # 分析の一貫性を重視
        max_retries=3,
        request_timeout=60,
        streaming=False,
        max_tokens=1000,
    )
    
    func_agent = create_openai_functions_agent(
        llm=llm, 
        tools=tools, 
        prompt=prompt
    )
    
    agent_executor = AgentExecutor(
        agent=func_agent,
        tools=tools,
        return_intermediate_steps=False,
        handle_parsing_errors=True,
        max_iterations=2,  # 分析は迅速に
        early_stopping_method="force",
        verbose=False
    )
    
    return agent_executor 