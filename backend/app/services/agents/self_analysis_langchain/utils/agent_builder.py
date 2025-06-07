from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import PromptTemplate
import logging

logger = logging.getLogger(__name__)

def build_step_agent(step_prompt: str, tools: list):
    """
    指定したプロンプトとツールで単純なエージェントを構築します。
    """

    template_content = f"""{step_prompt}

--- Additional Context for Agent ---
Conversation History (passed as 'messages'):
{{messages}}

Session ID (passed as 'session_id'):
{{session_id}}

Agent Scratchpad (for agent's internal thoughts and tool usage):
{{agent_scratchpad}}
"""

    prompt = PromptTemplate(
        template=template_content, 
        input_variables=["messages", "session_id", "agent_scratchpad"]
    )

    # Add rate limiting and retry configuration
    llm = ChatOpenAI(
        model="gpt-4o", 
        temperature=0,
        max_retries=3,  # Add retry attempts
        request_timeout=60,  # Add timeout
        streaming=False,  # Disable streaming to reduce token usage
        max_tokens=1000,  # Limit output tokens to reduce rate limiting
    )
    
    # Create function agent
    func_agent = create_openai_functions_agent(
        llm=llm, 
        tools=tools, 
        prompt=prompt
    )
    
    # Create agent executor with reasonable limits
    agent_executor = AgentExecutor(
        agent=func_agent,
        tools=tools,
        return_intermediate_steps=False,  # 中間ステップを返さないようにする
        handle_parsing_errors=True,       # パースエラーを処理する
        max_iterations=3,  # Reduce iterations to prevent infinite loops
        early_stopping_method="force",  # Use supported early stopping method
        verbose=False  # Reduce verbose logging
    )
    
    return agent_executor 