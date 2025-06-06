from ..utils.agent_builder import build_step_agent
from ..tools import note_store, list_notes, get_summary, render_markdown_timeline
from ..prompts import FUTURE_PROMPT
import logging
import json

logger = logging.getLogger(__name__)

class FutureStepAgent:
    def __init__(self):
        # 初期ツールリストを作成（テストでtoolsがモックに差し替えられることを想定）
        tools = [note_store, list_notes, get_summary, render_markdown_timeline]
        # build_step_agent呼び出しによるtoolsリストのインプレース変更を考慮
        self.agent = build_step_agent(FUTURE_PROMPT, tools)
        # 実際に利用するtoolsリストを保持
        self.tools = tools

    async def __call__(self, params: dict):
        messages = params.get("messages", [])
        session_id = params.get("session_id", "")
        
        logger.info(f"FutureStepAgent called for session {session_id} with {len(messages)} messages")
        
        # Prepare input for the agent
        agent_input = {
            "messages": str(messages),  # Convert to string for template
            "session_id": session_id,
            "input": messages[-1]["content"] if messages else "自己分析を開始してください"
        }
        
        logger.info(f"Agent input prepared: {agent_input}")

        try:
            # Execute the agent
            logger.info("Executing FUTURE agent...")
            response = await self.agent.ainvoke(agent_input)
            
            # Log the response for debugging
            logger.info(f"FUTURE agent raw response: {response}")
            
            # AgentExecutor returns a dict with 'output' key
            if isinstance(response, dict) and "output" in response:
                output = response["output"]
                logger.info(f"Extracted output from response: {output}")
                return output
            
            # Fallback: return the response as-is
            logger.info(f"Returning response as-is: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Error in FUTURE agent: {e}", exc_info=True)
            # Return a structured fallback response that matches expected format
            fallback_response = {
                "cot": "エラーが発生したため、基本的な質問を提供します。",
                "chat": {
                    "future": "将来の目標を明確にする",
                    "values": ["成長", "学習", "挑戦"],
                    "question": "あなたの将来の目標について具体的に教えてください。"
                }
            }
            logger.info(f"Returning fallback response: {fallback_response}")
            return json.dumps(fallback_response, ensure_ascii=False) 