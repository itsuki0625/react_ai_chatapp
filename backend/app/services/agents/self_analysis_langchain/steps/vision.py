from ..utils.agent_builder import build_step_agent
from ..tools import note_store, list_notes
from ..prompts import VISION_PROMPT
import logging

logger = logging.getLogger(__name__)

class VisionStepAgent:
    def __init__(self):
        tools = [note_store, list_notes]
        self.agent = build_step_agent(VISION_PROMPT, tools)

    async def __call__(self, params: dict):
        messages = params.get("messages", [])
        session_id = params.get("session_id", "")
        
        # Prepare input for the agent
        agent_input = {
            "messages": str(messages),  # Convert to string for template
            "session_id": session_id,
            "input": messages[-1]["content"] if messages else "自己分析を開始してください"
        }

        try:
            # Execute the agent
            response = await self.agent.ainvoke(agent_input)
            
            # Log the response for debugging
            logger.info(f"VISION agent raw response: {response}")
            
            # AgentExecutor returns a dict with 'output' key
            if isinstance(response, dict) and "output" in response:
                return response["output"]
            
            # Fallback: return the response as-is
            return response
            
        except Exception as e:
            logger.error(f"Error in VISION agent: {e}")
            # Return a fallback response
            return "申し訳ありませんが、ビジョン分析中にエラーが発生しました。もう一度お試しください。" 