# from typing import List, Dict, Optional, Any
# from agents import Runner # OpenAI Agents SDK をインポート
# # from app.core.config import settings # APIキーは環境変数から直接読み込む想定
# from app.services.agents import self_analysis_agent, admission_agent, study_support_agent # エージェント定義をインポート
# import logging


# logger = logging.getLogger(__name__)

# async def get_admission_agent_response(user_input: str, history: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
#     """
#     総合型選抜AI用のAgentを利用し、応答を生成します。
#     """
#     try:
#         print(f"Running {admission_agent.name} with input: {user_input[:50]}...")
#         result = await Runner.run(admission_agent, user_input)
#         # print(f"Agent {admission_agent.name} run finished. Status: {result.status}") # Comment out problematic line
#         if result.final_output: return str(result.final_output).strip()
#         else:
#             # print(f"Agent {admission_agent.name} did not produce output. Status: {result.status}, Error: {result.error}") # Comment out problematic line
#             print(f"Agent {admission_agent.name} did not produce output. Error: {getattr(result, 'error', 'Unknown error')}")
#             return "申し訳ありません、AIからの応答を取得できませんでした。"
#     except ImportError as e:
#          print(f"Error importing openai-agents: {e}. Make sure it is installed.")
#          return "AI Agent SDKの読み込みに失敗しました。インストールを確認してください。"
#     except Exception as e:
#         logger.error(f"An unexpected error occurred while running agent {getattr(admission_agent, 'name', 'Admission')}: {e}", exc_info=True)
#         return "申し訳ありません、総合型選抜AIの実行中にエラーが発生しました。"

# async def get_study_support_agent_response(user_input: str, history: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
#     """
#     汎用学習支援AI用のAgentを利用し、応答を生成します。
#     """
#     try:
#         print(f"Running {study_support_agent.name} with input: {user_input[:50]}...")
#         result = await Runner.run(study_support_agent, user_input)
#         # print(f"Agent {study_support_agent.name} run finished. Status: {result.status}") # Comment out problematic line
#         if result.final_output: return str(result.final_output).strip()
#         else:
#             # print(f"Agent {study_support_agent.name} did not produce output. Status: {result.status}, Error: {result.error}") # Comment out problematic line
#             print(f"Agent {study_support_agent.name} did not produce output. Error: {getattr(result, 'error', 'Unknown error')}")
#             return "申し訳ありません、AIからの応答を取得できませんでした。"
#     except ImportError as e:
#          print(f"Error importing openai-agents: {e}. Make sure it is installed.")
#          return "AI Agent SDKの読み込みに失敗しました。インストールを確認してください。"
#     except Exception as e:
#         logger.error(f"An unexpected error occurred while running agent {getattr(study_support_agent, 'name', 'StudySupport')}: {e}", exc_info=True)
#         return "申し訳ありません、学習支援AIの実行中にエラーが発生しました。"

# # --- 以前のコードは削除済 --- 

# # ai_service = AIService()

# # async def get_self_analysis_response(user_input: str, history: List[Dict[str, str]]) -> Optional[str]:
# #     ... 

from uuid import uuid4
from app.services.agents.self_analysis.orchestrator import SelfAnalysisOrchestrator
import logging
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

async def get_self_analysis_agent_response(user_input: str, history: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
    """
    monono_agent の SelfAnalysisAdvisor を利用して応答を生成します。
    history は現状サポートせず、毎回新規会話として扱います。
    """
    try:
        # 新しいセッションIDを生成し、オーケストレーターで自己分析を実行
        session_id = str(uuid4())
        orchestrator = SelfAnalysisOrchestrator()
        # user_visible にはクライアントに返す内容が含まれます
        user_visible = await orchestrator.run(session_id, user_input)
        return user_visible
    except Exception as e:
        logger.error(f"Unexpected error in get_self_analysis_agent_response: {e}", exc_info=True)
        return "申し訳ありません、自己分析AIの実行中にエラーが発生しました。"

async def get_admission_agent_response(user_input: str, history: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
    """
    総合型選抜AI用のAgentは未実装のため、簡易メッセージを返却します。
    """
    try:
        return "申し訳ありません、現在総合型選抜AIは準備中です。"
    except Exception as e:
        logger.error(f"Unexpected error in get_admission_agent_response: {e}", exc_info=True)
        return "申し訳ありません、総合型選抜AIの実行中にエラーが発生しました。"

async def get_study_support_agent_response(user_input: str, history: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
    """
    学習支援AI用のAgentは未実装のため、簡易メッセージを返却します。
    """
    try:
        return "申し訳ありません、現在学習支援AIは準備中です。"
    except Exception as e:
        logger.error(f"Unexpected error in get_study_support_agent_response: {e}", exc_info=True)
        return "申し訳ありません、学習支援AIの実行中にエラーが発生しました。"

async def get_review_agent_response(user_input: str, history: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
    """
    レビューAI用のAgentを利用して応答を生成します。
    """
    try:
        return "申し訳ありません、現在レビューAIは準備中です。"
    except Exception as e:
        logger.error(f"Unexpected error in get_review_agent_response: {e}", exc_info=True)
        return "申し訳ありません、レビューAIの実行中にエラーが発生しました。" 